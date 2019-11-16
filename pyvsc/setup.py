from setuptools import setup, find_packages

setup(
    name='vscm',
    description='Visual Studio Code core & extensions management via SSH tunneling',
    version='0.1',
    packages=find_packages(include=[
        'pyvsc', 
        'pyvsc.*'
    ]),
    entry_points={
        'console_scripts': [
            'vscm = pyvsc.pyvsc.manager:main',
        ]
    },
    install_requires=[
        'configargparse',
        'paramiko'
    ],
    python_requires='>=3.6'
)
