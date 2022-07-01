import os
import pathlib
import shutil
import tempfile
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
        self.tempdir = pathlib.Path(tempfile.mkdtemp())
        
    def tearDown(self):
        self.ds.close()
        shutil.rmtree(self.tempdir)
        
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
        self.assertIsInstance(doc_obj.document_control_number, (str, type(None)))
        self.assertEqual(doc_obj.download_url, self.base_url + 'dsweb/Get/' + self.valid_document_handle)

        doc_obj_path1 = doc_obj.download(self.tempdir)
        self.assertTrue(pathlib.Path(doc_obj_path1).is_file())

        doc_obj_path2 = doc_obj.download(self.tempdir.joinpath('document.bin'))
        self.assertTrue(pathlib.Path(doc_obj_path2).is_file())

        doc_obj_path3 = self.tempdir.joinpath('document.bin2')
        self.ds.download(self.valid_document_handle, doc_obj_path3)
        self.assertTrue(pathlib.Path(doc_obj_path3).is_file())
       
        doc_version_handles = doc_obj.version_handles
        self.assertIsInstance(doc_version_handles, list)
        self.assertTrue(len(doc_version_handles) > 0)
        self.assertTrue(all([version_handle.type == HandleType.Version for version_handle in doc_version_handles]))

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

        ver_obj_path1 = ver_obj.download(self.tempdir)
        self.assertTrue(pathlib.Path(ver_obj_path1).is_file())

        ver_obj_path2 = ver_obj.download(self.tempdir.joinpath('version.bin'))
        self.assertTrue(pathlib.Path(ver_obj_path2).is_file())

        ver_obj_path3 = self.tempdir.joinpath('version.bin2')
        self.ds.download(self.valid_version_handle, ver_obj_path3)
        self.assertTrue(pathlib.Path(ver_obj_path3).is_file())

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
        self.assertIsInstance(doc_obj.document_control_number, (str, type(None)))
        self.assertEqual(doc_obj.download_url, self.base_url + 'dsweb/Get/' + self.valid_document_handle)

        doc_version_handles = doc_obj.version_handles
        self.assertIsInstance(doc_version_handles, list)
        self.assertTrue(len(doc_version_handles) > 0)
        self.assertTrue(all([version_handle.type == HandleType.Version for version_handle in doc_version_handles]))

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
