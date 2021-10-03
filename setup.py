# pylint: disable=missing-module-docstring

from setuptools import setup, find_packages

__version__ = '0.5-dev'

setup(
    name='pyvem',
    description='VSCode extension management over SSH',
    version=__version__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'vem = pyvem.main:main'
        ]
    },
    install_requires=[
        'cached_property',
        'configargparse',
        'coloredlogs',
        'fabric',
        'fuzzywuzzy',
        'paramiko',
        'python-Levenshtein',
        'requests',
        'rich',
        'semantic_version',
    ],
    python_requires='>=3.6'
)
