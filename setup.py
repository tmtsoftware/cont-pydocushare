from distutils.command.clean import clean
from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

class CleanAlsoSphinx(clean):
    def run(self):
        super().run()
        
        import shutil
        from pathlib import Path
        dirs_to_remove = ['docs/doctrees/', 'docs/html/', 'docs/api/']
        for dir_to_remove in dirs_to_remove:
            dir_to_remove_abs = Path(dir_to_remove).resolve()
            print(f'Removing {dir_to_remove_abs}...')
            shutil.rmtree(dir_to_remove_abs, ignore_errors=True)

cmdclass = {'build_sphinx': BuildDoc}
name     = 'PyDocuShare'
version  = '0.1.0'

setup(
    name         = name,
    version      = version,
    description  = 'Python API to interact with DocuShare',
    url          = 'https://github.com/tnakamot/pydocushare',
    author       = 'Takashi Nakamoto',
    author_email = 'tnakamoto@tmt.org',
    license      = 'GPLv2',
    packages     = ['docushare'],
    python_requires  = '>=3.8',
    install_requires = [
        'beautifulsoup4 >= 4.8.2',
        'requests >= 2.22.0',
        'pyduktape >= 0.0.6',
        'anytree >= 2.8.0',
    ],
    extras_require = {
        'password-store': ['keyring >= 18.0.1'],
        'progress-bar': ['tqdm >= 4.30.0'],
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
            'build_dir' : ('setup.py', 'docs'),
            'builder'   : ('setup.py', 'html'),
        }
    },
    cmdclass = {
        'clean': CleanAlsoSphinx,
    }
)
