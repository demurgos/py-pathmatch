# -*- coding: utf8 -*-

u"""
Unit-test for the pathspec module
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import pathmatch.gitmatch as gitmatch
from pathmatch.gitmatch import GitmatchPattern
from pathmatch.pathspec import Pathspec, PathspecList


class TestPathspec(unittest.TestCase):
    u"""
    TestCase for the Pathspec class
    """

    def test_simple(self):
        files = {
            u'LICENSE.txt',
            u'src/banner.txt',
            u'README.md',
            u'src/script.py',
        }

        # Implicitly positive (negated=False)
        ps = Pathspec(GitmatchPattern(u'*.txt'))
        actual = set(ps.filter(files))
        expected = {
            u'LICENSE.txt',
            u'src/banner.txt',
        }
        self.assertEqual(expected, actual)

        # Explicitly positive (negated=False)
        ps = Pathspec(GitmatchPattern(u'*.txt'), negated=False)
        actual = set(ps.filter(files))
        expected = {
            u'LICENSE.txt',
            u'src/banner.txt',
        }
        self.assertEqual(expected, actual)

        # Negated
        ps = Pathspec(GitmatchPattern(u'*.txt'), negated=True)
        actual = set(ps.filter(files))
        expected = {
            u'README.md',
            u'src/script.py',
        }
        self.assertEqual(expected, actual)


class TestPathspecList(unittest.TestCase):
    u"""
    TestCase for the PathspecList class
    """

    def test_add_remove(self):
        files = {
            u'LICENSE.txt',
            u'src/banner.txt',
            u'README.md',
            u'src/script.py',
            u'build/result.txt',
            u'src/build.txt',
        }

        # Implicitly positive (negated=False)
        psl = PathspecList([
            # Included all the txt files
            Pathspec(GitmatchPattern(u'*.txt')),
            # Then exclude all the build files
            Pathspec(GitmatchPattern(u'build'), negated=True),
        ])
        actual = set(psl.filter(files))
        expected = {
            u'LICENSE.txt',
            u'src/banner.txt',
            u'src/build.txt',
        }
        self.assertEqual(expected, actual)


if __name__ == u'__main__':
    unittest.main()
