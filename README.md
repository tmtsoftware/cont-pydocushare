# PyDocuShare

This is the git repository of PyDocuShare, python API to interact with DocuShare.

## Install

Clone this repository, then run the commad below to install PyDocuShare module:

```sh
 $ pip install -e ".[password-store]"
```

For better user experience (storing password), it is recommended to specify all extra options as shown above. If you do not need those extra features, you can simply omit all options as shown below:

```sh
 $ pip install -e .
```

## Pre-requisite

PyDocuShare uses Node.js as JavaScript interpreter, which is required for the DocuShare authentication. By default, `/usr/bin/node` is assumed as the interpreter path. You can explicitly specify the interpreter path as an argument of [login()](#login).

## Quick Usage

Run the python code below. Replace `base_url` and the document number `Document-00000` with appropriate values.

```python
from docushare import *
ds = DocuShare(base_url='https://your.domain/docushare/')
ds.login()

doc = ds['Document-00000']
print(f'Download "{doc.title}" as "{doc.filename}".')
doc.download()
```

It should finally download the document in the current directory. See [API document](#api-document) for more detailed usage of the API.

### login()

The login() method asks username and password to login DocuShare if no argument is given. You may speicfy username or both as the argument(s):

```python
ds.login(username='your_user_name')
```

or 

```python
ds.login(username='your_user_name', password='your_password')
```

The login() method uses Node.js as JavaScript interpreter, which is required for authentication. By default, `/usr/bin/node` is assumed as the interpreter path. You can explicitly specify the path as an `js_interpreter` argument:

```python
ds.login(js_interpreter='/path/to/node')
```

## API Document

API documents can be generated using Sphinx. Install Sphinx and relevant extensions with the command below:

```sh
 $ pip install -e ".[docs]"
```

Then, run the command below in the root directory of this repository:

```sh
 $ python setup.py build_sphinx
```

The API documents are generated under `build/docs/html`. Open [build/docs/html/index.html](build/docs/html/index.html) in your Web browser to see the API documents.

Sometimes document generation does not work as intended due to remnant from the previous build. In that case, clean the build first:

```sh
 $ python setup.py clean
 $ python setup.py build_sphinx
```

## Restriction

This API has been tested with DocuShare version 7.0.0. The implementation of this API does not use DocuShare HTTP/XML interface. It rather parses the same HTML pages as the users see in their Web browsers. Therefore, it may not work with different versions or if the DocuShare configuration is different from what the author assumed.

## Developer information

The sections below provide information for developer who extend and/or fix PyDocuShare API.

### Documentation

PyDocuShare uses [numpy style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) as the docstring style. Use the same style for consistency.

### Unit Test

PyDocuShare uses [unittest](https://docs.python.org/3/library/unittest.html) unit testing framework. All test cases are stored under [tests/](tests/). Run

```sh
 $ python -m unittest discover tests/ -vvv
```

to test some cases. You may notice that many test cases are skipped. This is because the command above tests only the functionality that does not require connection with a DocuShare site, which probably does not make sense. To test the main functionality of PyDocuShare, you need to provide your DocuShare connection information through environmental variables:

 * **DOCUSHARE_BASEURL** : Base URL of your DocuShare site. For example, https://your.docushare.domain/docushare/ . It must end with a slash '/'.
 * **DOCUSHARE_USERNAME**: Your username of the DocuShare site.
 * **DOCUSHARE_VALID_DOCUMENT_HANDLE**: Valid document handle like Document-12345.
 * **DOCUSHARE_VALID_VERSION_HANDLE** : Valid version handle like Version-111111.
 * **DOCUSHARE_NOT_AUTHORIZED_DOCUMENT_HANDLE**: Document handle like Document-12345 that the user is not authorized to access.
 * **DOCUSHARE_NOT_AUTHORIZED_VERSION_HANDLE**: Version handle like Version-111111 that the user is not authorized to access.
 * **DOCUSHARE_PASSWORD**: [optional] Your password of the DocuShare site. Do not define this environmental variable to use stored password or have the unit test show the password prompt (recommended).
 * **DOCUSHARE_

With those environmental variables, run the command above again. Now all cases should have been tested.
