from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

cmdclass = {'build_sphinx': BuildDoc}

name         = 'PyDocuShare'
version      = '0.0.1'

setup(
    name         = name,
    version      = version,
    description  = 'Python API to interact with DocuShare',
    url          = 'https://github.com/tnakamot/pydocushare',
    author       = 'Takashi Nakamoto',
    author_email = 'tnakamoto@tmt.org',
    license      = 'Apache',
    python_requires  = '>=3.8',
    install_requires = [
        'beautifulsoup4 >= 4.8.2',
        'requests >= 2.22.0',
    ],
    extras_require = {
        'password-store': ['keyring >= 18.0.1'],
        'docs': [
            'sphinx >= 4.5.0',
            'sphinx-rtd-theme >= 1.0.0',
            'sphinx-automodapi >= 0.14.1',
            'enum-tools >= 0.9.0',
        ],
    },
    classifiers=[
        'Topic :: Utilities'
    ],
    keywords     = 'DocuShare',
    command_options={
        'build_sphinx': {
            'project'   : ('setup.py', name),
            'version'   : ('setup.py', version),
            'copyright' : ('setup.py', '2022 TMT International Observatory'),
            'source_dir': ('setup.py', 'docs'),
            'build_dir' : ('setup.py', 'build/docs'),
            'builder'   : ('setup.py', 'html'),
        }
    },
)
