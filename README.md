# PyDocuShare

This is the git repository of PyDocuShare, python API to interact with DocuShare.

The user documentation is available at https://tmtsoftware.github.io/pydocushare/ .

This README.md is the documentation for developers who extend, fix and/or release PyDocuShare API.

## License

PyDocuShare uses [pyduktape](https://github.com/stefano/pyduktape) as the underlying JavaScript interpreter to perform DocuShare challenge-response authentication. Because it is distributed under the terms of GNU General Public License version 2, PyDocuShare is distributed under the same license. See [LICENSE](LICENSE) for more details.

## Editable installation

If you want to test PyDocuShare under development, you may want to have the system recognize `docushare` module in your local git repository rather than installing them in one of python system paths. To do so, run the command below:

```bash
 $ pip install -e .
```

The command above adds `docusahre` module in your local git repository to the python system paths. It is called ["editable installs"](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs). You can undo the command above by running:

```bash
 $ pip uninstall pydocushare
```

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

 1. Pre-release procedure
    1. Make sure that you are in the _main_ branch. If not, run `git checkout main`.
    2. Make sure that all your local changes have been committed by `git commit -a -m "your_commit_message"`.
    3. Run [all unit tests](#unit-test) and confirm that all tests were passed.
    4. Generate [user documentation and API reference](#documentation) locally, make sure that there is no error or warning, and check the contents of the generated documents.
       * If the warning is known and you think you do not have to fix it, you may want to update [`nitpick_ignore`](https://www.sphinx-doc.org/en/master/usage/configuration.html?highlight=nitpick_ignore#confval-nitpick_ignore) or [`nitpick_ignore_regex`](https://www.sphinx-doc.org/en/master/usage/configuration.html?highlight=nitpick_ignore#confval-nitpick_ignore_regex) variable in [docs/conf.py](docs/conf.py). 
 2. Version tagging
    1. Open [setup.py](setup.py) and set the new version number to release.
    2. Run `git commit -a -m "Changed version number"` to commit the change in [setup.py](setup.py).
    3. Run `git tag -a vx.y.z -m "Version x.y.z"` to mark the new release.
    4. Run `git push --tags`. Make sure that you have `--tags` option to upload all tags to the upstream.
 3. Release documentation
    1. Run `git checkout gh-pages` to start working in the _gh-pages_ branch.
    2. Run `git merge main` to merge all changes made for the version to release.
    3. Re-generate [user documentation and API reference](#documentation) locally and check if the version number on the top-left corner of the generated HTML pages has been updated.
    4. Run `git add -f docs/html` and `git commit -m "Uploading documentation for version x.y.z."`. These commands are supposed to commit all changes in the documentation under [docs/html](docs/html).
    5. Run `git push` so that GitHub becomes aware of new documentation.
    6. Confirm that the updated documentation is available at https://tmtsoftware.github.io/pydocushare/ . Note that it may take a while (maybe a couple of minutes) until the updated documentation is available there.
    7. Run `git checkout main` to make sure that you are back in the _main_ branch for further development. Do not commit anything  in the _gh-pages_ branch except the new release documents.

## TODO

Use "TODO" keyword in the inline comments in the source code and documentation to indicate things to be fixed in the future versions. The list below shows the major TODOs that are not suitable as inline comments:

 * Add unit tests for Collection handles and CollectionObject.
