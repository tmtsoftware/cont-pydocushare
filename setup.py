from setuptools import setup, find_packages
setup(
    name         = 'PyDocuShare',
    version      = '0.0.1',
    description  = 'Python API to interact with DocuShare',
    url          = 'https://github.com/tnakamot/pydocushare',
    author       = 'Takashi Nakamoto',
    author_email = 'tnakamoto@tmt.org',
    license      = 'Apache',
    classifiers=[
        'Topic :: Utilities'
    ],
    keywords     = 'DocuShare',
    install_requires = [
        'beautifulsoup4 >= 4.8.2'
    ],
)
