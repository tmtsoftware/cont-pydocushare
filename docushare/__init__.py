'''
TODO: document "docushare" module.
'''

from .docushare import DocuShare
from .handle import handle, Handle, HandleType, InvalidHandleError
from .util import join_url

__all__ = [
    'DocuShare',

    'handle',
    'Handle',
    'HandleType',
    'InvalidHandleError',

    'join_url',
]

