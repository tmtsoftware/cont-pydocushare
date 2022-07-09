.. _installation:

Install/Uninstall PyDocuShare
=============================

Install
-------

Run the commands below to install PyDocuShare (``docushare`` module):

.. code-block:: bash
                
                $ pip install -i https://test.pypi.org/simple/ PyDocuShare[progress-bar,password-store]

For better user experience, it is recommended to specify all extra options (``progress-bar`` and ``password-store``) as shown above. With ``progress-bar`` option, PyDocuShare shows a progress bar when downloading a large file or multiple files. With ``password-store`` option, PyDocuShare can store passwords in a secure manner and reuse the stored passwords for the DocuShare authentication. If you do not need those extra features, you can simply omit all options as shown below:


.. code-block:: bash
                
                $ pip install -i https://test.pypi.org/simple/ PyDocuShare

Uninstall
---------

If you want to uninsall PyDocuShare that was installed with ``pip``, run the command below:

.. code-block:: bash
                
                $ pip uninstall PyDocuShare

