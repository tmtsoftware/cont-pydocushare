import getpass
import json
import re
import requests
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

class DocuShare:
    USE_STORED_PASSWORD = object()
    
    def __init__(self, base_url, js_interpreter = '/usr/bin/node'):
        # Check if the given URL is valid.
        parse_result = urlparse(base_url)
        if parse_result.scheme != 'http' and parse_result.scheme != 'https':
            raise ValueError(f'base_url was {base_url}, but it must start with "http://" or "https://"')

        if not parse_result.netloc:
            raise ValueError(f'"{base_url}" is an invalid URL. It must be in the form of https://www.example.org/.')

        self.__base_url = base_url
        self.__dsweb_url = urljoin(self.__base_url, '/docushare/dsweb/')
        self.__login_url = urljoin(self.__dsweb_url, 'Login')
        self.__apply_login_url = urljoin(self.__dsweb_url, 'ApplyLogin')
        self.__services_url = urljoin(self.__dsweb_url, 'Services/')
        self.__serviceslib_url = urljoin(self.__dsweb_url, 'ServicesLib/')
        self.__get_url = urljoin(self.__dsweb_url, 'Get/')
        self.__session = None
        self.__js_interpreter = js_interpreter

    @staticmethod
    def __validate_handle(handle, types = ['Version', 'Document', 'Collection']):
        if not isinstance(handle, str):
            raise TypeError('handle must be str')

        if 'Version' in types and re.match(r'^Version-([0-9]{6})$', handle):
            return True

        if 'Document' in types and re.match(r'^Document-([0-9]{5})$', handle):
            return True

        if 'Collection' in types and re.match(r'^Collection-([0-9]{5})$', handle):
            return True

        return False
        
    def _services_url(self, handle):
        self.__validate_handle(handle, types = ['Version', 'Document', 'Collection'])
        return urljoin(self.__services_url, handle)

    def _history_url(self, handle):
        self.__validate_handle(handle, types = ['Document'])
        url = urljoin(self.__serviceslib_url, handle + '/')
        return urljoin(url, 'History')

    def _get_url(self, handle):
        self.__validate_handle(handle, types = ['Version', 'Document'])
        return urljoin(self.__get_url, handle)

    def _download(self, handle, path):
        self.__check_if_logged_in()
        url = self._get_url(handle)
        r = self.__session.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)

        return path
    
    def login(self, username = None, password = None, js_interpreter = '/usr/bin/node', retry_count = 3):
        can_prompt = (username is None) or (password is None) or (password == self.USE_STORED_PASSWORD)
        store_password = (password == self.USE_STORED_PASSWORD)
        
        if username is None:
            print(f'\nEnter your username for {self.__base_url}')
            username = input('Username: ')
            password = None

        if store_password:
            password = self.__get_password(self.__base_url, username)
            
        if password is None:
            print(f'\nEnter password of "{username}" for {self.__base_url}')
            password = getpass.getpass('Password: ')

        self.__session = requests.Session()

        login_token, challenge_js_url = self.__parse_login_page(self.__login_url, self.__session)
        challenge_js = self.__session.get(challenge_js_url).text
        challenge_response = self.__challenge_response(
            password = password,
            login_token = login_token,
            challenge_js = challenge_js,
            js_interpreter = self.__js_interpreter
        )
        login_info = {
            'response': challenge_response,
            'login_token': login_token,
            'bookmark': '',
            'username': username,
            'password': '',
            'domain': 'DocuShare',
            'Login': 'Login'
        }

        self.__session.post(self.__apply_login_url, data = login_info)
        if 'AmberUser' not in self.__session.cookies.keys():
            if retry_count <= 1:
                raise Exception(f'Failed to login at {self.__login_url}')
            if store_password:
                # Delete unmatched password from the keyring, and ask the
                # username and password again.
                print(f'\nFailed to login at {self.__login_url}')
                self.__delete_password(self.__base_url, username)
                self.login( username = None,
                            password = self.USE_STORED_PASSWORD,
                            js_interpreter = js_interpreter,
                            retry_count = retry_count - 1 )
            elif can_prompt:
                print(f'\nFailed to login at {self.__login_url}')
                self.login( username = None,
                            password = None,
                            js_interpreter = js_interpreter,
                            retry_count = retry_count - 1 )
            else:
                raise Exception(f'Failed to login at {self.__login_url}')

        if store_password:
            self.__set_password(self.__base_url, username, password)

    @property
    def is_logged_in(self):
        return self.__session is not None and 'AmberUser' in self.__session.cookies.keys()

    def __check_if_logged_in(self):
        if not self.is_logged_in:
            raise Exception('Not logged in yet. Login first.')

    @staticmethod
    def __parse_login_page(login_url, session):
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

    @staticmethod
    def __get_password(base_url, username):
        try:
            import keyring
            return keyring.get_password(base_url, username)
        except:
            return None

    @staticmethod
    def __set_password(base_url, username, password):
        try:
            import keyring
            return keyring.set_password(base_url, username, password)
        except:
            pass
        
    @staticmethod
    def __delete_password(base_url, username):
        try:
            import keyring
            keyring.delete_password(base_url, username)
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

