"""Tests functionality of the editor module."""

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import subprocess
import sys
import unittest

import requests

from pyvem._editor import get_editors
from pyvem.tests.test_util import (
    should_skip_remote_testing,
    get_dummy_tunnel_connection,
    github_get
)

_TUNNEL = get_dummy_tunnel_connection(True)
_EDITORS = get_editors(_TUNNEL)


class TestEditorAttributes(unittest.TestCase):
    def test_editors_can_determine_if_installed(self):
        for editor in _EDITORS.values():
            self.assertIsNotNone(editor.installed)

    def test_installed_editors_have_extensions_directory(self):
        for editor in _EDITORS.values():
            extensions_dir = editor.extensions_dir
            editor_id = editor.editor_id
            if editor.installed:
                self.assertIsNotNone(extensions_dir, f'{editor_id} should '
                                     'have an extensions directory.')

    def test_installed_editors_have_existing_home_directory(self):
        for editor in _EDITORS.values():
            if editor.installed:
                extensions_dir = editor.extensions_dir
                self.assertTrue(os.path.isdir(extensions_dir),
                                f'{extensions_dir} is not a directory.')

    def test_installed_editors_are_on_path(self):
        for editor in _EDITORS.values():
            cmd = ['command', '-v', editor.command]
            if editor.installed:
                try:
                    subprocess.check_call(cmd, stdout=subprocess.PIPE)
                except subprocess.CalledProcessError:
                    self.fail(f'{editor.command} is installed but could '
                              'not be invoked.')
            else:
                with self.assertRaises(subprocess.CalledProcessError):
                    subprocess.check_call(cmd, stdout=subprocess.PIPE)

    def test_can_update_editors_that_are_not_installed(self):
        for editor in _EDITORS.values():
            if not editor.installed:
                self.assertTrue(editor.can_update)

    def test_editor_extensions_should_be_a_list(self):
        for editor in _EDITORS.values():
            self.assertIsInstance(editor.get_extensions(), list)


@unittest.skipIf(*should_skip_remote_testing())
class TestEditorDownloadUrls(unittest.TestCase):
    def test_updatable_editors_have_download_url(self):
        for editor in _EDITORS.values():
            if editor.can_update:
                self.assertTrue(editor.download_url.startswith('https://'))

    def test_code_download_url_is_valid(self):
        url = _EDITORS.code.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_code_insiders_download_url_is_valid(self):
        url = _EDITORS.insiders.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_code_exploration_download_url_is_valid(self):
        url = _EDITORS.exploration.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_vscodium_download_url_is_valid(self):
        url = _EDITORS.codium.download_url
        self.assertIsNotNone(url)
        self.assertEqual(github_get(url), 200)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
