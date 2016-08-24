# -*- coding: utf8 -*-

u"""
This module exposes file matching utilities using `gitmatch` patterns.

`gitmatch` is a small variation of wildmatch, it adds semantics for directory matching semantics
(a path is a directory if it ends with a trailing slash) and default deep paths (if the paths are
not rooted/do not start with a slash).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import posixpath
import re
# noinspection PyCompatibility
import typing

from six import text_type

from pathmatch import wildmatch
from pathmatch.pattern import Pattern

RegexType = type(re.compile(u''))


def normalize_path(path, base_path=u'/', is_dir=None):
    u"""
    Normalize a path to use it with a gitmatch pattern.
    This ensures that the separators are forward slashes.
    If a path is rooted (starts with a slash), it has to be a subdirectory of `project_root`. The
    path root is then changed to be based of `project_root`.

    :type path: text_type
    :param path:
    :type base_path: text_type
    :param base_path:
    :type is_dir: text_type
    :param is_dir: If `true`, adds a trailing slash. If `false` removes any trailing slash. If
                   `None`, keeps the current ending.
    :return:
    """
    path = path.replace(u'\\', u'/')
    path = posixpath.normpath(path)

    base_path = base_path.replace(u'\\', u'/')
    base_path = posixpath.normpath(base_path)

    if len(base_path) == 0:
        raise ValueError(u'`project_root` cannot be an empty string after normalization')

    if base_path[-1] != u'/':
        base_path += u'/'

    if path.startswith(base_path):
        path = u'/' + posixpath.relpath(path, base_path)

    if is_dir is None:
        return path
    elif is_dir and path[-1:] != u'/':
        return path + u'/'
    elif not is_dir and path[-1:] == u'/':
        return path[:-1]

    return path


def match(pattern, text):
    u"""
    Matches `text` against the gitmatch pattern `pattern`.

    :type pattern: text_type
    :param pattern: A gitmatch pattern
    :type text: text_type
    :param text: A text to match against this pattern
    :rtype: bool
    :return: Result of the match
    """
    return GitmatchPattern(pattern).match(text)


# noinspection PyShadowingBuiltins
def filter(pattern, texts):
    u"""
    Returns a generator yielding the elements of `texts` matching the pattern.

    :type pattern: text_type
    :param pattern: A gitmatch pattern
    :type texts: typing.Iterable[text_type]
    :param texts: An iterable collection of texts to match
    :rtype: typing.Generator[text_type]
    :return: A generator of filtered elements.
    """
    return GitmatchPattern(pattern).filter(texts)


def translate(pattern):
    u"""
    Returns a compiled Python regular expression equivalent to this pattern.

    :type pattern: text_type
    :param pattern: A gitmatch pattern
    :rtype: RegexType
    """
    return GitmatchPattern(pattern).translate()


class GitmatchPattern(Pattern):
    def __init__(self, pattern):
        u"""
        Creates a new `gitmatch` pattern, useful when reusing a pattern many times since it
        compiles the pattern only once.

        :type pattern: text_type
        :param pattern: A gitmatch pattern
        :rtype: None
        """
        self.pattern = pattern
        self._pattern = pattern if pattern[:1] == u'/' else u'**/' + pattern  # Normalized pattern
        self.regex = wildmatch.translate(self._pattern, closed_regex=True)

    def translate(self):
        u"""
        Returns a compiled Python regular expression equivalent to this pattern.

        :rtype: RegexType
        """
        return self.regex  # TODO: Handle the trailing slash semantic

    def match(self, text):
        u"""
        Matches `text` against the current pattern.

        :type text: text_type
        :param text: A text to match against this pattern
        :rtype: bool
        :return: Result of the match
        """
        # TODO: Handle the trailing slash semantic with the regex
        if self.regex.match(text) is not None:
            return True
        elif len(text) > 2 and text[-1] == u'/':
            return self.regex.match(text[:-1]) is not None
        else:
            return False

    __call__ = match
