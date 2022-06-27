from unittest import TestCase

from docushare import *


class HandleTest(TestCase):
    def test_init_wrong_type_1(self):
        with self.assertRaises(TypeError) as context:
            Handle('Collection', 12345)
        with self.assertRaises(TypeError) as context:
            Handle(12345, 12345)
        with self.assertRaises(TypeError) as context:
            Handle(None, 12345)
        
    def test_init_wrong_type_2(self):
        with self.assertRaises(TypeError) as context:
            Handle(HandleType.Collection, '12345')
        with self.assertRaises(TypeError) as context:
            Handle(HandleType.Collection, object())
        with self.assertRaises(TypeError) as context:
            Handle(HandleType.Collection, None)
            
    def test_init_negative_number(self):
        with self.assertRaises(ValueError) as context:
            Handle(HandleType.Collection, -1)
        with self.assertRaises(ValueError) as context:
            Handle(HandleType.Document, -1)
        with self.assertRaises(ValueError) as context:
            Handle(HandleType.Version, -1)
            
    def test_init_collection_0(self):
        hdl = Handle(HandleType.Collection, 0)
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 0)
        self.assertEqual(hdl.identifier, 'Collection-00000')
        
    def test_init_collection_1(self):
        hdl = Handle(HandleType.Collection, 12345)
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 12345)
        self.assertEqual(hdl.identifier, 'Collection-12345')

    def test_init_collection_2(self):
        hdl = Handle(HandleType.Collection, 1234)
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 1234)
        self.assertEqual(hdl.identifier, 'Collection-01234')

    def test_init_collection_3(self):
        hdl = Handle(HandleType.Collection, 99999)
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 99999)
        self.assertEqual(hdl.identifier, 'Collection-99999')

    def test_init_collection_4(self):
        with self.assertRaises(ValueError) as context:
            Handle(HandleType.Collection, 100000)
        
    def test_init_document_0(self):
        hdl = Handle(HandleType.Document, 0)
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 0)
        self.assertEqual(hdl.identifier, 'Document-00000')

    def test_init_document_1(self):
        hdl = Handle(HandleType.Document, 12345)
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 12345)
        self.assertEqual(hdl.identifier, 'Document-12345')

    def test_init_document_2(self):
        hdl = Handle(HandleType.Document, 1234)
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 1234)
        self.assertEqual(hdl.identifier, 'Document-01234')
        
    def test_init_document_3(self):
        hdl = Handle(HandleType.Document, 99999)
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 99999)
        self.assertEqual(hdl.identifier, 'Document-99999')

    def test_init_document_4(self):
        with self.assertRaises(ValueError) as context:
            Handle(HandleType.Document, 100000)
            
    def test_init_version_0(self):
        hdl = Handle(HandleType.Version, 0)
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 0)
        self.assertEqual(hdl.identifier, 'Version-000000')
        
    def test_init_version_1(self):
        hdl = Handle(HandleType.Version, 123456)
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 123456)
        self.assertEqual(hdl.identifier, 'Version-123456')

    def test_init_version_2(self):
        hdl = Handle(HandleType.Version, 1234)
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 1234)
        self.assertEqual(hdl.identifier, 'Version-001234')

    def test_init_version_3(self):
        hdl = Handle(HandleType.Version, 999999)
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 999999)
        self.assertEqual(hdl.identifier, 'Version-999999')
        
    def test_init_version_4(self):
        with self.assertRaises(ValueError) as context:
            Handle(HandleType.Version, 1000000)

    def test_from_str_collection_1(self):
        hdl = Handle.from_str('Collection-12345')
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 12345)
        self.assertEqual(hdl.identifier, 'Collection-12345')

    def test_from_str_collection_2(self):
        hdl = Handle.from_str('Collection-00000')
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 0)
        self.assertEqual(hdl.identifier, 'Collection-00000')

    def test_from_str_collection_3(self):
        hdl = Handle.from_str('Collection-99999')
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 99999)
        self.assertEqual(hdl.identifier, 'Collection-99999')

    def test_from_str_collection_4(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Collection-100000')
        
    def test_from_str_collection_5(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Collection-1')

    def test_from_str_document_1(self):
        hdl = Handle.from_str('Document-12345')
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 12345)
        self.assertEqual(hdl.identifier, 'Document-12345')

    def test_from_str_document_2(self):
        hdl = Handle.from_str('Document-00000')
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 0)
        self.assertEqual(hdl.identifier, 'Document-00000')

    def test_from_str_document_3(self):
        hdl = Handle.from_str('Document-99999')
        self.assertEqual(hdl.type, HandleType.Document)
        self.assertEqual(hdl.number, 99999)
        self.assertEqual(hdl.identifier, 'Document-99999')

    def test_from_str_document_4(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Document-100000')
        
    def test_from_str_document_5(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Document-1')
            
    def test_from_str_version_1(self):
        hdl = Handle.from_str('Version-123456')
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 123456)
        self.assertEqual(hdl.identifier, 'Version-123456')

    def test_from_str_version_2(self):
        hdl = Handle.from_str('Version-000000')
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 0)
        self.assertEqual(hdl.identifier, 'Version-000000')

    def test_from_str_version_3(self):
        hdl = Handle.from_str('Version-999999')
        self.assertEqual(hdl.type, HandleType.Version)
        self.assertEqual(hdl.number, 999999)
        self.assertEqual(hdl.identifier, 'Version-999999')

    def test_from_str_version_4(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Version-1000000')
        
    def test_from_str_version_5(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Version-1')

    def test_from_str_invalid_1(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('')

    def test_from_str_invalid_2(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('abc')
            
    def test_from_str_invalid_3(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Version123456')
            
    def test_from_str_invalid_4(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Version 123456')
            
    def test_from_str_invalid_5(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Version--123456')
            
    def test_from_str_invalid_6(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Version-xxxxxx')
            
    def test_from_str_invalid_7(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('-123456')
            
    def test_from_str_invalid_8(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = Handle.from_str('Hello-123456')
            
    def test_from_str_wrong_type_1(self):
        with self.assertRaises(TypeError) as context:
            hdl = Handle.from_str(None)
            
    def test_from_str_wrong_type_2(self):
        with self.assertRaises(TypeError) as context:
            hdl = Handle.from_str(12345)

    def test_from_str_wrong_type_3(self):
        with self.assertRaises(TypeError) as context:
            hdl = Handle.from_str(object())
            
class HandleFunctionTest(TestCase):
    def test_handle_1(self):
        hdl = handle('Collection-12345')
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 12345)
        self.assertEqual(hdl.identifier, 'Collection-12345')

    def test_handle_2(self):
        hdl = handle('Collection-12345')
        hdl = handle(hdl)
        self.assertEqual(hdl.type, HandleType.Collection)
        self.assertEqual(hdl.number, 12345)
        self.assertEqual(hdl.identifier, 'Collection-12345')

    def test_handle_invalid_1(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = handle('Collection-123456')

    def test_handle_invalid_2(self):
        with self.assertRaises(InvalidHandleError) as context:
            hdl = handle('')
            
    def test_handle_wrong_type_1(self):
        with self.assertRaises(TypeError) as context:
            hdl = handle(12345)
            
    def test_handle_wrong_type_2(self):
        with self.assertRaises(TypeError) as context:
            hdl = handle(None)

    def test_handle_wrong_type_3(self):
        with self.assertRaises(TypeError) as context:
            hdl = handle(object())
            
    def test_handle_equal(self):
        self.assertEqual(Handle(HandleType.Collection, 12345), Handle(HandleType.Collection, 12345))
        self.assertEqual(Handle(HandleType.Document, 99999), Handle(HandleType.Document, 99999))
        self.assertEqual(Handle(HandleType.Version, 111111), Handle(HandleType.Version, 111111))

        self.assertNotEqual(Handle(HandleType.Collection, 12345), Handle(HandleType.Collection, 54321))
        self.assertNotEqual(Handle(HandleType.Document, 99999), Handle(HandleType.Document, 11111))
        self.assertNotEqual(Handle(HandleType.Version, 111111), Handle(HandleType.Version, 999999))
        
        self.assertNotEqual(Handle(HandleType.Collection, 12345), Handle(HandleType.Document, 12345))
        self.assertNotEqual(Handle(HandleType.Collection, 12345), Handle(HandleType.Version, 12345))
        self.assertNotEqual(Handle(HandleType.Document, 99999), Handle(HandleType.Collection, 99999))
        self.assertNotEqual(Handle(HandleType.Document, 99999), Handle(HandleType.Version, 99999))
        self.assertNotEqual(Handle(HandleType.Version, 11111), Handle(HandleType.Collection, 11111))
        self.assertNotEqual(Handle(HandleType.Version, 11111), Handle(HandleType.Document, 11111))

    def test_handle_hash(self):
        self.assertEqual(Handle(HandleType.Collection, 12345).__hash__(), Handle(HandleType.Collection, 12345).__hash__())
        self.assertEqual(Handle(HandleType.Document, 99999).__hash__(), Handle(HandleType.Document, 99999).__hash__())
        self.assertEqual(Handle(HandleType.Version, 111111).__hash__(), Handle(HandleType.Version, 111111).__hash__())

        self.assertNotEqual(Handle(HandleType.Collection, 12345).__hash__(), Handle(HandleType.Collection, 54321).__hash__())
        self.assertNotEqual(Handle(HandleType.Document, 99999).__hash__(), Handle(HandleType.Document, 11111).__hash__())
        self.assertNotEqual(Handle(HandleType.Version, 111111).__hash__(), Handle(HandleType.Version, 999999).__hash__())
        
        self.assertNotEqual(Handle(HandleType.Collection, 12345).__hash__(), Handle(HandleType.Document, 12345).__hash__())
        self.assertNotEqual(Handle(HandleType.Collection, 12345).__hash__(), Handle(HandleType.Version, 12345).__hash__())
        self.assertNotEqual(Handle(HandleType.Document, 99999).__hash__(), Handle(HandleType.Collection, 99999).__hash__())
        self.assertNotEqual(Handle(HandleType.Document, 99999).__hash__(), Handle(HandleType.Version, 99999).__hash__())
        self.assertNotEqual(Handle(HandleType.Version, 11111).__hash__(), Handle(HandleType.Collection, 11111).__hash__())
        self.assertNotEqual(Handle(HandleType.Version, 11111).__hash__(), Handle(HandleType.Document, 11111).__hash__())
