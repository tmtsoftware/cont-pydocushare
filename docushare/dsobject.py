from abc import ABC
from enum import Enum
from pathlib import Path

from .handle import Handle, HandleType, DocumentHandleNode, CollectionHandleNode


class DocuShareBaseObject(ABC):
    '''Represents one object in DocuShare.

    Parameters
    ----------
    docushare : DocuShare
        The DocuShare site that this object belongs to.
    hdl : Handle
        The DocuShare handle that represents this object.
    '''
    
    def __init__(self, docushare, hdl):
        from .docushare import DocuShare
        if not isinstance(docushare, DocuShare):
            raise TypeError('docushare must be an instance of DocuShare')
        if not isinstance(hdl, Handle):
            raise TypeError('hdl must be an instance of Handle')
        
        self.__docushare = docushare
        self.__hdl       = hdl

    @property
    def docushare(self):
        '''DocuShare : The DocuShare site that this object belongs to.'''
        return self.__docushare

    @property
    def handle(self):
        '''Handle : The DocuShare handle that represents this object.'''
        return self.__hdl

    def __str__(self):
        return f'handle: "{self.handle}"'

class FileObject(DocuShareBaseObject):
    '''Represents one file object in DocuShare.

    Parameters
    ----------
    docushare : DocuShare
        The DocuShare site that this object belongs to.
    hdl : Handle
        The DocuShare handle that represents this object.
    title : str
        Title of this file.
    filename : str
        File name of this file.
    '''
    
    def __init__(self, docushare, hdl, title, filename):        
        super().__init__(docushare, hdl)
        
        if not isinstance(title, str):
            raise TypeError('title must be str')
        if not isinstance(filename, str):
            raise TypeError('filename must be str')

        self._title     = title
        self._filename  = filename
    
    @property
    def title(self):
        '''str : Title of this document.'''
        return self._title

    @property
    def filename(self):
        '''str : File name of this document.'''
        return self._filename

    def __str__(self):
        return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}"'
    
    @property
    def download_url(self):
        '''str : URL to download this document.'''
        from .docushare import Resource
        return self.docushare.url(Resource.Get, self.handle)

    def download(self, path = None, size_for_progress_report = 1000000):
        '''Download this document from the DocuShare site to the local storage.

        Parameters
        ----------
        path : path-like object or None
            If it is None, this method downloads the document as a file in the current directory
            and the file name is determined as suggested by the DocuShare site.
            If it is a directory path, the document is downloaded as a file in the given directory
            and the file name is determined as suggested by the DocuShare site.
            If the given path is not a directory or does not exist, the document is downloaded
            as a file to the given path.
        size_for_progress_report : int
            This method shows a progress bar using `tqdm <https://tqdm.github.io/>` if the file size is
            more than the specified size in bytes.

        Returns
        -------
        path-like object
            Path to the downloaded file.
        '''
        if path is None:
            path = Path.cwd()
        else:
            path = Path(path)
            
        if path.is_dir():
            path = path.joinpath(self.filename)
            
        self.docushare.download(self.handle, path, size_for_progress_report = size_for_progress_report)
        return path

class DocumentObject(FileObject):
    '''Represents one Document object in DocuShare.

    Parameters
    ----------
    docushare : DocuShare
        The DocuShare site that this object belongs to.
    hdl : Handle
        The DocuShare handle that represents this object. The type must be :py:enum:`HandleType.Document`.
    title : str
        Title of this document.
    filename : str
        File name of this document.
    document_control_number : str or None
        Document conrol number of this document. This can be None if document control number is not defined.
    version_handles : list
        Version handles of this document. :py:class:`list` of :py:class:`Handle` instances.'
    '''
    
    def __init__(self, docushare, hdl, title, filename, document_control_number, version_handles):
        super().__init__(docushare, hdl, title, filename)
        
        if hdl.type != HandleType.Document:
            raise ValueError('handle type must be Document')
        if not isinstance(document_control_number, (str, type(None))):
            raise TypeError('document_control_number must be str or None')
        if not isinstance(version_handles, list):
            raise TypeError('verion_handles must be list')
        if not all([isinstance(version_handle, Handle) for version_handle in version_handles]):
            raise TypeError('All elements in verion_handles must be instances of Handle')
        if not all([hdl.type == HandleType.Version for hdl in version_handles]):
            raise ValueError('All handle types in verion_handles must be Version')
        
        self._document_control_number = document_control_number
        self._version_handles         = version_handles

    @property
    def document_control_number(self):
        '''str : Document control number.'''
        return self._document_control_number

    def __str__(self):
        return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}", document_control_number: "{self.document_control_number}"'

    @property
    def version_handles(self):
        ''':py:class:`list` of :py:class:`Handle`: Version handles of this document.'''
        return self._version_handles

    @property
    def versions(self):
        ''':py:class:`list` of :py:class:`VersionObject`: Version objects of this document.'''
        return [self.docushare[ver_hdl] for ver_hdl in self.version_handles]

