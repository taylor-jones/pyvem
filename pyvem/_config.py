"""General program configurations"""

from fabric.util import get_local_user
from rich.theme import Theme

_PROG = 'vem'
_VERSION = '0.5.0-dev'

_DEFAULT_SSH_PORT = 22
_DEFAULT_SSH_USER = get_local_user()

# custom 'rich' theme to use for rich output formatting.
rich_theme = Theme({
    'h1': 'bold red',
    'h2': 'cyan',
    'info': 'cyan',
    'keyword': 'bold bright_white',
    'var': 'cornflower_blue',
    'example': 'italic grey58',
    'path': 'grey58',
    'error': 'red',
    'warning': 'gold3',
    'todo': 'bold bright_magenta on purple4',
}, inherit=True)
