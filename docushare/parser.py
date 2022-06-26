import re
from pathlib import PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .handle import handle, HandleType
from .util import join_url

class ParseError(RuntimeError):
    '''Raised when parsing one of DocuShare web page.'''
    pass

def parse_login_page(html_text):
    '''Parse the DocuShare login page and returns login token and path to challenge.js.

    Parameters
    ----------
    html_text : str
        HTML text that was obtained from a DocuShare login page like
        https://your.docushare.domain/docushare/dsweb/Login.

    Returns
    -------
    login_token : str
        Login token given by the DocuShare server like '1cwe4irxdwe7yl4v6ggow'.
    challenge_js_str : str
        Relative path of challenge.js.

    Raises
    ------
    ParseError
        If the given page cannot be parsed correctly.
    '''
    soup = BeautifulSoup(html_text, 'html.parser')
        
    login_token_element = soup.find('input', {'name': 'login_token'})
    if not login_token_element:
        raise ParseError(f'Cannot find login_token.')

    if not login_token_element.has_attr('value'):
        raise ParseError(f'"value" attribute is missing in {login_token_element}.')
        
    login_token = login_token_element['value']
    if not login_token:
        raise ParseError(f'login_token is empty.')
        
    challenge_js_script_tag = soup.find('script', src=re.compile('challenge\.js'))
    if (not challenge_js_script_tag) or (not challenge_js_script_tag.has_attr('src')):
        raise ParseError(f'Cannot find URL of challenge.js.')

    challenge_js_src = challenge_js_script_tag['src']

    return login_token, challenge_js_src

def parse_property_page(html_text, handle_type):
    '''Parse a DocuShare property page and returns the properties.

    Parameters
    ----------
    html_text : str
        HTML text that was obtained from a DocuShare property page like
        https://your.docushare.domain/docushare/dsweb/Services/Collection-xxxxx,
        https://your.docushare.domain/docushare/dsweb/Services/Document-xxxxx or
        https://your.docushare.domain/docushare/dsweb/Services/Version-xxxxxx.
 
    handle_type : HandleType
        Specify a handle type. If it is :attr:`HandleType.Document` or :attr:`HandleType.Version`,
        '_filename' property is added to indicate the file name of the document.

    Returns
    -------
    dict: property name as key and property value as value.

    Raises
    ------
    ParseError
        If the given page cannot be parsed correctly.
    '''

    try:
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
    except Exception as err:
        raise ParseError('Failed to parse a DocuShare property page.', err)


def parse_history_page(html_text):
    '''Parse a DocuShare history page and returns the version handles.

    Parameters
    ----------
    html_text : str
        HTML text that was obtained from a DocuShare history page like
        https://your.docushare.domain/docushare/dsweb/ServicesLib/Document-xxxxx/History

    Returns
    -------
    array: array of :class:`Handle` instances.

    Raises
    ------
    ParseError
        If the given page cannot be parsed correctly.
    '''

    try:
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
    except Exception as err:
        raise ParseError('Failed to parse a DocuShare history page.', err)


