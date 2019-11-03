from setuptools import setup, find_packages

setup(
    name='vsc-manager',
    version='0.1',
    packages=find_packages(include=[
        'pyvsc', 
        'pyvsc.*'
    ]),
    entry_points={
        'console_scripts': [
            'vsc-manager = pyvsc.pyvsc.manager:main',
        ]
    },
    install_requires=[
        'configargparse',
        'paramiko'
    ],
    python_requires='>=3.6'
)
