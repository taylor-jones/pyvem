# VS Code Extension Management CLI

[![made-for-VSCode](https://img.shields.io/badge/Made%20for-VSCode-1f425f.svg)](https://code.visualstudio.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)

## Description

CLI tool for downloading, installing, and/or updating VS Code extensions over SSH.

* Download
  * The `download` operation provides the ability to simply download `.vsix` etensions over ssh and store them in a local directory.
* Install
  * The `install` operation provides the ability to install .vsix extensions that exist locally on your file-system.
  * The difference between the pyvsc `install` command and the built-in VSCode `--install-extension` command is that pyvsc allows for installing multiple extensions via a single command.
* Update
  * The `update` operation provides the ability to perform a `download` + `install` in a single command. This command implements the core intension of this project.

## Usage

```sh
usage: vsc [--help] [-c CONFIG] [-d DEST_EDITOR] [-e EXTENSIONS] [-h SSH_HOST]
           [-k] [-n] [-o OUTPUT_DIR] [-p SSH_PORT] [-s SOURCE_EDITOR]
           [-u SSH_USER] [-v] [--insiders] [--codium]
           [operation]

Args that start with '--' (eg. -d) can also be set in a config file (specified
via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
than one place, then commandline values override config file values which
override defaults.

positional arguments:
  operation             The VSCode Extension Manager operation to execute:
                        [download|install|update]

optional arguments:
  --help                Show help message
  -c, --config CONFIG   config file path
  -d, --dest-editor DEST_EDITOR
                        The editor where the extensions will be installed
  -e, --extensions EXTENSIONS
                        A string, list, or directory of extensions to
                        download/update/install
  -h, --ssh-host SSH_HOST
                        SSH Host IP or network name
  -k, --keep            If set, downloaded .vsix files will not be deleted
  -n, --dry-run         Preview the action(s) that would be taken without
                        actually taking them
  -o, --output-dir OUTPUT_DIR
                        The directory where the extensions will be downloaded.
  -p, --ssh-port SSH_PORT
                        SSH Port
  -s, --source-editor SOURCE_EDITOR
                        The editor that will be used to identify extensions
  -u, --ssh-user SSH_USER
                        SSH username
  -v, --verbose         Display more program output
  --insiders            Use VSCode Insiders as the source and destination
                        editor
  --codium              Use VSCodium as the source and destination editor
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
    vsc update -h HOST
    ```

* Download and install the latest versions of all `VS Code Insiders` extensions via ssh host `HOST` and ssh-user `USER`.

    ```sh
    vsc update -h HOST -u USER --insiders
    ```

* Download and install the latest versions of all `VS Codium` extensions via ssh host `HOST` on port `PORT` using as user `USER`.

    ```sh
    vsc update -h HOST -p PORT -u USER --codium
    ```

#### Using multiple code editors

* Download the latest versions of all `VS Code` extensions and install them into `VS Code Insiders`.

    > Using the long-hand options for source and destination editors.

    ```sh
    vsc update -h HOST --source-editor code --dest-editor insiders
    ```

* Download the latest versions of all `VS Code Insiders` extensions and install them into `VS Codium`.

    > Using the short-hand options for source and destination editors.

    ```sh
    vsc update -h HOST -s insiders -d codium
    ```