class VersionObject(FileObject):
    '''Represents one Version object in DocuShare.

    Parameters
    ----------
    docushare : DocuShare
        The DocuShare site that this object belongs to.
    hdl : Handle
        The DocuShare handle that represents this object. The type must be :py:enum:`HandleType.Version`.
    title : str
        Title of this version.
    filename : str
        File name of this version.
    version_number : int
        Version number of this version.
    '''
    
    def __init__(self, docushare, hdl, title, filename, version_number):
        super().__init__(docushare, hdl, title, filename)
        if hdl.type != HandleType.Version:
            raise ValueError('handle type must be Version')
        
        self._version_number = version_number

    @property
    def version_number(self):
        '''int : version number (a sequential number)'''
        return self._version_number

    def __str__(self):
        return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}", version_number: {self.version_number}'

class CollectionDownloadOption(Enum):
    '''Represents a Collection download option.'''

    CHILD_DOCUMENTS = 'Download direct child Documents in the Collection. Does not include Documents in sub Collections.'
    ALL_DESCENDANTS_DOCUMENTS_IN_ONE_DIRECTORY = 'Dowload all documents in the Collection and all descendant Collections to one directory.'
    ALL_DESCENDANTS_IN_TREE_STRUCTURE = 'Download all documents in Collection and all descendant Collections preserving the Collection structure.'
        
