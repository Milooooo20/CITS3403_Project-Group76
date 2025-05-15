import unittest
from flask import url_for
from app import create_app, db
from app.models import User
from flask_testing import TestCase
from unittest.mock import patch

class RoutesTestCase(TestCase):
    def create_app(self):
        # Create app with testing config
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('password')
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self):
        with self.client:
            return self.client.post('/sign_in', data={
                'username': 'testuser',
                'password': 'password'
            }, follow_redirects=True)

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Home', response.data)

    def test_create_account_mismatched_passwords(self):
        response = self.client.post('/create_account', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'abc',
            'confirm-password': 'xyz'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', response.data)

    @patch('app.routes.spotify_api.search_tracks')
    def test_search_songs_route(self, mock_search_tracks):
        # Log in first
        self.login()

        mock_search_tracks.return_value = {
            'tracks': {
                'items': [
                    {
                        'id': '123',
                        'name': 'Test Song',
                        'artists': [{'name': 'Test Artist'}],
                        'album': {'name': 'Test Album', 'images': [{'url': 'http://example.com/image.jpg', 'width': 64}]},
                        'preview_url': 'http://example.com/preview.mp3'
                    }
                ]
            }
        }

        response = self.client.get('/search_songs?query=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Song', response.data)

