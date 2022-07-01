import getpass
import json
import logging
import subprocess
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import requests

import pyduktape

from .dsobject import DocumentObject, VersionObject, CollectionObject
from .handle import Handle, HandleType, handle
from .parser import (DocuShareParseError,
                     is_not_authorized_page, is_not_found_page,
                     parse_history_page, parse_if_system_error_page,
                     parse_login_page, parse_property_page,
                     parse_collection_page)
from .util import join_url


class Resource(Enum):
    '''This enum represents one DocuShare resource.'''
    
    DSWEB      = '(base URL for any resources in DocuShare)'
    Login      = 'HTTP GET : login page to get login token'
    ApplyLogin = 'HTTP POST: to send credential information'
    Services   = 'HTTP GET : property page'
    History    = 'HTTP GET : version history of a document'
    Get        = 'HTTP GET : get a document file'
    View       = 'HTTP GET : view a collection'

class PasswordOption(Enum):
    '''Option for password prompting.'''
    
    ASK        = 'Always prompts the user to enter the password in the console.'
    USE_STORED = 'Try to use the stored password if exists. If not, prompts the user to enter the password in the console. Correctly authenticated password will be stored. Note that `keyring` module is required to use this option.'

class DocuShareSystemError(RuntimeError):
    '''Raised if the DocuShare site encounters a system error.

    Parameters
    ----------
    error_code : str
        Error code returned by DocuShare.
    error_message : str
        Error message returned by DocuShare.
    docushare : DocuShare
        DocuShare instance to get the context for detailed error messages.
    url : str
        URL that caused this error.
    '''
    
    def __init__(self, error_code, error_message, docushare, url):
        self.__error_code    = error_code
        self.__error_message = error_message
        self.__username      = docushare.username
        self.__url           = url
        msg = f'DocuShare system error (code: {error_code}, message: {error_message}, username: {docushare.username}, url: {url})'
        super().__init__(msg)

    @property
    def error_code(self):
        '''str: Error code returned from DocuShare.'''
        return self.__error_code
    
    @property
    def error_message(self):
        '''str: Error message returned from DocuShare.'''
        return self.__error_message

    @property
    def url(self):
        '''str: URL that caused this error.'''
        return self.__url
    
    @property
    def username(self):
        '''str: DocuShare username when this error was returned.'''
        return self.__username

class DocuShareNotFoundError(RuntimeError):
    '''Raised if the object does not exist in the DocuShare site.

    Parameters
    ----------
    docushare : DocuShare
        DocuShare instance to get the context for detailed error messages.
    url : str
        URL that does not exist.
    '''
    
    def __init__(self, docushare, url):
        self.__username = docushare.username
        self.__url      = url
        msg = f'{url} does not exist (username: {docushare.username})'
        super().__init__(msg)

    @property
    def url(self):
        '''str: URL that does not exist.'''
        return self.__url
    
    @property
    def username(self):
        '''str: DocuShare username when this error was returned.'''
        return self.__username
    
class DocuShareNotAuthorizedError(RuntimeError):
    '''Raised if it is not authorized to access a DocuShare URL.

    Parameters
    ----------
    docushare : DocuShare
        DocuShare instance to get the context for detailed error messages.
    url : str
        URL that is not authorized to access.
    '''
    
    def __init__(self, docushare, url):
        self.__username = docushare.username
        self.__url      = url
        msg = f'"{docushare.username}" is not authorized to access {url}.'
        super().__init__(msg)

    @property
    def url(self):
        '''str: URL that is not authorized to access.'''
        return self.__url
    
    @property
    def username(self):
        '''str: DocuShare username who is not authorized to access the URL.'''
        return self.__username

