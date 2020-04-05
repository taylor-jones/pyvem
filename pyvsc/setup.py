from setuptools import setup, find_packages

__version__ = '0.2-dev'

setup(
    name='pyvsc',
    description='VS Code extension management via SSH',
    version=__version__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'vsc = pyvsc.manager:main',
        ]
    },
    install_requires=[
        'configargparse',
        'paramiko'
    ],
    python_requires='>=2.7'
)
