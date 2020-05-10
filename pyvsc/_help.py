"""
Help class that is used within Command instances to organize
the components of a Help output message.
"""
from __future__ import print_function, absolute_import
import re

from rich.console import Console
from rich.text import Text
from rich.containers import Lines
from rich.theme import Theme
from textwrap import dedent

from pyvsc._containers import AttributeDict
from pyvsc._util import shell_dimensions, less
from pyvsc._config import rich_theme

_DEFAULT_WRAP_WIDTH = 80
_DEFAULT_INDENT = '    '
_DEFAULT_PAD_SIZE = 4

_text = Text(tab_size=4)
_console = Console(theme=rich_theme)


def _rich_wrapped(text, style):
    """
    Prepares a string for rich formatting by wrapping it in rich-formatted
    syntax.

    Arguments:
        text {str} -- The text to return as rich-formatted
        style {str} -- A rich formatting style (space-separated)
            NOTE: This should be original rich-valid statements like:
            'red bold', etc., not custom theme styles.

    Returns:
        str -- The wrapped string, ready to pass to a rich Console for output.
    """
    return '[{0}]{1}[/{0}]'.format(style, text)


def _rich_themed(text, style, theme=rich_theme):
    """
    Prepares a string for rich formatting by wrapping it in rich-formatted
    syntax.

    Arguments:
        text {str} -- The text to return as rich-formatted
        style {str} -- The name of an existing style from the rich theme.
        theme {rich.Theme} -- The name of an existing rich theme.
            NOTE: This should be custom styles belonging to the theme
    Returns:
        str -- The wrapped string, ready to pass to a rich Console for output.
    """
    return '[{0}]{1}[/{0}]'.format(theme.styles[style], text)


def _rich_command_heading(text):
    """
    Returns a rich-formatted string using a pre-defined heading style.

    Arguments:
        text {str} -- The string to wrap in a rich heading

    Returns:
        str -- The heading-wrapped text.
    """
    return _rich_themed(text, 'h1')


def _current_wrap_width():
    """
    Helps determine the current width at which console text should
    wrap by finding the min of the current width and the default wrap width.

    Returns:
        int -- The number of columns at which the current console will wrap.
    """
    _, _column_width = shell_dimensions()
    return min(_column_width, _DEFAULT_WRAP_WIDTH)


def _wrap(content, pad_size=_DEFAULT_PAD_SIZE):
    """
    Wraps a string such that it fits within the current console width,
    while padding each line of the wrapped text with a specified amount
    of padding.

    Arguments:
        content {str} -- a string to wrap
        pad_size {int} -- the number of spaces to pad the content.

    Returns:
        Text -- a rich text, ready to be printed with a rich Console.
    """
    text = _text.from_markup(dedent(content).strip())
    text = text.wrap(
        console=_console,
        width=_current_wrap_width() - pad_size,
        justify=True,
        tab_size=4,
    )

    for line in text:
        line.pad_left(pad_size)

    return text


def _remove_leading_underscore(text):
    """
    Removes any leading underscores from a given text

    Arguments:
        text {str}

    Returns:
        str -- The text without any leading underscores.
    """
    return re.sub('^[^A-Za-z]*', '', text)


class Help(object):
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

        self._name = name
        self._brief = brief
        self._synopsis = synopsis
        self._description = description
        self._sub_commands = sub_commands
        self._options = options
        self._additional_details = additional_details


    def _generate_from_property(self, prop, titlecase=False):
        """
        Uses an underscored property name to generate both a heading for the
        corresponding help section and format the content for the body of the
        corresponding help section.

        Arguments:
            prop {str} -- A property name representing an internal property.
            Should lead with an underscore (e.g. _name, _description, etc.)

        Returns:
            tuple(Text, Text) -- a tuple of two rich Text objects, which
            are formatted to be printed via a rich Console.
        """
        name = _remove_leading_underscore(prop).upper()
        name = name.replace('_', '-')
        
        if titlecase:
            name = name.title()

        heading = _text.from_markup(_rich_command_heading('\n{}'.format(name)))
        body = _wrap(getattr(self, prop))
        return heading, body


    def print_help(self):
        # specify the list of attribute values we'd like to show
        _parts = [
            '_name',
            '_synopsis',
            '_description',
            '_sub_commands',
            '_options',
            '_additional_details',
        ]

        # get a flattened tuple of the corresponding section values
        # for each of the desirbed parts. Only include sections for which
        # values have been set.
        parts = sum(tuple(
            getattr(self, _remove_leading_underscore(x))
            for x in _parts if getattr(self, x)
        ), ())

        # print each of the sections we found.
        # TODO: Figure out how to capture/supress this, so I can use less
        # for paging the output.
        _console.print(*parts, sep='\n', end='\n', highlight=False)
        # output = _console.export_text(clear=False, styles=True)
        # less(output)

        # NOTE: printing an extra blank line at the end here because
        # the 'end' in the console print above is affecting the end of each
        # section as opposed to the end of the text as a whole.
        print('')


    @property
    def name(self):
        heading = _text.from_markup(_rich_command_heading('\nNAME'))
        name_and_brief = '{name}{brief}'.format(
            name=self._name,
            brief=' -- %s' % self._brief if self._brief else '')
        body = _wrap(name_and_brief)
        return heading, body

    @property
    def description(self):
        return self._generate_from_property('_description')

    @property
    def synopsis(self):
        return self._generate_from_property('_synopsis')

    @property
    def sub_commands(self):
        return self._generate_from_property('_sub_commands', titlecase=True)

    @property
    def options(self):
        return self._generate_from_property('_options')

    @property
    def additional_details(self):
        return self._generate_from_property('_additional_details')

