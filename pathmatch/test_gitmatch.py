# -*- coding: utf8 -*-

u"""
Unit-test for the gitmatch module
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import pathmatch.gitmatch as gitmatch
from pathmatch.helpers import generate_tests


@generate_tests(
    normalize_path=[
        # No transformation
        (u'foo', u'/', None, u'foo'),
        (u'/foo', u'/', None, u'/foo'),

        # We expected a POSIX path, this does not transforms separators
        (u'foo\\bar', u'/', None, u'foo\\bar'),

        # Base path
        (u'foo/bar', u'/foo', None, u'foo/bar'),
        (u'/foo/bar', u'/foo', None, u'/bar'),
    ],
    match=[
        (u'build', u'build', True),
        (u'build', u'build/', True),
        (u'build', u'build/README.md', True),
        (u'build/', u'build', False),
        (u'build/', u'build/', True),
        (u'build/', u'build/README.md', True),
        (u'build/**', u'build', False),
        (u'build/**', u'build/', True),
        (u'build/**', u'build/README.md', True),
    ]
)
class TestWildmatchFunctions(unittest.TestCase):
    u"""
    TestCase for the gitmatch functions
    """

    def normalize_path(self, path, base_path, is_dir, expected):
        if expected is None:
            with self.assertRaises(Exception):
                gitmatch.normalize_path(path, base_path, is_dir)
        else:
            actual = gitmatch.normalize_path(path, base_path, is_dir)
            self.assertEqual(expected, actual)

    def match(self, pattern, path, expected):
        if expected:
            self.assertTrue(gitmatch.match(pattern, path))
        else:
            self.assertFalse(gitmatch.match(pattern, path))


if __name__ == u'__main__':
    unittest.main()
