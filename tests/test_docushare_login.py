import os
from unittest import TestCase, skipIf
from docushare import *

class DocuShareLoginTest(TestCase):
    required_envs = [
        'DOCUSHARE_BASEURL',
        'DOCUSHARE_USERNAME',
    ]
    skip = not all([env in os.environ for env in required_envs])
    skip_reason = 'Following environmental variables are not defined: ' + ', '.join([env for env in required_envs if env not in os.environ])

    def setUp(self):
        self.base_url = os.environ['DOCUSHARE_BASEURL']
        self.username = os.environ['DOCUSHARE_USERNAME']

        if 'DOCUSHARE_PASSWORD' in os.environ:
            self.password = os.environ['DOCUSHARE_PASSWORD']
        else:
            self.password = PasswordOption.USE_STORED
            
    @skipIf(skip, skip_reason)
    def test_login(self):
        ds = DocuShare(self.base_url)
        
        self.assertFalse(ds.is_logged_in)
        self.assertIsNone(ds.username)
        
        ds.login(username = self.username, password = self.password)

        self.assertTrue(ds.is_logged_in)
        self.assertEqual(ds.username, self.username)
        self.assertTrue('JSESSIONID' in ds.cookies)
        self.assertTrue('AmberUser' in ds.cookies)
        
        ds.close()

        self.assertFalse(ds.is_logged_in)
        self.assertIsNone(ds.username)

