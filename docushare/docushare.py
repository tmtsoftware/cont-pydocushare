from enum import Enum, auto
import getpass
import json
import re
import requests
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .handle import HandleType, Handle, handle
from .parser import parse_login_page, parse_property_page, parse_history_page
from .util import join_url

class Resource(Enum):
    '''This enum represents one DocuShare resource.'''
    
    DSWEB      = '(base URL for any resources in DocuShare)'
    Login      = 'HTTP GET : login page to get login token'
    ApplyLogin = 'HTTP POST: to send credential information'
    Services   = 'HTTP GET : property page'
    History    = 'HTTP GET : version history of a document'
    Get        = 'HTTP GET : get a document file'

class PasswordOption(Enum):
    '''Option for password prompting.'''
    
    ASK        = 'Always prompts the user to enter the password in the console.'
    USE_STORED = 'Try to use the stored password if exists. If not, prompts the user to enter the password in the console. Correctly authenticated password will be stored. Note that `keyring` module is required to use this option.'

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
        
        self.__base_url = base_url
        self.__session  = requests.Session()
        self.__handle_properties = {}

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
        '''
        print(f'HTTP GET : {url}') # TODO: use a logging mechanism
        return self.__session.get(url)

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
        '''
        print(f'HTTP POST: {url}') # TODO: use a logging mechanism
        return self.__session.post(url, data = data)

    @property
    def cookies(self):
        return self.__session.cookies

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
        else:
            assert False, 'code must not reach here'
   
    def login(
            self,
            username = None,
            password = PasswordOption.USE_STORED,
            js_interpreter = '/usr/bin/node',
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
        
        js_interpreter : str
            Path to JavaScript interpreter.
            This will be used to run DocuShare's for challenge-response authentication.

        retry_count : int
            The user will have a chance to enter the credentials this amount of time.

        domain : str
            Domain to specify when logging in DocuShare. Typically, it is 'DocuShare'.
        '''

        if not (username is None or isinstance(username, str)):
            raise TypeError('username must be None or str')
        
        if not isinstance(password, (str, PasswordOption)):
            raise TypeError('password must be str or one of PasswordOption enum')

        if not isinstance(js_interpreter, str) or not js_interpreter:
            raise TypeError('js_interpreter must be a non-empty string')

        if not isinstance(retry_count, int) or retry_count < 1:
            raise TypeError('retry_count must be a positive integer')

        if not isinstance(domain, str):
            raise TypeError('domain must be str')

        self.cookies.clear()
        
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
        challenge_response = self.__challenge_response(
            password = entered_password,
            login_token = login_token,
            challenge_js = challenge_js,
            js_interpreter = js_interpreter
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
        self.http_post(self.url(Resource.ApplyLogin), data = login_info)

        # If the authentication is successful, 'AmberUser' is added to the
        # cookies.
        if 'AmberUser' not in self.cookies.keys():
            if retry_count <= 1:
                raise Exception(f'Failed to login at {login_url}')
            elif password == PasswordOption.USE_STORED:
                # Delete unmatched password from the keyring, and ask the
                # password again.
                print(f'\nFailed to login at {login_url}')
                self.__delete_password(entered_username)
                self.login(username = username,
                           password = PasswordOption.USE_STORED,
                           js_interpreter = js_interpreter,
                           retry_count = retry_count - 1,
                           domain = domain)
            elif password == PasswordOption.ASK:
                print(f'\nFailed to login at {login_url}')
                self.login(username = username,
                           password = PasswordOption.ASK,
                           js_interpreter = js_interpreter,
                           retry_count = retry_count - 1,
                           domain = domain )
            else:
                raise Exception(f'Failed to login at {login_url}')

        if password == PasswordOption.USE_STORED:
            self.__set_password(entered_username, entered_password)
            
    @property
    def is_logged_in(self):
        return 'AmberUser' in self.cookies.keys()

    def __check_if_logged_in(self):
        if not self.is_logged_in:
            raise Exception('Not logged in yet. Login first.')

    def __open_and_parse_login_page(self):
        login_url = self.url(Resource.Login)
        login_page = self.http_get(login_url)
        login_token, challenge_js_src = parse_login_page(login_page.text)
        return login_token, join_url(login_url, challenge_js_src)

    @staticmethod
    def __challenge_response(password, login_token, challenge_js, js_interpreter):
        password_escaped = json.dumps(password)
        login_token_escaped = json.dumps(login_token)
        challenge_js += f'\nconsole.log(obscure_string({password_escaped}, {login_token_escaped}))'
        response_bytes = subprocess.check_output(js_interpreter, input=challenge_js.encode())
        return response_bytes.decode().strip()

    def __get_password(self, username):
        try:
            import keyring
            return keyring.get_password(self.__base_url, username)
        except:
            return None

    def __set_password(self, username, password):
        try:
            import keyring
            return keyring.set_password(self.__base_url, username, password)
        except:
            pass
        
    def __delete_password(self, username):
        try:
            import keyring
            keyring.delete_password(self.__base_url, username)
        except:
            pass

    def download(self, hdl, path):
        '''Download the given handle (Document or Version) as a file.

        Parameters:
        hdl (Handle): Handle to download.
        path (path-like object): Destination file.
        '''
        
        self.__check_if_logged_in()
        url = self.url(Resource.Get, handle(hdl))
        http_response = self.http_get(url)
        http_response.raise_for_status()

        if self.__is_not_found_page(http_response):
            raise Exception(f'{url} was not found.')
        
        with open(path, 'wb') as f:
            f.write(http_response.content)

    def load_properties(self, hdl):
        '''Open and parse the property page of the given handle and return the properties as dict.

        Parameters:
        hdl (Handle): handle

        Returns:
        Property values as dict.
        '''
        self.__check_if_logged_in()
        hdl = handle(hdl)
        url = self.url(Resource.Services, hdl)
        http_response = self.http_get(url)
        http_response.raise_for_status()
        return parse_property_page(http_response.text, hdl.type)

    def load_history(self, hdl):
        '''Open and parse the history page of the given Document handle and return the Version handles.

        Parameters:
        hdl (Handle): Document handle. Its type must be HandleType.Document.

        Returns:
        An array of Version handles (e.g. Version-xxxxxx).
        '''
        self.__check_if_logged_in()
        hdl = handle(hdl)
        url = self.url(Resource.History, hdl)
        http_response = self.http_get(url)
        http_response.raise_for_status()
        version_handles = parse_history_page(http_response.text)
        return version_handles

    @staticmethod
    def __is_not_found_page(http_response):
        if not ('Content-Type' in http_response.headers and
                http_response.headers['Content-Type'].startswith('text/html')):
            return False

        soup = BeautifulSoup(http_response.text, 'html.parser')
        for h2s in soup.find_all('h2'):
            if 'Not Found' in h2s.text.strip():
                return True
        return False

    def __getitem__(self, hdl):
        self.__check_if_logged_in()
        
        hdl = handle(hdl)
        if hdl in self.__handle_properties:
            return self.__handle_properties[hdl]

        if hdl.type == HandleType.Collection:
            raise NotImplementedError()
        elif hdl.type == HandleType.Document:
            self.__handle_properties[hdl] = DocumentProperty(self, hdl)
            return self.__handle_properties[hdl]
        elif hdl.type == HandleType.Version:
            self.__handle_properties[hdl] = VersionProperty(self, hdl)
            return self.__handle_properties[hdl]
        else:
            assert False, 'code must not reach here'

class DocumentProperty:
    def __init__(self, docushare, hdl):
        if not isinstance(docushare, DocuShare):
            raise TypeError('docushare must be an instance of DocuShare')
        if not isinstance(hdl, Handle):
            raise TypeError('hdl must be an instance of Handle')
        if hdl.type != HandleType.Document:
            raise ValueError('handle type must be Document')
        
        self.__docushare = docushare
        self.__hdl       = hdl
        self.__title     = None
        self.__filename  = None
        self.__document_control_number = None
        self.__versions  = None
        
    def __load_properties(self):
        properties = self.docushare.load_properties(self.handle)
        self.__title = properties.get('Title', '')
        self.__filename = properties.get('_filename', '')
        self.__document_control_number = properties.get('Document Control Number', '')

    @property
    def docushare(self):
        return self.__docushare

    @property
    def handle(self):
        return self.__hdl

    @property
    def title(self):
        if self.__title is None:
            self.__load_properties()
        return self.__title

    @property
    def filename(self):
        if self.__filename is None:
            self.__load_properties()
        return self.__filename

    @property
    def document_control_number(self):
        if self.__document_control_number is None:
            self.__load_properties()
        return self.__document_control_number

    def __str__(self):
        return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}", document_control_number: "{self.document_control_number}"'

    @property
    def versions(self):
        if self.__versions is None:
            self.__versions = self.docushare.load_history(self.handle)
        return self.__versions

    @property
    def download_url(self):
        return self.docushare.url(Resource.Get, self.handle)

    def download(self, path = None):
        if path is None:
            path = Path.cwd()
        else:
            path = Path(path)
            
        if path.is_dir():
            path = path.joinpath(self.filename)
            
        self.docushare.download(self.handle, path)
        return path

class VersionProperty:
    def __init__(self, docushare, hdl):
        if not isinstance(docushare, DocuShare):
            raise TypeError('docushare must be an instance of DocuShare')
        if not isinstance(hdl, Handle):
            raise TypeError('hdl must be an instance of Handle')
        if hdl.type != HandleType.Version:
            raise ValueError('handle type must be Version')
        
        self.__docushare = docushare
        self.__hdl       = hdl
        self.__title     = None
        self.__filename  = None
        self.__version_number = None

    def __load_properties(self):
        properties = self.docushare.load_properties(self.handle)
        self.__title = properties.get('Title', '')
        self.__filename = properties.get('_filename', '')
        self.__version_number = properties.get('Version Number', '')

    @property
    def docushare(self):
        return self.__docushare

    @property
    def handle(self):
        return self.__hdl

    @property
    def title(self):
        if self.__title is None:
            self.__load_properties()
        return self.__title

    @property
    def filename(self):
        if self.__filename is None:
            self.__load_properties()
        return self.__filename

    @property
    def version_number(self):
        if self.__version_number is None:
            self.__load_properties()
        return self.__version_number

    def __str__(self):
        return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}", version_number: {self.version_number}'

    @property
    def download_url(self):
        return self.docushare.url(Resource.Get, self.handle)

    def download(self, path = None):
        if path is None:
            path = Path.cwd()
        else:
            path = Path(path)
            
        if path.is_dir():
            path = path.joinpath(self.filename)
            
        self.docushare.download(self.handle, path)
        return path
    
def main():
    docushare_url = input('Enter DocuShare URL: ')
    ds = DocuShare(docushare_url)
    ds.login(username='tnakamoto', password=PasswordOption.USE_STORED)

    doc = ds['Document-94736']
    print(doc)
    for version_handle in doc.versions:
        print(ds[version_handle])

if __name__ == "__main__":
    main()

