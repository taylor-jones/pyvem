# VS Code Extension Management CLI

[![made-for-VSCode](https://img.shields.io/badge/Made%20for-VSCode-1f425f.svg)](https://code.visualstudio.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)

## Description

CLI tool for downloading, installing, and/or updating VSCode editors and extensions over SSH.

## Installation

```sh
cd /path/to/pyvem
python3 -m pip install --user .
```

## Usage

```sh
vem  # or vem --help
```

## Examples

### Downloading Extensions

TODO

### Installing Extensions

TODO

### Updating Extensions

#### Using a single code editor

* Download and install the latest versions of all `VS Code` extensions via ssh host `HOST`.

    ```sh
    vem update -h HOST
    ```

* Download and install the latest versions of all `VS Code Insiders` extensions via ssh host `HOST` and ssh-user `USER`.

    ```sh
    vem update -h HOST -u USER --insiders
    ```

* Download and install the latest versions of all `VS Codium` extensions via ssh host `HOST` on port `PORT` using as user `USER`.

    ```sh
    vem update -h HOST -p PORT -u USER --codium
    ```

#### Using multiple code editors

* Download the latest versions of all `VS Code` extensions and install them into `VS Code Insiders`.

    > Using the long-hand options for source and destination editors.

    ```sh
    vem update -h HOST --source-editor code --dest-editor insiders
    ```

* Download the latest versions of all `VS Code Insiders` extensions and install them into `VS Codium`.

    > Using the short-hand options for source and destination editors.

    ```sh
    vem update -h HOST -s insiders -d codium
    ```
