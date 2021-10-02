"""Help class used within Command instances to organize the components of a
Help output message
"""

import re
from textwrap import dedent
from typing import Tuple

from rich.console import Console
from rich.text import Text, Lines

from pyvem._util import shell_dimensions
from pyvem._config import rich_theme
from rich.theme import Theme

_DEFAULT_WRAP_WIDTH = 80
_DEFAULT_PAD_SIZE = 4

_text = Text(tab_size=4)
_console = Console(theme=rich_theme)


def _rich_themed(text: str, style: str, theme: Theme = rich_theme) -> str:
    """
    Wraps a string in rich-formatted syntax.

    Arguments:
        text -- The text to return as rich-formatted
        style -- The name of an existing style from the rich theme.
        theme -- The name of an existing rich.Theme.
            NOTE: This should be custom styles belonging to the theme

    Returns:
        The wrapped string, ready to pass to a rich Console for output.
    """
    return '[{0}]{1}[/{0}]'.format(theme.styles[style], text)


def _rich_command_heading(text: str) -> str:
    """
    Returns a rich-formatted string using a pre-defined heading style.

    Arguments:
        text -- The string to wrap in a rich heading

    Returns:
        The heading-wrapped text.
    """
    return _rich_themed(text, 'h1')


def _current_wrap_width() -> int:
    """
    Helps determine the current width at which console text should
    wrap by finding the min of the current width and the default wrap width.

    Returns:
        int -- The number of columns at which the current console will wrap.
    """
    _, _column_width = shell_dimensions()
    return min(_column_width, _DEFAULT_WRAP_WIDTH)


def _wrap_for_console(content: str) -> Lines:
    """
    Wraps a string such that it fits within the current console width, while
    padding each line of the wrapped text with a specified amount of padding.

    Arguments:
        content -- a string to wrap
        padsize -- the number of spaces to pad the content.

    Returns:
        A rich.Text instance, ready to be printed with a rich.Console.
    """
    text = _text.from_markup(dedent(content).strip())
    text = text.wrap(console=_console,
                     width=_current_wrap_width() - _DEFAULT_PAD_SIZE,
                     justify=True, tab_size=4)
    for line in text:
        line.pad_left(_DEFAULT_PAD_SIZE)
    return text


class Help():
    """Help class implementation"""
    # pylint: disable=too-many-arguments

    def __init__(
            self,
            name,
            brief=None,
            synopsis=None,
            description=None,
            options=None,
            sub_commands=None,
            additional_details=None,
    ):
        super().__init__()
        self.name = name
        self.brief = brief
        self.synopsis = synopsis
        self.description = description
        self.sub_commands = sub_commands
        self.options = options
        self.additional_details = additional_details

        self.heading = name
        if self.brief:
            self.heading += ' -- ' + self.brief


    def _rich_section(self, name: str, content: str) -> Tuple[Text, Lines]:
        """
        Uses an underscored property name to generate both a heading for the
        corresponding help section and format the content for the body of the
        corresponding help section.

        Arguments:
            name -- The section name.
            content -- The help content to display for the section.

        Returns:
            A tuple of two rich objects:
                Text - the rich-formatted section heading
                Lines - the rich-formatted section body
        """
        name = name.upper().replace('_', '-')
        heading = _text.from_markup(_rich_command_heading('\n{}'.format(name)))
        body = _wrap_for_console(content)
        return heading, body


    def print_help(self) -> None:
        """Print the help output"""

        parts = list()

        for part in [
            ('NAME', self.heading),
            ('SYNOPSIS', self.synopsis),
            ('DESCRIPTION', self.description),
            ('Sub-Commands', self.sub_commands),
            ('OPTIONS', self.options),
            ('ADDITIONAL DETAILS', self.additional_details),
        ]:
            if part[1]:
                parts.append(self._rich_section(*part))

        parts = sum(tuple(parts), ())

        # Print the paged help info
        with _console.pager(styles=True):
            _console.print(*parts, sep='\n', end='\n', highlight=False)

        # NOTE: printing an extra blank line at the end here because
        # the 'end' in the console print above is affecting the end of each
        # section as opposed to the end of the text as a whole.
        print('')
