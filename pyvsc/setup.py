from setuptools import setup, find_packages

setup(
    name='vsc',
    description='VS Code extension management via SSH',
    version='0.1',
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
    python_requires='>=3.6'
)
