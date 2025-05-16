import unittest
from app import create_app, db
from app.config import TestConfig



class UnitTests(unittest.TestCase):
    def setUp(self):
        testApp = create_app(TestConfig)
        self.app_context = testApp.app_context()
        self.app_context.push()
        db.create_all()
        
#        return super().setUp()
    


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
#        return super().tearDown()