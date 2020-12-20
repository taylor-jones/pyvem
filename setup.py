from setuptools import setup, find_packages

__version__ = '0.4-dev'

setup(
    name='pyvsc',
    description='VSCode extension management over SSH',
    version=__version__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'vem = pyvsc.main:main'
        ]
    },
    install_requires=[
        'configargparse',
        'coloredlogs',
        'fabric',
        'fuzzywuzzy',
        'paramiko',
        'python-Levenshtein',
        'rich',
        'semantic_version',
    ],
    python_requires='>=3.6'
)
