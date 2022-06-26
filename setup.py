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
        'beautifulsoup4 >= 4.8.2'
    ],
    
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
