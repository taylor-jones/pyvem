from __future__ import print_function
from distutils.spawn import find_executable

import os
import sys
import unittest
import requests
import time
import subprocess

from pyvsc._util import get_public_attributes, has_internet_connection
from pyvsc._editor import Editors


def should_skip_remote_testing():
    """
    If NO_REMOTE env variable is set to a truthy value OR no internet
    connection is found, we'll skip any testing that depends on reaching out
    to remote resources to validate URLs

    Returns:
        tuple (bool, str) -- The boolean represents whether or not remote
            testing should be skipped, and the string indicates the reasoining.
    """
    reason = ''
    should_skip = False

    if not has_internet_connection():
        should_skip = True
        reason = 'No internet connection'
    elif bool(os.getenv('NO_REMOTE', False)):
        should_skip = True
        reason = 'NO_REMOTE env var was set'
    return should_skip, reason



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

        # Have to use GET instead of HEAD here, because GitHub doesn't allow
        # HEAD requests, so we'd just get a status_code of 403.
        
        # This bit of code ensures we don't wait for the entire size response
        # size of downloading VSCodium before we can return. Instead, we just
        # get a specified content size (or timeout, whichever happens first),
        # since we really only care about the status code of the request, not
        # the body of the response.
        MAX_CONTENT_LEN = 1
        response = requests.get(url, stream=True)
        response.raise_for_status()

        try:
            if int(response.headers.get('Content-Length')) > MAX_CONTENT_LEN:
                raise ValueError
        except ValueError:
            self.assertEqual(response.status_code, 200)



def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')