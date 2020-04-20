from __future__ import print_function
from distutils.spawn import find_executable

import os
import sys
import unittest
import requests
import time
import subprocess

from pyvsc._marketplace import Marketplace
from pyvsc.tests.test_util import should_skip_remote_testing


@unittest.skipIf(*should_skip_remote_testing())
class TestMarketplace(unittest.TestCase):
    def test_marketplace_should_be_able_to_get_exact_extension(self):
        m = Marketplace()
        # use a known [publisher].[package] name
        uid = 'twxs.cmake'
        response = m.get_extension(uid)

        self.assertIsInstance(response, dict)
        self.assertTrue(bool(response))

    def test_marketplace_should_be_able_search_extensions(self):
        m = Marketplace()
        # use a generic search text that is known to have a bunch of results
        search_text = 'js'
        response_count = 10
        response = m.search_extensions(search_text, response_count)

        self.assertIsInstance(response, list)
        self.assertIs(len(response), response_count)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')