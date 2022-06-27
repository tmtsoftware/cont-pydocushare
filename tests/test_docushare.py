import os
from unittest import TestCase, skipIf
from docushare import *

class DocuShareTest(TestCase):
    required_envs = [
        'DOCUSHARE_BASEURL',
        'DOCUSHARE_USERNAME',
        'DOCUSHARE_VALID_DOCUMENT_HANDLE',
        'DOCUSHARE_VALID_VERSION_HANDLE',
    ]
    skip = not all([env in os.environ for env in required_envs])
    skip_reason = 'Following environmental variables are not defined: ' + ', '.join([env for env in required_envs if env not in os.environ])
    
    def setUp(self):
        self.base_url = os.environ['DOCUSHARE_BASEURL']
        self.username = os.environ['DOCUSHARE_USERNAME']
        self.valid_document_handle = os.environ['DOCUSHARE_VALID_DOCUMENT_HANDLE']
        self.valid_version_handle = os.environ['DOCUSHARE_VALID_VERSION_HANDLE']

        if 'DOCUSHARE_PASSWORD' in os.environ:
            self.password = os.environ['DOCUSHARE_PASSWORD']
        else:
            self.password = PasswordOption.USE_STORED

        self.ds = DocuShare(self.base_url)
        self.ds.login(username = self.username, password = self.password)

    def tearDown(self):
        self.ds.close()

    @skipIf(skip, skip_reason)
    def test_normal_workflow_1(self):
        doc_obj = self.ds.object(self.valid_document_handle)
        self.assertIsInstance(doc_obj, DocumentObject)
        self.assertIsInstance(doc_obj, DocuShareBaseObject)
        self.assertEqual(doc_obj.docushare, self.ds)
        self.assertEqual(doc_obj.handle.type, HandleType.Document)
        self.assertIsInstance(doc_obj.handle.number, int)
        self.assertTrue(doc_obj.handle.number >= 0)
        self.assertEqual(doc_obj.handle.identifier, self.valid_document_handle)
        self.assertIsInstance(doc_obj.title, str)
        self.assertIsInstance(doc_obj.filename, str)
        self.assertIsInstance(doc_obj.document_control_number, str)
        self.assertEqual(doc_obj.download_url, self.base_url + 'dsweb/Get/' + self.valid_document_handle)

        doc_versions = doc_obj.versions
        self.assertIsInstance(doc_versions, list)
        self.assertTrue(len(doc_versions) > 0)
        self.assertTrue(all([version_handle.type == HandleType.Version for version_handle in doc_versions]))

        ver_obj = self.ds.object(self.valid_version_handle)
        self.assertIsInstance(ver_obj, VersionObject)
        self.assertIsInstance(ver_obj, DocuShareBaseObject)
        self.assertEqual(ver_obj.docushare, self.ds)
        self.assertEqual(ver_obj.handle.type, HandleType.Version)
        self.assertIsInstance(ver_obj.handle.number, int)
        self.assertTrue(ver_obj.handle.number >= 0)
        self.assertEqual(ver_obj.handle.identifier, self.valid_version_handle)
        self.assertIsInstance(ver_obj.title, str)
        self.assertIsInstance(ver_obj.filename, str)
        self.assertIsInstance(ver_obj.version_number, int)
        self.assertEqual(ver_obj.download_url, self.base_url + 'dsweb/Get/' + self.valid_version_handle)

    @skipIf(skip, skip_reason)
    def test_normal_workflow_2(self):
        doc_obj = self.ds[self.valid_document_handle]
        self.assertIsInstance(doc_obj, DocumentObject)
        self.assertIsInstance(doc_obj, DocuShareBaseObject)
        self.assertEqual(doc_obj.docushare, self.ds)
        self.assertEqual(doc_obj.handle.type, HandleType.Document)
        self.assertIsInstance(doc_obj.handle.number, int)
        self.assertTrue(doc_obj.handle.number >= 0)
        self.assertEqual(doc_obj.handle.identifier, self.valid_document_handle)
        self.assertIsInstance(doc_obj.title, str)
        self.assertIsInstance(doc_obj.filename, str)
        self.assertIsInstance(doc_obj.document_control_number, str)
        self.assertEqual(doc_obj.download_url, self.base_url + 'dsweb/Get/' + self.valid_document_handle)

        doc_versions = doc_obj.versions
        self.assertIsInstance(doc_versions, list)
        self.assertTrue(len(doc_versions) > 0)
        self.assertTrue(all([version_handle.type == HandleType.Version for version_handle in doc_versions]))

        ver_obj = self.ds[self.valid_version_handle]
        self.assertIsInstance(ver_obj, VersionObject)
        self.assertIsInstance(ver_obj, DocuShareBaseObject)
        self.assertEqual(ver_obj.docushare, self.ds)
        self.assertEqual(ver_obj.handle.type, HandleType.Version)
        self.assertIsInstance(ver_obj.handle.number, int)
        self.assertTrue(ver_obj.handle.number >= 0)
        self.assertEqual(ver_obj.handle.identifier, self.valid_version_handle)
        self.assertIsInstance(ver_obj.title, str)
        self.assertIsInstance(ver_obj.filename, str)
        self.assertIsInstance(ver_obj.version_number, int)
        self.assertEqual(ver_obj.download_url, self.base_url + 'dsweb/Get/' + self.valid_version_handle)
            
    # TODO: test DocuShareNotAuthorizedError
