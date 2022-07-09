.. _installation:

Install/Uninstall PyDocuShare
=============================

Install
-------

Run the commands below to install PyDocuShare (``docushare`` module) into your user directory:

.. code-block:: bash
                
                $ git clone https://github.com/tmtsoftware/pydocushare.git
                $ cd pydocushare
                $ latest_release=$(git describe --tags `git rev-list --tags --max-count=1`)
                $ git checkout $latest_release
                $ pip install ".[progress-bar,password-store]"

The last command above also installs all required python modules.

For better user experience, it is recommended to specify all extra options (``progress-bar`` and ``password-store``) as shown above. With ``progress-bar`` option, PyDocuShare shows a progress bar when downloading a large file or multiple files. With ``password-store`` option, PyDocuShare can store passwords in a secure manner and reuse the stored passwords for the DocuShare authentication. If you do not need those extra features, you can simply omit all options as shown below:


.. code-block:: bash
                
                $ pip install .

Uninstall
---------

If you want to uninsall PyDocuShare that was installed with ``pip``, run the command below:

.. code-block:: bash
                
                $ pip uninstall pydocushare

