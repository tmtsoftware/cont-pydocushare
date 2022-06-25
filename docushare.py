from enum import Enum, auto
import getpass
import json
import re
import requests
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

def join_url(*args):
    ret = None
    for arg in args:
        if ret is None:
            ret = arg
        else:
            ret = urljoin(ret, arg)
    return ret

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

def handle(handle_str):
    '''
    This method converts handle string (e.g., Collection-10101, Document-20202, Version-123456)
    to an instance of Handle.
    '''
    if isinstance(handle_str, Handle):
        return handle_str
    
    return Handle.from_str(handle_str)
    
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

        self.__session.cookies.clear()
        
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
        challenge_js = self.__session.get(challenge_js_url).text

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
        self.__session.post(self.url(Resource.ApplyLogin), data = login_info)

        # If the authentication is successful, 'AmberUser' is added to the
        # cookies.
        if 'AmberUser' not in self.__session.cookies.keys():
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
            
    def download(self, hdl, path):
        '''Download the given handle (Document or Version) as a file.

        Parameters:
        hdl (Handle): Handle to download.
        path (path-like object): Destination file.
        '''
        
        self.__check_if_logged_in()
        url = self.url(Resource.Get, handle(hdl))
        r = self.__session.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)

    @property
    def is_logged_in(self):
        return 'AmberUser' in self.__session.cookies.keys()

    def __check_if_logged_in(self):
        if not self.is_logged_in:
            raise Exception('Not logged in yet. Login first.')

    def __open_and_parse_login_page(self):
        login_url = self.url(Resource.Login)
        session   = self.__session
    
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.content, 'html.parser')
        
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

    def get_document(self, handle_number):
        self.__check_if_logged_in()

        if isinstance(handle_number, int):
            handle_number = f'{handle_number:05d}'
        elif isinstance(handle_number, str):
            m = re.match(r'^Document-([0-9]{5})$', handle_number)
            if m:
                handle_number = m.group(1)
            elif re.match(r'^[0-9]{5}$', handle_number):
                pass
            else:
                raise ValueException('"handle_number" must be a 5-digit number or Document-xxxxxx')
        else:
            raise TypeError('"handle_number" must be int or str.')

        handle = f'Document-{handle_number}'
        document_property_url = self._services_url(handle)
        title, filename, document_control_number = self.__parse_document_property_page(document_property_url, self.__session)

        document_history_url = self._history_url(handle)
        versions = self.__parse_document_history_page(document_history_url, self.__session)

        return self.Document(docushare = self,
                             handle_number = handle_number,
                             title = title,
                             filename = filename,
                             document_control_number = document_control_number,
                             versions = versions)

    @staticmethod
    def __parse_document_property_page(document_property_url, session):
        document_property_page = session.get(document_property_url)
        soup = BeautifulSoup(document_property_page.content, 'html.parser')

        title = None
        filename = None
        document_control_number = None

        propstable = soup.find('table', {'class': 'propstable'})
        for row in propstable.find_all('tr'):
            cols = row.find_all('td')
            field_name = cols[0].text.strip()
           
            if 'Title' in field_name:
                title = cols[1].text.strip()
                file_url = cols[1].find('a')['href']
                filename = PurePosixPath(urlparse(file_url).path).name
            elif 'Document Control Number' in field_name:
                document_control_number = cols[1].text.strip()

        return title, filename, document_control_number

    @staticmethod
    def __parse_document_history_page(document_history_url, session):
        document_history_page = session.get(document_history_url)
        soup = BeautifulSoup(document_history_page.content, 'html.parser')

        propstable = soup.find('table', {'class': 'table_properties'})

        version_number_column = None
        version_column = None
        
        column_headers = propstable.find('thead').find_all('th')
        for i in range(len(column_headers)):
            column_name = column_headers[i].text.strip()
            if '#' in column_name:
                version_number_column = i
            elif 'Version' in column_name:
                version_column = i

        if version_number_column is None:
            raise Exception(f'Cannot find "#" column in {document_history_url}.')
        if version_column is None:
            raise Exception(f'Cannot find "Version" column in {document_history_url}.')

        versions = []
        for row in propstable.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > max(version_number_column, version_column):
                version_number = cells[version_number_column].text.strip()
                if re.match(r'^[0-9]+$', version_number):
                    file_url = cells[version_number_column].find('a')['href']
                    handle_number = re.search(r'Version-([0-9]{6})', file_url).group(1)
                    filename = PurePosixPath(urlparse(file_url).path).name
                    title = cells[version_column].find('a').text

                    versions.append( DocuShare.Version( document = None,
                                                        handle_number = handle_number,
                                                        title = title,
                                                        filename = filename,
                                                        version_number = version_number ) )

        return versions
                    
    class Version:
        def __init__(self, document, handle_number, title, filename, version_number):
            self.__document       = document
            self.__handle_number  = handle_number
            self.__title          = title
            self.__filename       = filename
            self.__version_number = version_number

        @property
        def document(self):
            return self.__document

        def set_document(self, document):
            self.__document = document

        @property
        def handle_number(self):
            return self.__handle_number

        @property
        def handle(self):
            return f'Version-{self.__handle_number}'

        @property
        def title(self):
            return self.__title

        @property
        def filename(self):
            return self.__filename

        @property
        def version_number(self):
            return self.__version_number

        @property
        def download_url(self):
            return self.__document.docushare._get_url(self.handle)

        def __str__(self):
            return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}", version_number: {self.version_number}'

        def download(self, path = None):
            if path is None:
                path = Path.cwd()
            else:
                path = Path(path)

            if path.is_dir():
                path = path.joinpath(self.__filename)

            return self.__document.docushare._download(self.handle, path)

    class Document:
        def __init__(self, docushare, handle_number, title, filename, document_control_number, versions):
            self.__docushare        = docushare
            self.__handle_number    = handle_number
            self.__title            = title
            self.__filename         = filename
            self.__document_control_number = document_control_number
            self.__versions         = versions

            for version in self.__versions:
                version.set_document(self)

        @property
        def docushare(self):
            return self.__docushare

        @property
        def handle_number(self):
            return self.__handle_number

        @property
        def handle(self):
            return f'Document-{self.__handle_number}'

        @property
        def title(self):
            return self.__title

        @property
        def filename(self):
            return self.__filename

        @property
        def document_control_number(self):
            return self.__document_control_number

        @property
        def versions(self):
            return self.__versions
      
        @property
        def download_url(self):
            return self.__docushare._get_url(self.handle)

        def __str__(self):
            return f'handle: "{self.handle}", title: "{self.title}", filename: "{self.filename}", document_control_number: "{self.document_control_number}"'

        def download(self, path = None):
            if path is None:
                path = Path.cwd()
            else:
                path = Path(path)

            if path.is_dir():
                path = path.joinpath(self.__filename)

            return self.__docushare._download(self.handle, path)
       
def main():
    docushare_url = input('Enter DocuShare URL: ')
    ds = DocuShare(docushare_url)
    ds.login(username='tnakamoto', password=DocuShare.USE_STORED_PASSWORD)

    document = ds.get_document('Document-94736')
    print(document)
    print(document.handle)
    print(document.download_url)

    for version in document.versions:
        print(version)
        version.download()


if __name__ == "__main__":
    main()

