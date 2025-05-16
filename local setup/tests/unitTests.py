import unittest
from controllers import logging_in, signing_up
from app import create_app, db
from app.models import User
from app.config import TestConfig



class UnitTests(unittest.TestCase):
    def setUp(self):
        testApp = create_app(TestConfig)
        self.app_context = testApp.app_context()
        self.app_context.push()
        db.create_all()
        return super().setUp()
    
    def test_password_hashing(self):
        user1 = User(id=1, username='user1', email='user1@example.com')
        user1.set_password('testpassword')
        self.assertTrue(user1.check_password('testpassword'))
        self.assertFalse(user1.check_password('wrongpassword'))

    def add_User(self, id=2, email='user2@eg.com', username='user2', password='password', database=True):
        user = User(id=id, email=email, username=username)
        user.set_password(password)
        if database:
            db.session.add(user)
            db.session.commit()
        return user
    
    def test_login_user(self):
        user2 = self.add_User()
        self.assertEqual(logging_in(user2.id, user2.username, 'password'), "redirect(url_for('main.profile'))", 'User should be logged in successfully')
        self.assertEqual(logging_in(user2.id, user2.username, 'wrongpassword'), "redirect(url_for('main.sign_in'))", 'User should not be logged in with the wrong password')

    def test_signup_user(self):
        self.assertEqual(signing_up('user3', 'user3@example.com', 'pw', 'pw'), "redirect(url_for('main.sign_in'))", 'User should have successfully signed up')
        self.assertEqual(signing_up('invalid_user', 'user3@example.com', 'pwd', 'pwd'), "same_credential: redirect(url_for('main.create_account'))", "User cannot sign up with the same username or email")
        self.assertEqual(signing_up('iclumsy_user', 'user3@example.com', 'pwd', 'pwd4'), "confirm_pw: redirect(url_for('main.create_account'))", "User must make sure to correctly confirm their password")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        return super().tearDown()