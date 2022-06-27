import os
import pathlib
import shutil
import tempfile
from unittest import TestCase, skipIf

from docushare import *


class DocuShareErrorTest(TestCase):
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
            
        self.ds = DocuShare(self.base_url)
        self.ds.login(username = self.username, password = self.password)
        self.tempdir = pathlib.Path(tempfile.mkdtemp())
            
    def tearDown(self):
        self.ds.close()
        shutil.rmtree(self.tempdir)
            
    @skipIf(skip, skip_reason)
    def test_http_get_errors(self):
        import requests
        
        with self.assertRaises(requests.HTTPError) as context:
            self.ds.http_get(self.base_url + 'dsweb/xxx')

        with self.assertRaises(DocuShareSystemError) as context:
            self.ds.http_get(self.base_url + 'dsweb/Services/Document-00000')

    @skipIf(skip, skip_reason)
    def test_docushare_system_errors(self):
        with self.assertRaises(DocuShareSystemError) as context:
            self.ds.object('Document-00000')
            
        with self.assertRaises(DocuShareSystemError) as context:
            self.ds['Document-00000']
            
        with self.assertRaises(DocuShareSystemError) as context:
            self.ds.object('Version-000000')

        with self.assertRaises(DocuShareSystemError) as context:
            self.ds['Version-000000']
            
        with self.assertRaises(DocuShareSystemError) as context:
            self.ds['Version-000000']

    @skipIf(skip, skip_reason)
    def test_docushare_not_found_error(self):
        with self.assertRaises(DocuShareNotFoundError) as context:
            self.ds.download('Document-00000', self.tempdir.joinpath('test.bin'))
