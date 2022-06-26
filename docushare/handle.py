import re
from enum import Enum

def handle(handle_str):
    '''Utility function to convert a handle string to a canonical instance.

    Parameters
    ----------
    handle_str : str or Handle
       A string that represents a DocuShare handle like 'Document-20202'.
       If an instance of Handle is given, this method simply returns the same instance.

    Returns
    -------
    Handle
        A canonical instance that represents the given handle.
    '''
    if isinstance(handle_str, Handle):
        return handle_str
    
    return Handle.from_str(handle_str)

class HandleType(Enum):
    '''Represents a DocuShare handle type.'''
    
    Collection = 'Collection'
    Document   = 'Document'
    Version    = 'Version'

    def __init__(self, identifier):
        self.__identifier = identifier

    @property
    def identifier(self):
        '''str: Canonical string representation of the DocuShare handle type.'''
        return self.__identifier

    def __str__(self):
        return self.identifier
  
class Handle:
    '''This class represents a DocuShare handle.

    DocuShare identifies each object on your DocuShare site with a unique handle like 
    Collection-10101, Document-20202 and Version-123456. This class represents one 
    handle in the canonical way for the PyDocuShare API.

    It consists of two parts: type and number. For example, the handle 'Document-20202'
    has 'Collection' type and 20202 is the number.

    Parameters
    ----------
    handle_type : HandleType
        Handle type.
    handle_number : int
        Handle number.
    '''

    def __init__(self, handle_type, handle_number):
        if not isinstance(handle_type, HandleType):
            raise TypeError('handle_type must be one of HandleType enum')
        if not isinstance(handle_number, int):
            raise TypeError('handle_number must be int')
        if handle_number < 0:
            raise ValueError('handle_number must be a positive integer')

        # Check the number of digits.
        max_number = 10 ** self.__num_of_digits[handle_type] - 1
        if handle_number > max_number:
            raise ValueError(f'handle_number must be {max_number} or less for handle_type = {handle_type}.')
        
        self.__handle_type   = handle_type
        self.__handle_number = handle_number
        
    # The number of digits for the handle number.
    #
    # TODO: The number of digits is maybe not be the same for all DocuShare site.
    #       It would be useful to make it configurable.
    __num_of_digits = {
        HandleType.Collection: 5,
        HandleType.Document  : 5,
        HandleType.Version   : 6,
    }
       
    @property
    def type(self):
        '''HandleType: Handle type.'''
        return self.__handle_type
    
    @property
    def number(self):
        '''int: Handle number.'''
        return self.__handle_number

    @property
    def identifier(self):
        '''str: String representation of this handle like "Document-20202".'''
        type_id = self.__handle_type.identifier
        num_of_digits = self.__num_of_digits[self.__handle_type]
        number_str = format(self.__handle_number, f'0{num_of_digits}')
        return f'{type_id}-{number_str}'

    @classmethod
    def from_str(cls, handle_str):
        '''Parse the given string as a DocuShare handle and return Handle instance.

        Parameters
        ----------
        handle_str : str
           A string that represents a DocuShare handle like 'Document-20202'.

        Returns
        -------
        Handle
            A canonical instance that represents the given handle.

        Raises
        ------
        InvalidHandleError
            If the given string is not a valid DocuShare handle.
        '''
        
        for handle_type in HandleType:
            pattern = f'^{handle_type.identifier}-([0-9]{{{cls.__num_of_digits[handle_type]}}})$'
            match = re.match(pattern, handle_str)
            if match:
                return Handle(handle_type, int(match.group(1)))

        raise InvalidHandleError(handle_str)
   
    def __str__(self):
        return self.identifier

    def __eq__(self, obj):
        return isinstance(obj, Handle) and obj.type == self.type and obj.number == self.number

    def __hash__(self):
        return hash(self.identifier)

class InvalidHandleError(ValueError):
    '''Indicates an invalid DocuShare handle.

    Parameters
    ----------
    invalid_handle_str : str
        Invalid DocuShare handle.
    '''
    
    def __init__(self, invalid_handle_str):
        super().__init__(f'{invalid_handle_str} is not a valid DocuShare handle.')

