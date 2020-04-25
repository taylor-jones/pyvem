from __future__ import print_function
from distutils.spawn import find_executable

import os
import sys
import unittest
import requests
import time
import subprocess

from pyvsc._extension import (
    MarketplaceExtension,
    GithubExtension,
    ExtensionSourceTypes,
    get_extension
)

from pyvsc.tests.test_util import should_skip_remote_testing


_GITHUB_EXTENSION_UNIQUE_ID = 'ms-vscode.cpptools'
_MARKETPLACE_EXTENSION_UNIQUE_ID = 'twxs.cmake'


@unittest.skipIf(*should_skip_remote_testing())
class TestGithubExtensions(unittest.TestCase):
    def test_github_extension_is_recognized(self):
        e = get_extension(_GITHUB_EXTENSION_UNIQUE_ID)
        self.assertIsInstance(e, GithubExtension)
        self.assertFalse(e.download_from_marketplace)

    def test_github_extension_download_url_is_valid(self):
        e = get_extension(_GITHUB_EXTENSION_UNIQUE_ID)
        url = e.download_url
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



@unittest.skipIf(*should_skip_remote_testing())
class TestMarketplaceExtensions(unittest.TestCase):
    def test_marketplace_extension_is_recognized(self):
        e = get_extension(_MARKETPLACE_EXTENSION_UNIQUE_ID)
        self.assertIsInstance(e, MarketplaceExtension)
        self.assertTrue(e.download_from_marketplace)

    def test_marketplace_extension_download_url_is_valid(self):
        e = get_extension(_MARKETPLACE_EXTENSION_UNIQUE_ID)
        url = e.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')