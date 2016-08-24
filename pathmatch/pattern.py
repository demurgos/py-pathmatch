# -*- coding: utf8 -*-

u"""
Abstract pattern
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from abc import ABCMeta, abstractmethod
import re
# noinspection PyCompatibility
import typing

from six import text_type, with_metaclass


RegexType = type(re.compile(u''))


####################################################################################################
# Abstract Pattern                                                                                 #
####################################################################################################


class Pattern(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def match(self, text):
        u"""
        Match a text against the current pattern.

        :type text: text_type
        :param text: A text to match against the current Pattern.
        :rtype: bool
        :return: If the provided text is matched by the current Pattern.
        """
        pass

    def filter(self, texts):
        u"""
        A helper function that returns a generator yielding the elements of `texts` matching
        this pattern.

        :type texts: typing.Iterable[text_type]
        :param texts: An iterable collection of texts to match
        :rtype: typing.Generator[text_type]
        :return: A generator of matched elements
        """
        return (text for text in texts if self.match(text))

    @abstractmethod
    def translate(self):
        u"""
        Returns a compiled regular expression equivalent to this pattern.
        :rtype: RegexType
        """
        pass
