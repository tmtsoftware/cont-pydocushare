'''
TODO: document "docushare" module.
'''


from .docushare import DocuShare, Resource, PasswordOption, DocuShareSystemError
from .handle import handle, Handle, HandleType, InvalidHandleError
from .parser import ParseError, parse_if_system_error_page, parse_login_page, parse_property_page, parse_history_page
from .util import join_url

__all__ = [
    'DocuShare',
    'Resource',
    'PasswordOption',
    'DocuShareSystemError',

    'handle',
    'Handle',
    'HandleType',
    'InvalidHandleError',

    'ParseError',
    'parse_if_system_error_page',
    'parse_login_page',
    'parse_property_page',
    'parse_history_page',
    
    'join_url',
]

