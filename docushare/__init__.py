'''This is the PyDocuShare module that provides Python API to interact with DocuShare.

In DocuShare, each docuemnt and object can be identified by a handle like Document-00000, Version-000000,
Collection-00000. The PyDocuShare API allows you to access the files and properties of the documents
through the handles. See more details in the examples and API reference below.

Examples
--------

Example below downloads Document-12345 from your DocuShare site at https://your.docushare.domain/docushare/:

>>> from docushare import *
>>> ds = DocuShare(base_url='https://your.docushare.domain/docushare/')
>>> ds.login()
_ 
Enter your username for https://your.docushare.domain/docushare/
Username: your_user_name
_ 
Enter password of "your_user_name" for https://your.docushare.domain/docushare/
Password:
_ 
>>> doc = ds.object('Document-12345')
>>> print(f'Download "{doc.title}" as "{doc.filename}".')
>>> doc.download()
PosixPath('/path/to/your/current/directory/{doc.filename}')

``ds.object(handle)`` may be replaced by ``ds[handle]`` as shown below:

>>> doc = ds['Document-12345']

To download a specific version, you can also specify Version handle:

>>> ver = ds['Version-123456']
>>> print(f'Download "{ver.title}" as "{ver.filename}".')
>>> ver.download()
PosixPath('/path/to/your/current/directory/{ver.filename}')

You can get the version information as shown below:

>>> doc = ds['Document-12345']
>>> for ver_hdl in doc.version_handles:
...     ver = ds[ver_hdl]
...     print(f'{ver_hdl} is version #{ver.version_number} for {doc.handle}.')
'''

from .docushare import DocuShare, Resource, PasswordOption, DocuShareSystemError, DocuShareNotFoundError, DocuShareNotAuthorizedError
from .dsobject import DocuShareBaseObject, FileObject, DocumentObject, VersionObject, CollectionObject, CollectionDownloadOption
from .handle import handle, Handle, HandleNode, CollectionHandleNode, DocumentHandleNode, HandleType, InvalidHandleError
from .parser import DocuShareParseError
from .util import join_url

__all__ = [
    'DocuShare',
    'Resource',
    'PasswordOption',
    'DocuShareSystemError',
    'DocuShareNotFoundError',
    'DocuShareNotAuthorizedError',

    'DocuShareBaseObject',
    'FileObject',
    'DocumentObject',
    'VersionObject',
    'CollectionObject',
    'CollectionDownloadOption',
    
    'handle',
    'Handle',
    'HandleNode',
    'CollectionHandleNode',
    'DocumentHandleNode',
    'HandleType',
    'InvalidHandleError',

    'DocuShareParseError',
    
    'join_url',
]

