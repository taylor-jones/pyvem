## VSCode Extension Management CLI

Download, install, and/or update VS Code extensions over SSH.

```sh
Defaults:
  --ssh-host:        localhost
  --ssh-port:        22
  --ssh-user:        user

usage: vscm [-h] [-c CONFIG] [-o OUTPUT_DIR] [-e EXTENSIONS]
            [--ssh-host SSH_HOST] [--ssh-port SSH_PORT] [--ssh-user SSH_USER]
            [--keep] [-i]
            [command]

Args that start with '--' (eg. -o) can also be set in a config file (specified
via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
than one place, then commandline values override config file values which
override defaults.

positional arguments:
  command               The VSCode Extension Manager command to execute:
                        [download|install|update]

optional arguments:
  -h, --help            show this help message and exit
  -c, --config CONFIG   config file path
  -o, --output-dir OUTPUT_DIR
                        The directory where the extensions will be downloaded.
  -e, --extensions EXTENSIONS
                        A string, list, or directory of extensions to
                        download/update/install
  --ssh-host SSH_HOST   SSH Host IP or network name
  --ssh-port SSH_PORT   SSH Port
  --ssh-user SSH_USER   SSH username
  --keep                If set, downloaded .vsix files will not be deleted
  -i, --insiders        Install extensions to VS Code Insiders
```
