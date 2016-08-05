# -*- coding: utf8 -*-

u"""
Unit-test for the wildmatch module
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import pathmatch.wildmatch as wildmatch


class TestWildmatchFunctions(unittest.TestCase):
    u"""
    TestCase for the TestWildmatch class
    """

    def match_wild_star(self, pattern, text, result):
        msg = u'Expect match({}, {}) to be {}'.format(repr(pattern), repr(text), repr(result))
        self.assertEqual(result, wildmatch.match(pattern, text, wild_star=True), msg)

    def match(self, pattern, text, result):
        msg = u'Expect match({}, {}) to be {}'.format(repr(pattern), repr(text), repr(result))
        self.assertEqual(result, wildmatch.match(pattern, text), msg)

    def match_case_fold(self, pattern, text, result):
        msg = u'Expect match({}, {}) to be {}'.format(repr(pattern), repr(text), repr(result))
        self.assertEqual(result, wildmatch.match(pattern, text, case_fold=True), msg)

    def translate(self, pattern, regex_pattern):
        translated = wildmatch.translate(pattern)
        self.assertEqual(translated.pattern, regex_pattern)

    def test_match(self):
        # Basic wildmatch features

        # Literal match
        self.match_wild_star(u'foo', u'foo', True)
        self.match_wild_star(u'foo', u'bar', False)
        self.match_wild_star(u'', u'', True)

        # Quantifiers
        self.match_wild_star(u'???', u'foo', True)
        self.match_wild_star(u'??', u'foo', False)
        self.match_wild_star(u'*', u'foo', True)
        self.match_wild_star(u'f*', u'foo', True)
        self.match_wild_star(u'*f', u'foo', False)
        self.match_wild_star(u'*foo*', u'foo', True)
        self.match_wild_star(u'*ob*a*r*', u'foobar', True)
        self.match_wild_star(u'*ab', u'aaaaaaabababab', True)

        # Escaped literal
        self.match_wild_star(u'foo\\*', u'foo*', True)
        self.match_wild_star(u'foo\\*bar', u'foobar', False)
        self.match_wild_star(u'f\\\\oo', u'f\\oo', True)

        # Bracket expression
        self.match_wild_star(u'*[al]?', u'ball', True)
        self.match_wild_star(u'[ten]', u'ten', False)
        self.match_wild_star(u'**[!te]', u'ten', False)  # ** interpreted as wildstar ?
        self.match_wild_star(u'**[!ten]', u'ten', False)  # ** interpreted as wildstar ?

        # Negative character class
        self.match_wild_star(u't[a-g]n', u'ten', True)
        self.match_wild_star(u't[!a-g]n', u'ten', False)
        self.match_wild_star(u't[!a-g]n', u'ton', True)
        self.match_wild_star(u't[^a-g]n', u'ton', True)

        # Bracket expression meta-characters
        self.match_wild_star(u'a[]]b', u'a]b', True)
        self.match_wild_star(u'a[]-]b', u'a-b', True)
        self.match_wild_star(u'a[]-]b', u'a]b', True)
        self.match_wild_star(u'a[]-]b', u'aab', False)
        self.match_wild_star(u'a[]a-]b', u'aab', True)
        self.match_wild_star(u']', u']', True)

        # Extended slash-matching features

        self.match_wild_star(u'foo*bar', u'foo/baz/bar', False)
        self.match_wild_star(u'foo**bar', u'foo/baz/bar', False)
        self.match_wild_star(u'foo**bar', u'foobazbar', False)
        self.match_wild_star(u'foo/**/bar', u'foo/baz/bar', True)
        self.match_wild_star(u'foo/**/**/bar', u'foo/baz/bar', True)
        self.match_wild_star(u'foo/**/bar', u'foo/b/a/z/bar', True)
        self.match_wild_star(u'foo/**/**/bar', u'foo/b/a/z/bar', True)
        self.match_wild_star(u'foo/**/bar', u'foo/bar', True)
        self.match_wild_star(u'foo/**/**/bar', u'foo/bar', True)
        self.match_wild_star(u'foo?bar', u'foo/bar', False)
        self.match_wild_star(u'foo[/]bar', u'foo/bar', False)
        self.match_wild_star(u'f[^eiu][^eiu][^eiu][^eiu][^eiu]r', u'foo/bar', False)
        self.match_wild_star(u'f[^eiu][^eiu][^eiu][^eiu][^eiu]r', u'foo-bar', True)
        self.match_wild_star(u'**/foo', u'foo', True)
        self.match_wild_star(u'**/foo', u'/foo', True)
        self.match_wild_star(u'**/foo', u'bar/baz/foo', True)
        self.match_wild_star(u'*/foo', u'bar/baz/foo', False)
        self.match_wild_star(u'**/bar*', u'foo/bar/baz', False)

        # File/directory distinction
        self.match_wild_star(u'**/bar/*', u'deep/foo/bar/baz', True)
        self.match_wild_star(u'**/bar/*', u'deep/foo/bar/baz/', False)
        self.match_wild_star(u'**/bar/**', u'deep/foo/bar/baz/', True)
        self.match_wild_star(u'**/bar/*', u'deep/foo/bar', False)
        self.match_wild_star(u'**/bar/**', u'deep/foo/bar/', True)
        self.match_wild_star(u'**/bar**', u'foo/bar/baz', False)
        self.match_wild_star(u'*/bar/**', u'foo/bar/baz/x', True)
        self.match_wild_star(u'*/bar/**', u'deep/foo/bar/baz/x', False)
        self.match_wild_star(u'**/bar/*/*', u'deep/foo/bar/baz/x', True)

        # Various additional tests

        self.match_wild_star(u'a[c-c]st', u'acrt', False)
        self.match_wild_star(u'a[c-c]rt', u'acrt', True)
        self.match_wild_star(u'[!]-]', u']', False)
        self.match_wild_star(u'[!]-]', u'a', True)
        self.match_wild_star(u'\\', u'', False)
        self.match_wild_star(u'\\', u'\\', False)
        self.match_wild_star(u'*/\\', u'/\\', False)
        self.match_wild_star(u'*/\\\\', u'/\\', True)

        self.match_wild_star(u'foo', u'foo', True)
        self.match_wild_star(u'@foo', u'@foo', True)
        self.match_wild_star(u'@foo', u'foo', False)

        self.match_wild_star(u'\\[ab]', u'[ab]', True)
        self.match_wild_star(u'[[]ab]', u'[ab]', True)
        self.match_wild_star(u'[[:]ab]', u'[ab]', True)
        self.match_wild_star(u'[[::]ab]', u'[ab]', False)
        self.match_wild_star(u'[[:digit]ab]', u'[ab]', True)
        self.match_wild_star(u'[\\[:]ab]', u'[ab]', True)
        self.match_wild_star(u'\\??\\?b', u'?a?b', True)
        self.match_wild_star(u'\\a\\b\\c', u'abc', True)
        self.match_wild_star(u'', u'foo', False)
        self.match_wild_star(u'**/t[o]', u'foo/bar/baz/to', True)

        # Character class tests

        self.match_wild_star(u'[[:alpha:]][[:digit:]][[:upper:]]', u'a1B', True)
        self.match_wild_star(u'[[:digit:][:upper:][:space:]]', u'a', False)
        self.match_wild_star(u'[[:digit:][:upper:][:space:]]', u'A', True)
        self.match_wild_star(u'[[:digit:][:upper:][:space:]]', u'1', True)
        self.match_wild_star(u'[[:digit:][:upper:][:spaci:]]', u'1', False)
        self.match_wild_star(u'[[:digit:][:upper:][:space:]]', u' ', True)
        self.match_wild_star(u'[[:digit:][:upper:][:space:]]', u'.', False)
        self.match_wild_star(u'[[:digit:][:punct:][:space:]]', u'.', True)
        self.match_wild_star(u'[[:xdigit:]]', u'5', True)
        self.match_wild_star(u'[[:xdigit:]]', u'f', True)
        self.match_wild_star(u'[[:xdigit:]]', u'D', True)
        self.match_wild_star(u'[[:alnum:][:alpha:][:blank:][:cntrl:][:digit:][:graph:][:lower:][:print:][:punct:][:space:][:upper:][:xdigit:]]', u'_', True)
        self.match_wild_star(u'[^[:alnum:][:alpha:][:blank:][:cntrl:][:digit:][:lower:][:space:][:upper:][:xdigit:]]', u'.', True)
        self.match_wild_star(u'[a-c[:digit:]x-z]', u'5', True)
        self.match_wild_star(u'[a-c[:digit:]x-z]', u'b', True)
        self.match_wild_star(u'[a-c[:digit:]x-z]', u'y', True)
        self.match_wild_star(u'[a-c[:digit:]x-z]', u'q', False)

        # Additional tests, including some malformed wildmatch patterns

        self.match_wild_star(u'[\\\\-^]', u']', True)
        self.match_wild_star(u'[\\\\-^]', u'[', False)
        self.match_wild_star(u'[\\-_]', u'-', True)
        self.match_wild_star(u'[\\]]', u']', True)
        self.match_wild_star(u'[\\]]', u'\\]', False)
        self.match_wild_star(u'[\\]]', u'\\', False)
        self.match_wild_star(u'a[]b', u'ab', False)
        self.match_wild_star(u'a[]b', u'a[]b', False)
        self.match_wild_star(u'ab[', u'ab[', False)
        self.match_wild_star(u'[!', u'ab', False)
        self.match_wild_star(u'[-', u'ab', False)
        self.match_wild_star(u'[-]', u'-', True)
        self.match_wild_star(u'[a-', u'-', False)
        self.match_wild_star(u'[!a-', u'-', False)
        self.match_wild_star(u'[--A]', u'-', True)
        self.match_wild_star(u'[--A]', u'5', True)
        self.match_wild_star(u'[ --]', u' ', True)
        self.match_wild_star(u'[ --]', u'$', True)
        self.match_wild_star(u'[ --]', u'-', True)
        self.match_wild_star(u'[ --]', u'0', False)
        self.match_wild_star(u'[---]', u'-', True)
        self.match_wild_star(u'[------]', u'-', True)
        self.match_wild_star(u'[a-e-n]', u'j', False)
        self.match_wild_star(u'[a-e-n]', u'-', True)
        self.match_wild_star(u'[!------]', u'a', True)
        self.match_wild_star(u'[]-a]', u'[', False)
        self.match_wild_star(u'[]-a]', u'^', True)
        self.match_wild_star(u'[!]-a]', u'^', False)
        self.match_wild_star(u'[!]-a]', u'[', True)
        self.match_wild_star(u'[a^bc]', u'^', True)
        self.match_wild_star(u'[a-]b]', u'-b]', True)
        self.match_wild_star(u'[\\]', u'\\', False)
        self.match_wild_star(u'[\\\\]', u'\\', True)
        self.match_wild_star(u'[!\\\\]', u'\\', False)
        self.match_wild_star(u'[A-\\\\]', u'G', True)
        self.match_wild_star(u'b*a', u'aaabbb', False)
        self.match_wild_star(u'*ba*', u'aabcaa', False)
        self.match_wild_star(u'[,]', u',', True)
        self.match_wild_star(u'[\\\\,]', u',', True)
        self.match_wild_star(u'[\\\\,]', u'\\', True)
        self.match_wild_star(u'[,-.]', u'-', True)
        self.match_wild_star(u'[,-.]', u'+', False)
        self.match_wild_star(u'[,-.]', u'-.]', False)
        self.match_wild_star(u'[\\1-\\3]', u'2', True)
        self.match_wild_star(u'[\\1-\\3]', u'3', True)
        self.match_wild_star(u'[\\1-\\3]', u'4', False)
        self.match_wild_star(u'[[-\\]]', u'\\', True)
        self.match_wild_star(u'[[-\\]]', u'[', True)
        self.match_wild_star(u'[[-\\]]', u']', True)
        self.match_wild_star(u'[[-\\]]', u'-', False)

        # Test recursion and the abort code

        self.match_wild_star(u'-*-*-*-*-*-*-12-*-*-*-m-*-*-*', u'-adobe-courier-bold-o-normal--12-120-75-75-m-70-iso8859-1', True)
        self.match_wild_star(u'-*-*-*-*-*-*-12-*-*-*-m-*-*-*', u'-adobe-courier-bold-o-normal--12-120-75-75-X-70-iso8859-1', False)
        self.match_wild_star(u'-*-*-*-*-*-*-12-*-*-*-m-*-*-*', u'-adobe-courier-bold-o-normal--12-120-75-75-/-70-iso8859-1', False)

        self.match_wild_star(u'XXX/*/*/*/*/*/*/12/*/*/*/m/*/*/*', u'XXX/adobe/courier/bold/o/normal//12/120/75/75/m/70/iso8859/1', True)
        self.match_wild_star(u'XXX/*/*/*/*/*/*/12/*/*/*/m/*/*/*', u'XXX/adobe/courier/bold/o/normal//12/120/75/75/X/70/iso8859/1', False)

        self.match_wild_star(u'**/*a*b*g*n*t', u'abcd/abcdefg/abcdefghijk/abcdefghijklmnop.txt', True)
        self.match_wild_star(u'**/*a*b*g*n*t', u'abcd/abcdefg/abcdefghijk/abcdefghijklmnop.txtz', False)

        self.match_wild_star(u'*/*/*', u'foo', False)
        self.match_wild_star(u'*/*/*', u'foo/bar', False)
        self.match_wild_star(u'*/*/*', u'foo/bba/arr', True)
        self.match_wild_star(u'*/*/*', u'foo/bb/aa/rr', False)
        self.match_wild_star(u'**/**/**', u'foo/bb/aa/rr', True)

        self.match_wild_star(u'*X*i', u'abcXdefXghi', True)
        self.match_wild_star(u'*X*i', u'ab/cXd/efXg/hi', False)
        self.match_wild_star(u'*/*X*/*/*i', u'ab/cXd/efXg/hi', True)
        self.match_wild_star(u'**/*X*/**/*i', u'ab/cXd/efXg/hi', True)

        # Test path_name option

        self.match(u'foo', u'foo', True)
        self.match(u'fo', u'foo', False)
        self.match(u'foo/bar', u'foo/bar', True)
        self.match(u'foo/*', u'foo/bar', True)
        self.match(u'foo/*', u'foo/bba/arr', True)
        self.match(u'foo/**', u'foo/bba/arr', True)
        self.match(u'foo*', u'foo/bba/arr', True)
        self.match(u'foo**', u'foo/bba/arr', True)
        self.match(u'foo/*arr', u'foo/bba/arr', True)
        self.match(u'foo/**arr', u'foo/bba/arr', True)
        self.match(u'foo/*z', u'foo/bba/arr', False)
        self.match(u'foo/**z', u'foo/bba/arr', False)
        self.match(u'foo?bar', u'foo/bar', True)
        self.match(u'foo[/]bar', u'foo/bar', True)
        self.match(u'*/*/*', u'foo', False)
        self.match(u'*/*/*', u'foo/bar', True)
        self.match(u'*/*/*', u'foo/bba/arr', True)
        self.match(u'*/*/*', u'foo/bb/aa/rr', True)
        self.match(u'*X*i', u'abcXdefXghi', True)
        self.match(u'*/*X*/*/*i', u'ab/cXd/efXg/hi', True)
        self.match(u'*Xg*i', u'ab/cXd/efXg/hi', True)

        # Case-sensitivy features

        self.match_wild_star(u'[A-Z]', u'a', False)
        self.match_wild_star(u'[A-Z]', u'A', True)
        self.match_wild_star(u'[a-z]', u'A', False)
        self.match_wild_star(u'[a-z]', u'a', True)
        self.match_wild_star(u'[[:upper:]]', u'a', False)
        self.match_wild_star(u'[[:upper:]]', u'A', True)
        self.match_wild_star(u'[[:lower:]]', u'A', False)
        self.match_wild_star(u'[[:lower:]]', u'a', True)
        self.match_wild_star(u'[B-Za]', u'A', False)
        self.match_wild_star(u'[B-Za]', u'a', True)
        self.match_wild_star(u'[B-a]', u'A', False)
        self.match_wild_star(u'[B-a]', u'a', True)
        self.match_wild_star(u'[Z-y]', u'z', False)
        self.match_wild_star(u'[Z-y]', u'Z', True)

        self.match_case_fold(u'[A-Z]', u'a', True)
        self.match_case_fold(u'[A-Z]', u'A', True)
        self.match_case_fold(u'[a-z]', u'A', True)
        self.match_case_fold(u'[a-z]', u'a', True)
        self.match_case_fold(u'[[:upper:]]', u'a', True)
        self.match_case_fold(u'[[:upper:]]', u'A', True)
        self.match_case_fold(u'[[:lower:]]', u'A', True)
        self.match_case_fold(u'[[:lower:]]', u'a', True)
        self.match_case_fold(u'[B-Za]', u'A', True)
        self.match_case_fold(u'[B-Za]', u'a', True)
        self.match_case_fold(u'[B-a]', u'A', True)
        self.match_case_fold(u'[B-a]', u'a', True)
        self.match_case_fold(u'[Z-y]', u'z', True)
        self.match_case_fold(u'[Z-y]', u'Z', True)

        # Additional tests

        self.match_wild_star(u'[[:space:]-\\]]', u'-', True)
        self.match_wild_star(u'[]-z]', u'c', True)
        self.match_wild_star(u'[]-z]', u'-', False)
        self.match_wild_star(u'[[:space:]-z]', u'c', False)

        self.match_wild_star(u'foo', u'foo/bar', False)
        self.match_wild_star(u'foo', u'bar/foo', False)
        self.match_wild_star(u'foo', u'bar/foo/baz', False)

        self.match_wild_star(u'foo/**/bar', u'foo//bar', True)
        self.match_wild_star(u'foo]bar', u'foo]bar', True)
        self.match_wild_star(u'foo[bar', u'foo[bar', False)
        self.match_wild_star(u'foo/**bar', u'foo/bar', False)
        self.match_wild_star(u'foo/**bar', u'foo/x/bar', False)

        self.match_wild_star(u'deep/**', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/*****', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/******', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/***/**', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/***/***', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/**', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/**', u'deep/foo/bar/baz/x', True)
        self.match_wild_star(u'deep/**/***/****/*****', u'deep/foo/bar/baz/x', True)


    def test_translate(self):
        # Basic wildmatch features

        self.translate(u'foo', u'\Afoo\Z')
        self.translate(u'???', u'\A[^/][^/][^/]\Z')
        self.translate(u'??', u'\A[^/][^/]\Z')

        # Extended slash-matching features

        self.translate(u'foo*bar', u'\Afoo[^/]*bar\Z')
        # u'foo/baz/bar' -> False

        self.translate(u'foo**bar', u'\A\Z')
        # u'foo/baz/bar' -> False
        # u'foobazbar' -> False

        self.translate(u'foo/**/bar', u'\Afoo/(?:.*/)*bar\Z')
        # u'foo/baz/bar' -> True
        # u'foo/b/a/z/bar' -> True
        # u'foo/bar' -> True

        self.translate(u'foo/**/**/bar', u'\Afoo/(?:.*/)*bar\Z')
        # u'foo/baz/bar' -> True
        # u'foo/b/a/z/bar' -> True
        # u'foo/bar' -> True

        self.translate(u'foo?bar', u'\Afoo[^/]bar\Z')
        # u'foo/bar' -> False

        self.translate(u'foo[/]bar', None)
        # u'foo/bar' -> False

        self.translate(u'', u'\A\Z')
        self.translate(u'', u'\A\Z')



        self.match_wild_star(u'f[^eiu][^eiu][^eiu][^eiu][^eiu]r', u'foo/bar', False)
        self.match_wild_star(u'f[^eiu][^eiu][^eiu][^eiu][^eiu]r', u'foo-bar', True)
        self.match_wild_star(u'**/foo', u'foo', True)
        self.match_wild_star(u'**/foo', u'/foo', True)
        self.match_wild_star(u'**/foo', u'bar/baz/foo', True)
        self.match_wild_star(u'*/foo', u'bar/baz/foo', False)
        self.match_wild_star(u'**/bar*', u'foo/bar/baz', False)

        # File/directory distinction
        self.match_wild_star(u'**/bar/*', u'deep/foo/bar/baz', True)
        self.match_wild_star(u'**/bar/*', u'deep/foo/bar/baz/', False)
        self.match_wild_star(u'**/bar/**', u'deep/foo/bar/baz/', True)
        self.match_wild_star(u'**/bar/*', u'deep/foo/bar', False)
        self.match_wild_star(u'**/bar/**', u'deep/foo/bar/', True)
        self.match_wild_star(u'**/bar**', u'foo/bar/baz', False)
        self.match_wild_star(u'*/bar/**', u'foo/bar/baz/x', True)
        self.match_wild_star(u'*/bar/**', u'deep/foo/bar/baz/x', False)
        self.match_wild_star(u'**/bar/*/*', u'deep/foo/bar/baz/x', True)


if __name__ == u'__main__':
    unittest.main()
