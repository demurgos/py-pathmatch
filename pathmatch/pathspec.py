# -*- coding: utf8 -*-

u"""
This module exposes a minimal interface to manipulate files independently of the detail
implementation (e.g. stored locally or accessed trough SSH).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

# noinspection PyCompatibility
import typing

from six import text_type

from pathmatch.pattern import Pattern


####################################################################################################
# Pathspec                                                                                         #
####################################################################################################


class Pathspec(object):
    def __init__(self, pattern, negated=False):
        u"""
        :type pattern: Pattern
        :param pattern: A pattern
        :type negated: bool
        :param negated: Is this a negative pattern ?
        """
        self.pattern = pattern
        self.negated = negated

    def match(self, text):
        return self.pattern.match(text)


class PathspecList(object):
    def __init__(self, pathspecs):
        u"""
        :type pathspecs: typing.Iterable[Pathspec]
        :param pathspecs:
        """
        self.pathspecs = list(pathspecs)

    def match(self, path):
        u"""

        :type path: text_type
        :param path: The path to match against this list of path specs.
        :return:
        """
        for spec in reversed(self.pathspecs):
            if spec.match(path):
                return not spec.negated

        return False
