import re
from enum import Enum

from anytree import NodeMixin

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
            raise ValueError('handle_number must be zero or a positive integer')

        # TODO: is zero really a valid handle number?

        self.__handle_type   = handle_type
        self.__handle_number = handle_number
       
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
        return f'{self.__handle_type.identifier}-{self.__handle_number}'

    @classmethod
    def from_str(cls, handle_str):
        '''Parse the given string as a DocuShare handle and return Handle instance.

        Parameters
        ----------
        handle_str : str or bytes-like object
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
            pattern = f'^{handle_type.identifier}-([0-9]+)$'
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

class HandleNode(Handle, NodeMixin):
    '''This class represents a DocuShare handle in a tree structure.

    Parameters
    ----------
    handle_type : HandleType
        Handle type.
    handle_number : int
        Handle number.
    '''

    def __init__(self, handle_type, handle_number):
        super(HandleNode, self).__init__(handle_type, handle_number)
        self._readonly_node = True

    def _pre_attach(self, parent):
        if self._readonly_node:
            raise RuntimeError('It is not allowed to change the handle tree structure.')

    def _pre_detach(self, parent):
        if self._readonly_node:
            raise RuntimeError('It is not allowed to change the handle tree structure.')
        
    @property
    def ancestors(self):
        '''All parent Collection handles and their parent Collection handles.'''
        return super().ancestors

    @property
    def anchestors(self):
        '''All parent Collection handles and their parent Collection handles.'''
        return super().anchestors

    @property
    def children(self):
        '''All child handles.'''
        return super().children
    
    @property
    def depth(self):
        '''Number of handles to the root :py:class:`CollectionHandleNode`.

        Notes
        -----
        The root is not necessarily a root Collection of the DocuShare site.
        '''
        return super().depth

    @property
    def descendants(self):
        '''All child handles and their child handles.'''
        return super().descendants

    @property
    def height(self):
        '''Number of handles on the longest path to a leaf :py:class:`HandleNode`.'''
        return super().height

    @property
    def is_leaf(self):
        '''Indicates if this handle node has no children.'''
        return super().is_leaf

    @property
    def is_root(self):
        '''Indicates if this handle node is tree root.

        Notes
        -----
        This handle does not necessarily represent a root Collection/Document in the DocuShare site even if this property is True.
        '''
        return super().is_root
    
    @property
    def leaves(self):
        '''Tuple of all leaf handles excluding Collection handles.'''
        return tuple([hdl_node for hdl_node in super().leaves if hdl_node.type != HandleType.Collection])

    @property
    def parent(self):
        '''Parent Collection handle.'''
        return super().parent

    @parent.setter
    def parent(self, parent):
        super(HandleNode, HandleNode).parent.fset(self, parent)

    @property
    def path(self):
        '''Path of this handle.'''
        return super().path
    
    @property
    def root(self):
        '''Root Collection handle.

        Notes
        -----
        It is not necessarily a root Collection of the DocuShare site.
        '''
        return super().root

    @property
    def separator(self):
        ''''''
        return super().separator

    @property
    def siblings(self):
        '''Tuple of handles with the same parent Collection handle.'''
        return super().siblings
    
class DocumentHandleNode(HandleNode):
    '''This class represents a DocuShare Document handle in a tree structure.

    Document handle is always a leaf node in the tree structure. It cannot have a child.

    Parameters
    ----------
    handle_number : int
        Handle number.
    '''

    def __init__(self, handle_number):
        super(DocumentHandleNode, self).__init__(HandleType.Document, handle_number)

    @property
    def children(self):
        '''All child handles. It is always an empty :py:class:`list`.'''
        return []

    @property
    def descendants(self):
        '''All child handles and their child handles.

        It is always an empty :py:class:`tuple`.'''
        return tuple()

    @property
    def height(self):
        '''Number of handles on the longest path to a leaf :py:class:`HandleNode`.

        It is always zero.'''
        return 0

    @property
    def is_leaf(self):
        '''Indicates if this handle node has no children.

        It is always True.'''
        return True

    @property
    def leaves(self):
        '''Tuple of all leaf handles excluding Collection handles.

        It is always a :py:class:`tuple` that includes this instance itself only.'''
        return (self, )

   
class CollectionHandleNode(HandleNode):
    '''This class represents a DocuShare Collection handle in a tree structure.

    Parameters
    ----------
    handle_number : int
        Handle number.
    children : list
        :py:class:`list` of :py:class:`CollectionHandleNode` and :py:class:`DocumentHandleNode`. Children of this collection.
    '''

    def __init__(self, handle_number, children = []):
        super(CollectionHandleNode, self).__init__(HandleType.Collection, handle_number)

        if not isinstance(children, list):
            raise TypeError('children must be list')
        if not all([isinstance(child, HandleNode) for child in children]):
            raise TypeError('All elements in children must be an instance of HandleNode.')

        for child in children:
            child._readonly_node = False
            child.parent = self
            child._readonly_node = True

class InvalidHandleError(ValueError):
    '''Indicates an invalid DocuShare handle.

    Parameters
    ----------
    invalid_handle_str : str
        Invalid DocuShare handle.
    '''
    
    def __init__(self, invalid_handle_str):
        super().__init__(f'{invalid_handle_str} is not a valid DocuShare handle.')
