# PyDocuShare

This is the git repository of PyDocuShare, python API to interact with DocuShare.

## Install

Clone this repository, then run the commad below to install PyDocuShare module:

```bash
 $ pip install ".[progress-bar,password-store]"
```

The command above also installs all required python modules.

For better user experience, it is recommended to specify all extra options (`progress-bar` and `password-store`) as shown above. With `progress-bar` option, PyDocuShare shows a progress bar when downloading a large file. With `password-store` option, PyDocuShare can store passwords in a secure manner and reuse the stored passwords for the DocuShare authentication. If you do not need those extra features, you can simply omit all options as shown below:

```bash
 $ pip install .
```

## Unintall

If you want to uninsall PyDocuShare that was installed with `pip`, run the command below:

```bash
 $ pip uninstall pydocushare
```

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

If `password` argument is not specified, PyDocuShare stores the successful password using [keyring](https://keyring.readthedocs.io/) module, and use the stored password in the future login so that you do not have to enter the password many times.

## API Document

To know more about PyDocuShare API, you first need to generate API document using [Sphinx](https://www.sphinx-doc.org/). Install Sphinx and required extensions with the command below:

```bash
 $ pip install -e ".[docs]"
```

Then, run the command below in the root directory of this repository:

```bash
 $ python setup.py build_sphinx
```

This command generates the API documents under `build/docs/html`. Open [build/docs/html/index.html](build/docs/html/index.html) in your Web browser to see the API documents.

The above command sometimes does not work as intended due to remnant from the previous build. In that case, clean the build first:

```bash
 $ python setup.py clean
 $ python setup.py build_sphinx
```

## Restriction

This API has been tested with DocuShare version 7.0.0. The implementation of this API does not use DocuShare HTTP/XML interface. It rather parses the same HTML pages as the users see in their Web browsers. Therefore, it may not work with different versions or if the DocuShare configuration is different from what the author assumes.

## Developer information

The sections below provide information for developer who extend and/or fix PyDocuShare API.

### Documentation

PyDocuShare uses [numpy style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) as the docstring style. Use the same style for consistency.

### Unit Test

PyDocuShare uses [unittest](https://docs.python.org/3/library/unittest.html) unit testing framework. All test cases are stored under [tests/](tests/). Execute the command below to run the unit tests:

```bash
 $ python -m unittest discover tests/ -vvv
```

You may notice that many test cases are skipped. This is because the command above tests only the functionality that does not require connection with a DocuShare site, which probably does not make sense. To test the main functionality of PyDocuShare, you need to provide your DocuShare connection information through environmental variables as follows:

 * **DOCUSHARE_BASEURL** : Base URL of your DocuShare site. For example, https://your.docushare.domain/docushare/ . It must end with a slash '/'.
 * **DOCUSHARE_USERNAME**: Your username of the DocuShare site.
 * **DOCUSHARE_PASSWORD**: [optional] Your password of the DocuShare site. Do not define this environmental variable to use stored password or have the unit test show the password prompt (recommended).
 * **DOCUSHARE_VALID_DOCUMENT_HANDLE**: Valid document handle like Document-12345.
 * **DOCUSHARE_VALID_VERSION_HANDLE** : Valid version handle like Version-111111.
 * **DOCUSHARE_NOT_AUTHORIZED_DOCUMENT_HANDLE**: Document handle like Document-12345 that the user is not authorized to access.
 * **DOCUSHARE_NOT_AUTHORIZED_VERSION_HANDLE**: Version handle like Version-111111 that the user is not authorized to access.

With those environmental variables, run the command above again. Now all test cases should have been executed.

The bash script below is the template to set all required environmental variables Modify each value as appropriate.

```bash
# Base URL of your DocuShare site. It must end with a slash '/'.
export DOCUSHARE_BASEURL=https://your.docushare.domain/docushare/

# Your username of the DocuShare site.
export DOCUSHARE_USERNAME=your_user_name

# Valid document handle.
export DOCUSHARE_VALID_DOCUMENT_HANDLE=Document-12345

# Valid version handle.
export DOCUSHARE_VALID_VERSION_HANDLE=Version-111111

# Document handle like Document-54321 that the user is not authorized to access.
export DOCUSHARE_NOT_AUTHORIZED_DOCUMENT_HANDLE=Document-54321

# Version handle like Version-111111 that the user is not authorized to access.
export DOCUSHARE_NOT_AUTHORIZED_VERSION_HANDLE=Version-99999
```

### Release Procedure

Follow the procedure below to release a new version.

 * Make sure that all your changes have been committed by `git commit -a -m "your_commit_message"`.
 * Run [all unit tests](#unit-test) and confirm that all tests were passed.
 * Generate [API document](#api-document) and make sure that no error/warning is shown during the document generation.
 * Open [setup.py](setup.py) and set the new version number to release.
 * Run `git commit -a -m "Changed version number"` to commit the change in [setup.py](setup.py).
 * Run `git tag -a vx.y.z -m "Version x.y.z"` to mark the new release.
 * Run `git push --tags`. Make sure that you have `--tags` option to upload all tags to the upstream.
 * You may regenerate [API document](#api-document) to see the new version number in the API document.
 
### TODO

Use "TODO" keyword in the inline comments in the source code and documentation to indicate things to be fixed in the future versions. The list below shows the major TODOs that are not suitable as inline comments:

 * Upload the generated document to a static Web site (e.g. [readthetodcs](https://readthedocs.org/) or [GitHub Pages](https://pages.github.com/) so that anyone can access the documents without generating the documents locally.
 * Add unit tests for Collection handles and CollectionObject.