class DocuShare:
    '''This class represents a session to access a DocuShare site.

    An instance of this class stores login session so that the user does not have to enter the authentication
    information many times. It also caches some metadata so that it does not have to access the DocuShare
    multiple times to get the same information.

    Parameters
    ----------
    base_url : str
        Base URL of DocuShare. Both 'http' and 'https' schemes are supported.
        For example, https://your.docushare.domain/docushare/.

    Warnings
    --------
    This class is not thread-safe. Use an appropriate mechanism if you want to use an instance of this class
    in multiple threads.
    '''
    
    def __init__(self, base_url):        
        # Check if the given URL is valid.
        parse_result = urlparse(base_url)
        if parse_result.scheme != 'http' and parse_result.scheme != 'https':
            raise ValueError(f'base_url was {base_url}, but it must start with "http://" or "https://"')
        if not parse_result.netloc:
            raise ValueError(f'"{base_url}" is an invalid URL. It must be in the form of https://www.example.org/.')
        if not parse_result.path.endswith('/'):
            base_url = base_url + '/'

        # Default logging settings to output log messages to stdout.
        self.__logger = logging.getLogger(__name__)
        log_handler   = logging.StreamHandler() # to output stdout.
        log_formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
        log_handler.setFormatter(log_formatter)
        self.__logger.addHandler(log_handler)

        self.__base_url = base_url
        self.__session  = requests.Session()
        self.__username = None
        self.__dsobjects = {} # Dict to cache the DocuShare object.
                              # The key is an instance of Handle,
                              # and the value is an instance of DocuShareBaseObject.

    @property
    def logger(self):
        '''logging.Logger: Logger of this instance

        It may be useful to change logging settings like log level.

        Examples
        --------
        >>> import logging
        >>> ds = DocuShare(base_url='https://your.domain/docushare/')
        >>> ds.logger.setLevel(logging.DEBUG)
        '''
        return self.__logger

    def http_get(self, url):
        '''Access the given URL with HTTP GET method using the current DocuShare session.

        This method may be useful to access the resource that PyDocuShare does not directly support
        (e.g. Wiki, Calendar).

        Parameters
        ----------
        url : str
            URL to access.

        Returns
        -------
        requests.Response
            HTTP response.

        Raises
        ------
        requests.HTTPError
            If HTTP error status code was returned.
        DocuShareSystemError
            If the DocuShare site encounters a system error.
        DocuShareNotAuthorizedError
            If the user is not authorized to access the URL.
        DocuShareParseError
            If this method fails to parse the DocuShare system error page.
        '''
        self.__logger.info(f'HTTP GET  {url}')
        headers = {'Accept-Language': 'en-US,en;q=0.9'} # Specify English.
        response = self.__session.get(url, headers = headers, stream=True)
        response.raise_for_status()

        try:
            error_code, error_message = parse_if_system_error_page(response)
        except Exception as err:
            raise DocuShareParseError(self, url, err)
            
        if error_code:
            raise DocuShareSystemError(error_code, error_message, self, url)

        if is_not_authorized_page(response):
            raise DocuShareNotAuthorizedError(self, url)

        return response

    def http_post(self, url, data = None):
        '''Access the given URL with HTTP POST method using the current DocuShare session.

        This method may be useful to access the resource that PyDocuShare does not directly support
        (e.g. uploading documents).

        Parameters
        ----------
        url : str
            URL to access.

        data
           See :py:meth:`requests.Session.post` for more details.

        Returns
        -------
        requests.Response
            HTTP response.

        Raises
        ------
        requests.HTTPError
            If HTTP error status code was returned.
        '''
        self.__logger.info(f'HTTP POST {url}')
        response = self.__session.post(url, data = data)
        response.raise_for_status()
        return response

    def url(self, resource = None, hdl = None):
        if not resource:
            return self.__base_url

        if not isinstance(resource, Resource):
            raise TypeError('resource must be one of Resource enum')

        if resource == Resource.DSWEB:
            return join_url(self.__base_url, 'dsweb/')
        elif resource == Resource.Login:
            return join_url(self.url(Resource.DSWEB), 'Login')
        elif resource == Resource.ApplyLogin:
            return join_url(self.url(Resource.DSWEB), 'ApplyLogin')
        elif resource == Resource.Services:
            if not isinstance(hdl, Handle):
                raise TypeError('hdl must be an instance of Handle')
            return join_url(self.url(Resource.DSWEB), 'Services/', hdl.identifier)
        elif resource == Resource.History:
            if not isinstance(hdl, Handle):
                raise TypeError('hdl must be an instance of Handle')
            if hdl.type != HandleType.Document:
                raise ValueError('handle type must be Document')
            return join_url(self.url(Resource.DSWEB), 'ServicesLib/', hdl.identifier + '/', 'History')
        elif resource == Resource.Get:
            if not isinstance(hdl, Handle):
                raise TypeError('hdl must be an instance of Handle')
            if hdl.type != HandleType.Document and hdl.type != HandleType.Version:
                raise ValueError('handle type must be Document or Version')
            return join_url(self.url(Resource.DSWEB), 'Get/', hdl.identifier)
        elif resource == Resource.View:
            if not isinstance(hdl, Handle):
                raise TypeError('hdl must be an instance of Handle')
            if hdl.type != HandleType.Collection:
                raise ValueError('handle type must be Collection')
            return join_url(self.url(Resource.DSWEB), 'View/', hdl.identifier)
        else:
            assert False, 'code must not reach here'
   
    def login(
            self,
            username = None,
            password = PasswordOption.USE_STORED,
            retry_count = 3,
            domain = 'DocuShare'):
        '''Login the DocuShare site.

        This must be executed, at least, once before accessing any other resources in DocuShare.

        Parameters
        ----------

        username : str or None
            Username for Docushare. Specify None to prompt the user to enter the username.

        password : str or PasswordOption
            Password for the DocuShare user.
            If a string is given, it is considered as the password and this method never prompts the user.
            If an :class:`PasswordOption` enum is given, this method behaves as described in each enum
            value.
        
        retry_count : int
            The user will have a chance to enter the credentials this amount of time.

        domain : str
            Domain to specify when logging in DocuShare. Typically, it is 'DocuShare'.

        Raises
        ------
        DocuShareParseError
            If this method fails to parse the DocuShare login page.
        '''

        if not (username is None or isinstance(username, str)):
            raise TypeError('username must be None or str')
        
        if not isinstance(password, (str, PasswordOption)):
            raise TypeError('password must be str or one of PasswordOption enum')

        if not isinstance(retry_count, int) or retry_count < 1:
            raise TypeError('retry_count must be a positive integer')

        if not isinstance(domain, str):
            raise TypeError('domain must be str')

        self.cookies.clear()
        self.__username = None
        
        if username is None:
            print(f'\nEnter your username for {self.__base_url}')
            entered_username = input('Username: ')
        else:
            entered_username = username

        login_url = self.url(Resource.Login)

        if password == PasswordOption.ASK:
            print(f'\nEnter password of "{entered_username}" for {login_url}')
            entered_password = getpass.getpass('Password: ')
        elif password == PasswordOption.USE_STORED:
            entered_password = self.__get_password(entered_username)
            if not entered_password:
                print(f'\nEnter password of "{entered_username}" for {login_url}')
                entered_password = getpass.getpass('Password: ')
        else:
            entered_password = password

        # Open the DocuShare login page, get the login token and JavaScript for
        # challenge-response authentication.
        #
        # Note that, JSESSIONID is added to the cookies when the login page is
        # opened and it is saved as a part of self.__session.
        login_token, challenge_js_url = self.__open_and_parse_login_page()
        challenge_js = self.http_get(challenge_js_url).text

        # Get the challenge response.
        self.__logger.debug(f'challenge_js: {challenge_js}')
        challenge_response = self.__challenge_response(
            password = entered_password,
            login_token = login_token,
            challenge_js = challenge_js,
        )

        # Send credentails to DocuShare.
        login_info = {
            'response': challenge_response,
            'login_token': login_token,
            'bookmark': '',
            'username': entered_username,
            'password': '',
            'domain': domain,
            'Login': 'Login'
        }
        
        # Do not log 'response' because it can be a hint to an attacker.
        self.__logger.debug(f'login_token = {login_token}')
        self.__logger.debug(f'username    = {entered_username}')
        self.__logger.debug(f'domain      = {domain}')
        self.http_post(self.url(Resource.ApplyLogin), data = login_info)

        self.__logger.debug(f'cookies.keys() = {self.cookies.keys()}')

        # If the authentication is successful, 'AmberUser' is added to the
        # cookies.
        if 'AmberUser' not in self.cookies.keys():
            if retry_count <= 1:
                raise RuntimeError(f'Failed to login at {login_url}')
            elif password == PasswordOption.USE_STORED:
                # Delete unmatched password from the keyring, and ask the
                # password again.
                print(f'\nFailed to login at {login_url}.')
                self.__delete_password(entered_username)
                self.login(username = username,
                           password = PasswordOption.USE_STORED,
                           retry_count = retry_count - 1,
                           domain = domain)
            elif password == PasswordOption.ASK:
                print(f'\nFailed to login at {login_url}.')
                self.login(username = username,
                           password = PasswordOption.ASK,
                           retry_count = retry_count - 1,
                           domain = domain )
            else:
                raise RuntimeError(f'Failed to login at {login_url}.')

        # If successfully logged in, record the username.
        self.__username = entered_username
        if password == PasswordOption.USE_STORED:
            self.__set_password(entered_username, entered_password)

        # The entered password is no longer needed. Remove it from the memory.
        del entered_password

    @property
    def cookies(self):
        '''Cookies of the current session.

        See more details in :py:attr:`requests.Session.cookies`.'''
        return self.__session.cookies
    
    @property
    def is_logged_in(self):
        '''boolean: indicates if this instance successfully logged in the DocuShare site.'''
        return 'AmberUser' in self.cookies.keys()

    def __check_if_logged_in(self):
        if not self.is_logged_in:
            raise RuntimeError('Not logged in yet. Login first.')
        
    @property
    def username(self):
        '''str or None: Currently logged in DocuShare username, or None if login has not been done yet.'''
        return self.__username

    def __open_and_parse_login_page(self):
        login_url = self.url(Resource.Login)
        login_page = self.http_get(login_url)

        try:
            login_token, challenge_js_src = parse_login_page(login_page.text)
        except Exception as err:
            raise DocuShareParseError(self, login_url, err)
            
        challenge_js_url = join_url(login_url, challenge_js_src)
        self.__logger.debug(f'login_token = {login_token}')
        self.__logger.debug(f'challenge_js_src = {challenge_js_src}')
        self.__logger.debug(f'challenge_js_url = {challenge_js_url}')
        self.__logger.debug(f'cookies.keys()   = {self.cookies.keys()}')
        if 'JSESSIONID' not in self.cookies.keys():
            self.__logger.warning('JSESSIONID is missing in the cookies.')
        return login_token, challenge_js_url

    @staticmethod
    def __challenge_response(password, login_token, challenge_js):
        js_context = pyduktape.DuktapeContext()
        js_context.eval_js(challenge_js)
        js_context.set_globals(arg1=password, arg2=login_token)
        response = js_context.eval_js('obscure_string(arg1,arg2);')
        return response

    def __get_password(self, username):
        try:
            import keyring
            password = keyring.get_password(self.__base_url, username)
            if password:
                self.__logger.info(f'Found stored password of "{username}" for {self.__base_url}.')
            return password
        except:
            return None

    def __set_password(self, username, password):
        try:
            import keyring
            keyring.set_password(self.__base_url, username, password)
            self.__logger.info(f'Stored password of "{username}" for {self.__base_url}.')
        except:
            pass
        
    def __delete_password(self, username):
        try:
            import keyring
            keyring.delete_password(self.__base_url, username)
            self.__logger.info(f'Deleted password of "{username}" for {self.__base_url}.')
        except:
            pass

    def download(self, hdl, path, size_for_progress_report = 1000000):
        '''Download the given handle (Document or Version) as a file.

        Parameters
        ----------
        hdl : Handle or str
            DocuShare handle to download as a file or a string that represents a valid DocuShare handle.
        path : path-like object:
            Destination file path.
        size_for_progress_report : int
            This method shows a progress bar using `tqdm <https://tqdm.github.io/>` if the file size is
            more than the specified size in bytes.

        Raises
        ------
        DocuShareNotFoundError
            If the given handle does not exist.
        DocuShareNotAuthorizedError
            If the user is not authorized to access the URL.
        '''

        path = Path(path)
        self.__check_if_logged_in()
        url = self.url(Resource.Get, handle(hdl))
        http_response = self.http_get(url)

        if is_not_found_page(http_response):
            raise DocuShareNotFoundError(self, url)

        # Get the file size.
        if 'Content-Length' in http_response.headers:
            file_size = int(http_response.headers['Content-Length'])
            self.__logger.debug(f'Content-Length is {file_size} for {url}.')
        else:
            self.__logger.debug(f'Content-Length is missing for {url}.')

        self.__logger.info(f'Started downloading: {url} => {path}.')
            
        with open(path, 'wb') as output_file:
            try:
                from tqdm import tqdm
                use_tqdm = True
            except:
                use_tqdm = False
               
            if use_tqdm and file_size >= size_for_progress_report:
                with tqdm(
                        desc = hdl.identifier,
                        total = file_size,
                        unit = 'B',
                        unit_scale = True,
                        unit_divisor = 1000,
                ) as progress_bar:
                    for data in http_response.iter_content(chunk_size = 1000):
                        downloaded_size = output_file.write(data)
                        progress_bar.update(downloaded_size)
            else:
                # If tqdm is not available or the file size is not large,
                # simply download the file silently.
                output_file.write(http_response.content)

        self.__logger.info(f'Completed downloading: {url} => {path}.')

    def __load_properties(self, hdl):
        '''Open and parse the property page of the given handle and return the properties as dict.

        Parameters
        ----------
        hdl : Handle
            DocuShare handle for which the properties will be obtained.

        Returns
        -------
            Property names and values as :py:class:`dict`.

        Notes
        -----
        This method internally uses :py:func:`parse_property_page`. Special properties are added depending on the
        handle type. See :py:func:`parse_property_page` for more details about those special properties.

        Raises
        ------
        DocuShareSystemError
            If the given handle does not exist or the DocuShare site encounters a system error.
        DocuShareNotAuthorizedError
            If the user is not authorized to access the given handle.
        DocuShareParseError
            If this method fails to parse the DocuShare property page.
        '''
        self.__check_if_logged_in()
        hdl = handle(hdl)
        url = self.url(Resource.Services, hdl)
        http_response = self.http_get(url)

        try:
            return parse_property_page(http_response.text, hdl.type)
        except Exception as err:
            raise DocuShareParseError(self, url, err)
    
    def __load_history(self, hdl):
        '''Open and parse the history page of the given Document handle and return the Version handles.

        Parameters
        ----------
        hdl : Handle
            DocuShare handle. Its type must be :py:enum:`HandleType.Document`.

        Returns
        -------
        list : :py:class:`list` of :py:enum:`Handle` instances, each represents a Version handle (e.g. Version-xxxxxx).

        Raises
        ------
        DocuShareSystemError
            If the given handle does not exist or the DocuShare site encounters a system error.
        DocuShareNotAuthorizedError
            If the user is not authorized to access the given handle.
        DocuShareParseError
            If this method fails to parse the DocuShare history page.
        '''
        self.__check_if_logged_in()
        hdl = handle(hdl)
        url = self.url(Resource.History, hdl)
        http_response = self.http_get(url)

        try:
            version_handles = parse_history_page(http_response.text)
        except Exception as err:
            raise DocuShareParseError(self, url, err)
            
        return version_handles

    def __load_collection(self, hdl):
        '''Open and parse the Collection page and return the handles of the objects under the Collection.

        Parameters
        ----------
        hdl : Handle
            DocuShare handle. Its type must be :py:enum:`HandleType.Collection`.

        Returns
        -------
        list : :py:class:`list` of :py:enum:`Handle` instances, each represents a handle of the objects under the specified Collection.

        Raises
        ------
        DocuShareSystemError
            If the given handle does not exist or the DocuShare site encounters a system error.
        DocuShareNotAuthorizedError
            If the user is not authorized to access the given handle.
        DocuShareParseError
            If this method fails to parse the DocuShare collection page.
        '''
        self.__check_if_logged_in()
        hdl = handle(hdl)
        url = self.url(Resource.View, hdl)
        http_response = self.http_get(url)
        
        try:
            object_handles = parse_collection_page(http_response.text)
        except Exception as err:
            raise DocuShareParseError(self, url, err)
            
        return object_handles

    def object(self, hdl):
        '''Get an instance that represents a DocuShare object.

        Parameters
        ----------
        hdl : Handle or str
            DocuShare handle for which you want to get an instance that represents a DocuShare object.
            It can be a string that represents a DocuShare handle like "Document-xxxxx".

        Returns
        -------
        DocuShareBaseObject
            An instance through which you can get individual property values, file, etc.

        Raises
        ------
        DocuShareNotFoundError
            If the given handle does not exist.
        DocuShareNotAuthorizedError
            If the user is not authorized to access the URL.
        DocuShareParseError
            If this method fails to parse one of DocuShare pages related to the given handle.
        '''

        self.__check_if_logged_in()
        
        hdl = handle(hdl)
        if hdl in self.__dsobjects:
            return self.__dsobjects[hdl]

        if hdl.type == HandleType.Collection:
            properties = self.__load_properties(hdl)
            title = properties['Title']

            # Get objects under this collection
            object_handles = self.__load_collection(hdl)

            self.__dsobjects[hdl] = CollectionObject(
                docushare = self,
                hdl = hdl,
                title = title,
                object_handles = object_handles
            )
            return self.__dsobjects[hdl]
        elif hdl.type == HandleType.Document:
            # Get properties
            properties = self.__load_properties(hdl)
            title = properties['Title']
            filename = properties['_filename']
            document_control_number = properties.get('Document Control Number', None)

            # Get history
            version_handles = self.__load_history(hdl)
            
            self.__dsobjects[hdl] = DocumentObject(
                docushare = self,
                hdl = hdl,
                title = title,
                filename = filename,
                document_control_number = document_control_number,
                version_handles = version_handles
            )
            return self.__dsobjects[hdl]
        elif hdl.type == HandleType.Version:
            # Get properties
            properties = self.__load_properties(hdl)
            title = properties['Title']
            filename = properties['_filename']
            version_number = properties['Version Number']
            
            self.__dsobjects[hdl] = VersionObject(
                docushare = self,
                hdl = hdl,
                title = title,
                filename = filename,
                version_number = version_number
            )
            return self.__dsobjects[hdl]
        else:
            assert False, 'code must not reach here'

    def __getitem__(self, hdl):
        return self.object(hdl)

    def close(self):
        '''Close the session with the DocuShare site.

        You need to run :py:meth:`login` again to access any resources on the DocuShare site again.'''
        self.cookies.clear()
        self.__username = None
        self.__session.close()
        self.__session = requests.Session()
