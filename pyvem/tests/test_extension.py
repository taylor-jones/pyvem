from __future__ import print_function
from distutils.spawn import find_executable

import sys
import unittest
import requests

from pyvem._extension import (
    Extension,
    MarketplaceExtension,
    GithubExtension,
    get_extension
)

from pyvem.tests.test_util import (
    should_skip_remote_testing,
    get_dummy_tunnel_connection,
    github_get
)


_KNOWN_GITHUB_EXTENSION_UID = 'ms-vscode.cpptools'
_KNOWN_MARKETPLACE_EXTENSION_UID = 'twxs.cmake'
_tunnel = get_dummy_tunnel_connection(True)


@unittest.skipIf(*should_skip_remote_testing())
class TestGithubExtensions(unittest.TestCase):
    def test_github_extension_is_extension(self):
        e = get_extension(_KNOWN_GITHUB_EXTENSION_UID, tunnel=_tunnel)
        self.assertIsInstance(e, Extension)
        self.assertFalse(e.should_download_from_marketplace)

    def test_github_extension_is_recognized(self):
        e = get_extension(_KNOWN_GITHUB_EXTENSION_UID, tunnel=_tunnel)
        self.assertIsInstance(e, GithubExtension)
        self.assertFalse(e.should_download_from_marketplace)

    def test_github_extension_latest_download_url_is_valid(self):
        e = get_extension(_KNOWN_GITHUB_EXTENSION_UID, tunnel=_tunnel)
        url = e.download_url
        self.assertIsNotNone(url)
        self.assertEqual(github_get(url), 200)

    def test_github_extension_release_download_url_is_valid(self):
        e = get_extension(
            _KNOWN_GITHUB_EXTENSION_UID,
            release='0.27.0',
            tunnel=_tunnel)
        url = e.download_url
        self.assertIsNotNone(url)
        self.assertEqual(github_get(url), 200)

    def test_github_extension_invalid_release_download_url_is_not_found(self):
        e = get_extension(
            _KNOWN_GITHUB_EXTENSION_UID,
            release='0.0.0',
            tunnel=_tunnel)
        url = e.download_url
        self.assertIsNotNone(url)
        self.assertEqual(github_get(url), 404)


@unittest.skipIf(*should_skip_remote_testing())
class TestMarketplaceExtensions(unittest.TestCase):
    def test_marketplace_extension_is_recognized(self):
        e = get_extension(_KNOWN_MARKETPLACE_EXTENSION_UID, tunnel=_tunnel)
        self.assertIsInstance(e, MarketplaceExtension)
        self.assertTrue(e.should_download_from_marketplace)

    def test_marketplace_extension_is_extension(self):
        e = get_extension(_KNOWN_MARKETPLACE_EXTENSION_UID, tunnel=_tunnel)
        self.assertIsInstance(e, Extension)
        self.assertTrue(e.should_download_from_marketplace)

    def test_marketplace_extension_download_url_is_valid(self):
        e = get_extension(_KNOWN_MARKETPLACE_EXTENSION_UID, tunnel=_tunnel)
        url = e.download_url
        self.assertIsNotNone(url)

        response = requests.head(url, allow_redirects=True)
        self.assertEqual(response.status_code, 200)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
