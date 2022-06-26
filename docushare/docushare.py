from enum import Enum, auto
import getpass
import json
import re
import requests
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .handle import HandleType, Handle, handle

def join_url(*args):
    ret = None
    for arg in args:
        if ret is None:
            ret = arg
        else:
            ret = urljoin(ret, arg)
    return ret

class Resource(Enum):
    DSWEB      = auto()
    Login      = auto()
    ApplyLogin = auto()
    Services   = auto()
    History    = auto()
    Get        = auto()

class PasswordOption(Enum):
    ASK        = auto()
    USE_STORED = auto()

class DocuShare:
    '''This class represents one DocuShare site.'''
    
    USE_STORED_PASSWORD = object()
    
    def __init__(self, base_url):
        '''Constructor

        Parameters:
        base_url (str): Base URL of DocuShare. For example, https://www.example.com/docushare/.
        '''
        
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
        print(f' GET: {url}')
        return self.__session.get(url)

    def http_post(self, url, data):
        print(f'POST: {url}')
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
            return urljoin(self.__base_url, 'dsweb/')
        elif resource == Resource.Login:
            return urljoin(self.url(Resource.DSWEB), 'Login')
        elif resource == Resource.ApplyLogin:
            return urljoin(self.url(Resource.DSWEB), 'ApplyLogin')
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
        '''Login DocuShare.

        Parameters:
        username (str): Username for DocuShare. Specify None to prompt the user to enter the username.

        password (str or PasswordOption): Password for the DocuShare user.
            If a string is given, it is considered as the password and this method never prompts the user.

            If PasswordOption.ASK, this method always prompts the user to enter the password.

            If PassowrdOption.USE_STORED, this method first tries to use the stored password. If the password
            is not stored or the stored password is not correct, this method prompts the user to enter the 
            password. If the password is correct, it will be stored in the keyring so that the user does not
            have to enter the same password again next time this method is called.
            Note that storing password requires 'keyring' module.
        

        js_interpreter (str): Path to JavaScript interpreter. This will be used to run DocuShare's
                              for challenge-response authentication.

        retry_count (int): The user will have a chance to enter the credentials this amount of time.

        domain (str): Domain to specify when logging in DocuShare. Typically, it is 'DocuShare'.
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
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        login_token_element = soup.find('input', {'name': 'login_token'})
        if not login_token_element:
            raise Exception(f'Cannot find login_token in {login_url}.')

        if not login_token_element.has_attr('value'):
            raise Exception(f'"value" attribute is missing in {login_token_element} ({login_url}).')
        
        login_token = login_token_element['value']
        if not login_token:
            raise Exception(f'login_token is empty in {login_url}.')
        
        challenge_js_script_tag = soup.find('script', src=re.compile('challenge\.js'))
        if not challenge_js_script_tag:
            raise Exception(f'Cannot find URL to challenge.js in {login_url}')
        
        challenge_js_src = challenge_js_script_tag['src']
        challenge_js_url = urljoin(login_url, challenge_js_src)

        return login_token, challenge_js_url

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
        return self.__parse_property_page(http_response.text, hdl.type)

    @staticmethod
    def __parse_property_page(html_text, handle_type):
        properties = {}
        
        soup = BeautifulSoup(html_text, 'html.parser')
        propstable = soup.find('table', {'class': 'propstable'})
        for row in propstable.find_all('tr'):
            cols = row.find_all('td')
            field_name = cols[0].text.strip()
            if field_name.endswith(':'):
                field_name = field_name[:-1]

            field_value = cols[1].text.strip()

            if field_name == 'Handle':
                properties[field_name] = handle(field_value)
            elif field_name == 'Version Number':
                properties[field_name] = int(field_value)
            else:
                # TODO: parse user name, date and size
                properties[field_name] = field_value

            if (handle_type == HandleType.Document or handle_type == HandleType.Version) and \
               field_name == 'Title':
                file_url = cols[1].find('a')['href']
                filename = PurePosixPath(urlparse(file_url).path).name
                properties['_filename'] = filename
            
        return properties

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
        version_handles = self.__parse_history_page(http_response.text)
        return version_handles

    @staticmethod
    def __parse_history_page(html_text):
        soup = BeautifulSoup(html_text, 'html.parser')
        propstable = soup.find('table', {'class': 'table_properties'})

        header_columns = propstable.find('thead').find_all('th')
        field_names = {}
        for column_index in range(len(header_columns)):
            field_name = header_columns[column_index].text.strip()
            if field_name:
                field_names[column_index] = field_name

        version_handles = []
        for row in propstable.find_all('tr'):
            cells = row.find_all('td')

            for column_index in field_names.keys():
                field_name = field_names[column_index]

                if len(cells) > column_index:
                    if field_name == 'Preferred':
                        # TODO: parse the radio button and find the preferred version
                        pass
                    elif field_name == '#':
                        a_tag = cells[column_index].find('a')
                        if a_tag:
                            file_url = a_tag['href']
                            handle_str = re.search(r'\/(Version-[0-9]{6})\/', file_url).group(1)
                            version_handles.append(handle(handle_str))
                    else:
                        # Ignore other information
                        pass

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