class CollectionObject(DocuShareBaseObject):
    '''Represents one Collection object in DocuShare.

    Parameters
    ----------
    docushare : DocuShare
        The DocuShare site that this object belongs to.
    hdl : Handle
        The DocuShare handle that represents this object. The type must be :py:enum:`HandleType.Collection`.
    title : str
        Title of this collection.
    object_handles : list
        Handles of the objects under this collection. :py:class:`list` of :py:class:`Handle` instances.'
    '''
    
    def __init__(self, docushare, hdl, title, object_handles):
        super().__init__(docushare, hdl)
        
        if hdl.type != HandleType.Collection:
            raise ValueError('handle type must be Collection')
        if not isinstance(title, str):
            raise TypeError('title must be str')
        if not isinstance(object_handles, list):
            raise TypeError('object_handles must be list')
        if not all([isinstance(object_handle, Handle) for object_handle in object_handles]):
            raise TypeError('All elements in object_handles must be instances of Handle')
        
        self._title          = title
        self._object_handles = object_handles

    @property
    def title(self):
        '''str : Title of this collection.'''
        return self._title

    def __str__(self):
        return f'handle: "{self.handle}", title: "{self.title}"'

    @property
    def object_handles(self):
        ''':py:class:`list` of :py:class:`Handle`: Handles of the objects under this collection.'''
        return self._object_handles

    @property
    def object_handle_tree(self):
        '''Tree structure under this collection.

        The root node of the tree structure is this collection. Each node is an instance of 
        :py:class:`CollectionHandleNode` or :py:class:`DocumentHandleNode`. In addition to
        the DocuShare handle information (e.g. Collection-xxxxx, Document-zzzzz), these classes
        include the parent/child relation information using :py:class:`anytree.node.nodemixin.NodeMixin`.
        Therefore, you can traverse, visualize and search the tree structure using
        `anytree <https://anytree.readthedocs.io/en/latest/index.html>`_ API.

        Examples
        --------

        The example below shows the tree structure under the Collection-10000.
        
        >>> from docushare import *
        >>> from anytree import RenderTree
        >>> ds = DocuShare(base_url='https://your.docushare.domain/docushare/')
        >>> ds.login()
        >>> collection = ds['Collection-10000']
        >>> print(RenderTree(collection.object_handle_tree).by_attr('identifier'))
        Collection-10000
        ├── Collection-11000
        │   ├── Document-11001
        │   └── Document-11002
        ├── Collection-12000
        │   ├── Document-12001
        │   └── Document-12002
        ├── Document-10001
        ├── Document-10002
        └── Document-10003

        In principle, each node in the tree contains only handle and parent/child information. To show more
        information like title in the tree visualization, you need to query properties like this:

        >>> for pre, fill, handle in RenderTree(collection.object_handle_tree):
        ...     node_str = f'{pre}{handle}'
        ...     hdl_obj = ds[handle]
        ...     print(node_str.ljust(25), hdl_obj.title)
        Collection-10000          (Title of Collection-10000)
        ├── Collection-11000      (Title of Collection-11000)
        │   ├── Document-11001    (Title of Document-11001)
        │   └── Document-11002    (Title of Document-11001)
        ├── Collection-12000      (Title of Collection-12000)
        │   ├── Document-12001    (Title of Document-12001)
        │   └── Document-12002    (Title of Document-12002)
        ├── Document-10001        (Title of Document-10001)
        ├── Document-10002        (Title of Document-10002)
        └── Document-10003        (Title of Document-10003)

        If you want to get all Document handles under Collection-10000 and its descendant Collections,
        you may want to use :py:meth:`CollectionHandleNode.leaves`:

        >>> for doc_hdl in collection.object_handle_tree.leaves:
        ...     doc_obj = ds[doc_hdl]
        ...     print(f'{doc_hdl.identifier}    {doc_obj.title}')
        Document-11001    (Title of Document-11001)
        Document-11002    (Title of Document-11001)
        Document-12001    (Title of Document-12001)
        Document-12002    (Title of Document-12002)
        Document-10001    (Title of Document-10001)
        Document-10002    (Title of Document-10002)
        Document-10003    (Title of Document-10003)
        '''
        children = []
        for obj_hdl in self._object_handles:
            if obj_hdl.type == HandleType.Document:
                children.append(DocumentHandleNode(obj_hdl.number))
            elif obj_hdl.type == HandleType.Collection:
                children.append(self.docushare[obj_hdl].object_handle_tree)
            else:
                assert False, 'code must not reach here'
        root = CollectionHandleNode(self.handle.number, children)
        return root

    def download(self,
                 destination_path = None,
                 option = CollectionDownloadOption.CHILD_DOCUMENTS,
                 progress_report = True,
                 collection_title_as_directory_name = True):
        '''Downlaod the documents in this Collection.

        Parameters
        ----------
        destination_path : path-like object or None
            This method downloads the documents in this Collection to this directory. If it is None,
            they will be downloaded to the current directory.
        option : CollectionDownloadOption
            TODO: document
        progress_report : bool
            Show progress bar using `tqdm <https://tqdm.github.io/>` if it is True.
        collection_title_as_directory_name : bool
            Use the Collection title as the directory name if it is True. Otherwise, the Collection handle
            will be used as the directory name.

        Returns
        -------
        list
            :py:class:`list` of downloaded files as :py:class:`pathlib.Path`.
        '''

        if destination_path is None:
            destination_path = Path.cwd()
        else:
            destination_path = Path(destination_path)

        if destination_path.exists() and (not destination_path.is_dir()):
            raise NotADirectoryError(f'{destination_path} is not a directory.')            

        # List of tuples
        #   The first element in the tuple is the DocumentObject to download.
        #   The second element is the destination path.
        download_infos = []
        
        if option == CollectionDownloadOption.CHILD_DOCUMENTS:
            for obj_hdl in self.object_handles:
                if obj_hdl.type == HandleType.Document:
                    doc_obj   = self.docushare[obj_hdl]
                    file_path = destination_path.joinpath(doc_obj.filename)
                    download_infos.append( (doc_obj, file_path) )
        elif option == CollectionDownloadOption.ALL_DESCENDANTS_DOCUMENTS_IN_ONE_DIRECTORY:
            for obj_hdl in self.object_handle_tree.leaves:
                doc_obj   = self.docushare[obj_hdl]
                file_path = destination_path.joinpath(doc_obj.filename)
                download_infos.append( (doc_obj, file_path) )
        elif option == CollectionDownloadOption.ALL_DESCENDANTS_IN_TREE_STRUCTURE:
            for doc_hdl in self.object_handle_tree.leaves:
                file_path = destination_path
                for col_hdl in doc_hdl.path[1:-1]:
                    if collection_title_as_directory_name:
                        file_path = file_path.joinpath(col_hdl.identifier)
                    else:
                        col_obj = self.docushare[col_hdl]
                        file_path = file_path.joinpath(col_obj.title)
                        
                doc_obj = self.docushare[doc_hdl]
                file_path = file_path.joinpath(doc_obj.filename)
                download_infos.append( (doc_obj, file_path) )

        if len(download_infos) == 0:
            return []
               
        if progress_report:
            try:
                from tqdm import tqdm
                iterator = tqdm(download_infos)
            except:
                iterator = download_infos
        else:
            iterator = download_infos
            
        for doc_obj, file_path in iterator:
            file_path.parent.mkdir(parents = True, exist_ok = True)
            self.docushare.download(doc_obj.handle, file_path)

        return [di[1] for di in download_infos]

