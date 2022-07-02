.. _getting-started:

Getting Started
===============

PyDocuShare API allows you to access Collections, Documents and their versions in a DocuShare site in a programmatic way.
You can automate your task or workflow that requires accesses to Xerox DocuShare using this API in Python.

Overview of Typical Workflow
----------------------------

In DocuShare, each docuemnt and object can be identified by a **handle** like Document-00000, Version-000000, Collection-00000. These handles are typically shown as a part of URL when you access your DocuShare site. For example, when you open a Collection in your DocuShare site, the URL in your Web browser should look like:

    https://your.docushare.domain/docushare/dsweb/Get/Document-98765/xxxxx.pdf

"Document-98765" with in this URL is what we call **handle**. This handle is essentially the key to view the properties of the document/collection/version and download the docuemnt file.

Download a document
^^^^^^^^^^^^^^^^^^^

Example below downloads Document-98765 from your DocuShare site in Python:

>>> from docushare import *
>>> ds = DocuShare(base_url='https://your.docushare.domain/docushare/')
>>> ds.login()
_ 
Enter your username for https://your.docushare.domain/docushare/
Username: your_user_name
_ 
Enter password of "your_user_name" for https://your.docushare.domain/docushare/
Password:
_ 
>>> doc = ds.object('Document-98765')
>>> print(f'Download "{doc.title}" as "{doc.filename}".')
>>> doc.download()
PosixPath('/path/to/your/current/directory/{doc.filename}')

Now the Document-98765 should have been downloaded to your local storage in the shown path.

``ds.object(handle)`` may be replaced by ``ds[handle]`` as shown below:

>>> doc = ds['Document-98765']

Download a specific version
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To download a specific version, you can also specify Version handle:

>>> ver = ds['Version-111111']
>>> print(f'Download "{ver.title}" as "{ver.filename}".')
>>> ver.download()
PosixPath('/path/to/your/current/directory/{ver.filename}')


Accessing version information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get the version information as shown below:

>>> doc = ds['Document-98765']
>>> for ver_hdl in doc.version_handles:
...     ver = ds[ver_hdl]
...     print(f'{ver_hdl} is version #{ver.version_number} for {doc.handle}.')


Login DocuShare Site
--------------------

TODO: show more details about login

Handle (Collection-xxxxx, Document-yyyyy, Version-zzzzzz)
----------------------------------------------------------

TODO: talk about what is handle

Document
--------

TODO: talk about the details of handling Document

Collection
----------

TODO: talk about the details of handling Collection
