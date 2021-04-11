from __future__ import print_function
from distutils.spawn import find_executable
from getpass import getpass

import sys
import unittest

from pyvem._marketplace import Marketplace
from pyvem._containers import ConnectionParts
from pyvem._tunnel import Tunnel
from pyvem.tests.test_util import (
    should_skip_remote_testing,
    get_dummy_tunnel_connection,
)

_tunnel = get_dummy_tunnel_connection(True)
_KNOWN_MARKETPLACE_EXTENSION_UID = 'twxs.cmake'
_KNOWN_MARKETPLACE_SEARCH_TEXT = 'js'

@unittest.skipIf(*should_skip_remote_testing())
class TestMarketplace(unittest.TestCase):
    def test_marketplace_should_be_able_to_get_exact_extension(self):
        m = Marketplace(tunnel=_tunnel)
        uid = _KNOWN_MARKETPLACE_EXTENSION_UID
        response = m.get_extension(uid)

        self.assertIsInstance(response, dict)
        self.assertTrue(bool(response))

    def test_marketplace_should_be_able_search_extensions(self):
        m = Marketplace(tunnel=_tunnel)
        search_text = _KNOWN_MARKETPLACE_SEARCH_TEXT
        response_count = 10
        response = m.search_extensions(search_text, response_count)

        self.assertIsInstance(response, list)
        self.assertIs(len(response), response_count)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
