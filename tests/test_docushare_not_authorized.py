import os
import pathlib
import shutil
import tempfile
from unittest import TestCase, skipIf

from docushare import *


class DocuShareNotAuthorizedTest(TestCase):
    required_envs = [
        'DOCUSHARE_BASEURL',
        'DOCUSHARE_USERNAME',
        'DOCUSHARE_NOT_AUTHORIZED_DOCUMENT_HANDLE',
        'DOCUSHARE_NOT_AUTHORIZED_VERSION_HANDLE',
    ]
    skip = not all([env in os.environ for env in required_envs])
    skip_reason = 'Following environmental variables are not defined: ' + ', '.join([env for env in required_envs if env not in os.environ])

    def setUp(self):
        self.base_url = os.environ['DOCUSHARE_BASEURL']
        self.username = os.environ['DOCUSHARE_USERNAME']
        self.not_authorized_document_handle = os.environ['DOCUSHARE_NOT_AUTHORIZED_DOCUMENT_HANDLE']
        self.not_authorized_version_handle  = os.environ['DOCUSHARE_NOT_AUTHORIZED_VERSION_HANDLE']

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
    def test_not_authorized_errors(self):
        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds.object(self.not_authorized_document_handle)

        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds[self.not_authorized_document_handle]
            
        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds.download(self.not_authorized_document_handle, self.tempdir.joinpath('test.bin'))
            
        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds.http_get(self.base_url + 'dsweb/Services/' + self.not_authorized_document_handle)
            
        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds.object(self.not_authorized_version_handle)

        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds[self.not_authorized_version_handle]
            
        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds.download(self.not_authorized_version_handle, self.tempdir.joinpath('test.bin'))

        with self.assertRaises(DocuShareNotAuthorizedError) as context:
            self.ds.http_get(self.base_url + 'dsweb/Services/' + self.not_authorized_version_handle)
