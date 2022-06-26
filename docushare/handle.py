import re
from enum import Enum

class HandleType(Enum):
    Collection = 'Collection'
    Document   = 'Document'
    Version    = 'Version'

    def __init__(self, identifier):
        self.__identifier = identifier

    @property
    def identifier(self):
        return self.__identifier

    def __str__(self):
        return self.identifier
   
class Handle:
    '''This class represents a handle like Collection-10101, Document-20202 and Version-123456.'''

    # The number of digits for the handle number.
    __num_of_digits = {
        HandleType.Collection: 5,
        HandleType.Document  : 5,
        HandleType.Version   : 6,
    }

    def __init__(self, handle_type, number):
        '''Constructor

        Parameters:
        handle_type (HandleType): Type of handle.
        number (int): Handle number
        '''
        
        if not isinstance(handle_type, HandleType):
            raise TypeError('handle_type must be one of HandleType enum')
        if not isinstance(number, int):
            raise TypeError('number must be int')

        if number < 0:
            raise ValueError('number must be a positive number')

        # Check the number of digits.
        max_number = 10 ** self.__num_of_digits[handle_type] - 1
        if number > max_number:
            raise ValueError(f'number must be {max_number} or less for handle_type = {handle_type}.')
        
        self.__handle_type = handle_type
        self.__number      = number

    @property
    def type(self):
        return self.__handle_type

    @property
    def number(self):
        return self.__number

    @property
    def identifier(self):
        type_id = self.__handle_type.identifier
        num_of_digits = self.__num_of_digits[self.__handle_type]
        number_str = format(self.__number, f'0{num_of_digits}')
        return f'{type_id}-{number_str}'

    @classmethod
    def from_str(cls, handle_str):
        for handle_type in HandleType:
            pattern = f'^{handle_type.identifier}-([0-9]{{{cls.__num_of_digits[handle_type]}}})$'
            match = re.match(pattern, handle_str)
            if match:
                return Handle(handle_type, int(match.group(1)))

        raise ValueError(f'"{handle_str}" is not a valid handle.')

    def __str__(self):
        return self.identifier

    def __eq__(self, obj):
        return isinstance(obj, Handle) and obj.type == self.type and obj.number == self.number

    def __hash__(self):
        return hash(self.identifier)

def handle(handle_str):
    '''
    This utility method converts handle string (e.g., Collection-10101, Document-20202, Version-123456)
    to an instance of Handle.
    '''
    if isinstance(handle_str, Handle):
        return handle_str
    
    return Handle.from_str(handle_str)
