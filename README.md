# PyDocuShare

This is the git repository of PyDocuShare, python API to interact with DocuShare.

## Install

Clone this repository, then run the commad below to install PyDocuShare module.

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
 $ pip intall sphinx sphinx-rtd-theme sphinx-prompt sphinx-automodapi enum-tools[sphinx]
```

Then, run the command below in the root directory of this repository:

```sh
 $ python setup.py build_sphinx
```

The API documents are generated under `build/docs/html`. Open [build/docs/html/index.html](build/docs/html/index.html) in your Web browser to see the API documents.

## Restriction

This API has been tested with DocuShare version 7.0.0. The implementation of this API does not use DocuShare HTTP/XML interface. It rather parses the same HTML pages as the users see in their Web browsers. Therefore, it may not work with different versions or if the DocuShare configuration is different from what the author assumed.

## Developer information

The sections below provide information for developer who extend and/or fix PyDocuShare API.

### Documentation

PyDocuShare uses [numpy style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) as the docstring style. Use the same style for consistency.

### Unit Test

PyDocuShare uses [unittest](https://docs.python.org/3/library/unittest.html) unit testing framework. All test cases are stored under [tests/](tests/). Run

```sh
 $ python -m unittest discover tests
```

to test all cases.
