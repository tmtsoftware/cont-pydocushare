# PyDocuShare

This is the git repository of PyDocuShare, python API to interact with DocuShare.

The user documentation is available at https://tmtsoftware.github.io/pydocushare/ .

This README.md is the documentation for developers who extend, fix and/or release PyDocuShare API.

## License

PyDocuShare uses [pyduktape](https://github.com/stefano/pyduktape) as the underlying JavaScript interpreter to perform DocuShare challenge-response authentication. Because it is distributed under the terms of GNU General Public License version 2, PyDocuShare is distributed under the same license. See [LICENSE](LICENSE) for more details.

## Inline Documentation

PyDocuShare uses [numpy style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) to document the module, classes, functions, methods and attributes. Use the same style for consistency.

## Documentation

PyDocuShare uses [Sphinx](https://www.sphinx-doc.org/) to generate the user documentation and API reference. They are published at https://tmtsoftware.github.io/pydocushare/ through [GitHug Pages](https://pages.github.com/).

The source files of user documentation can be found under [docs/](docs/). If you want to generate the user documentation and API reference locally to see how your updates appear in the documentation, you need to first install Sphinx. Run the command below to install required tools including Sphinx:

```bash
 $ pip install -e ".[docs]"
```

Then, run the command below in the root directory of this repository:

```bash
 $ python setup.py build_sphinx
```

The command above generates the user documentation and API documents under [docs/html](docs/html/). Open [docs/html/index.html](docs/html/index.html) in your Web browser to see how your updates appear in the documentation.

Note that [docs/index.html](docs/index.html) is the top page of https://tmtsoftware.github.io/pydocushare/, but it simply redirects to https://tmtsoftware.github.io/pydocushare/html/index.html which is the substantial top page of PyDocuShare. The equivalent source file is [docs/index.rst](docs/index.rst).

The above command sometimes does not work as intended due to remnant from the previous build. In that case, clean the build first:

```bash
 $ python setup.py clean
 $ python setup.py build_sphinx
```

See [Release Procedure](#release-procedure) for more details about how to release the documents at https://tmtsoftware.github.io/pydocushare/ .

## Unit Test

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

## Release Procedure

Follow the procedure below to release a new version.

 * Make sure that all your changes have been committed by `git commit -a -m "your_commit_message"`.
 * Run [all unit tests](#unit-test) and confirm that all tests were passed.
 * Generate [API document](#api-document) and make sure that no error/warning is shown during the document generation.
 * Open [setup.py](setup.py) and set the new version number to release.
 * Run `git commit -a -m "Changed version number"` to commit the change in [setup.py](setup.py).
 * Run `git tag -a vx.y.z -m "Version x.y.z"` to mark the new release.
 * Run `git push --tags`. Make sure that you have `--tags` option to upload all tags to the upstream.
 * You may regenerate [API document](#api-document) to see the new version number in the API document.
 
(TODO: add the document release procedure)
 
## TODO

Use "TODO" keyword in the inline comments in the source code and documentation to indicate things to be fixed in the future versions. The list below shows the major TODOs that are not suitable as inline comments:

 * Add unit tests for Collection handles and CollectionObject.
