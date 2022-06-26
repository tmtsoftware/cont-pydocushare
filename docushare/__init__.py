'''
TODO: document "docushare" module.
'''

from .docushare import DocuShare
from .handle import handle, Handle, HandleType, InvalidHandleError

__all__ = [
    'DocuShare',
    
    'handle',
    'Handle',
    'HandleType',
    'InvalidHandleError',
]

