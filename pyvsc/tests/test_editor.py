from __future__ import print_function
from distutils.spawn import find_executable

import os
import sys
import unittest
import requests
import subprocess

from pyvsc._editor import Editors
from pyvsc.tests.test_util import should_skip_remote_testing, github_get


class TestEditorAttributes(unittest.TestCase):
    def test_editors_can_determine_if_installed(self):
        for e in Editors.keys():
            self.assertIsNotNone(Editors[e].installed)

    def test_installed_editors_have_existing_home_directory(self):
        for e in Editors.keys():
            if Editors[e].installed:
                self.assertTrue(os.path.isdir(Editors[e].extensions_dir))

    def test_installed_editors_are_on_path(self):
        for e in Editors.keys():
            cmd = ['command', '-v', Editors[e].command]
            if Editors[e].installed:
                try:
                    subprocess.check_call(cmd, stdout=subprocess.PIPE)
                except subprocess.CalledProcessError:
                    self.fail(
                        '%s was determined to be installed but could not'
                        ' be invoked' % Editors[e].command)
            else:
                with self.assertRaises(subprocess.CalledProcessError):
                    subprocess.check_call(cmd, stdout=subprocess.PIPE)

    def test_can_update_editors_that_are_not_installed(self):
        for e in Editors.keys():
            if not Editors[e].installed:
                self.assertTrue(Editors[e].can_update)

    def test_editor_extensions_should_be_a_list(self):
        for e in Editors.keys():
            self.assertIsInstance(Editors[e].get_extensions(), list)



@unittest.skipIf(*should_skip_remote_testing())
class TestEditorDownloadUrls(unittest.TestCase):
    def test_updatable_editors_have_download_url(self):
        for e in Editors.keys():
            if Editors[e].can_update:
                self.assertTrue(Editors[e].download_url.startswith('https://'))

    def test_code_download_url_is_valid(self):
        url = Editors.code.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_code_insiders_download_url_is_valid(self):
        url = Editors.insiders.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_code_exploration_download_url_is_valid(self):
        url = Editors.exploration.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_vscodium_download_url_is_valid(self):
        url = Editors.codium.download_url
        self.assertIsNotNone(url)
        self.assertEqual(github_get(url), 200)



def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')