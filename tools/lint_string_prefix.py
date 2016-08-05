# -*- coding: utf8 -*-

u"""
Define a Pylint plugin to check for string literal prefixes: every string should start either
with `u` or `b`.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import tokenize

from pylint.interfaces import ITokenChecker
from pylint.checkers import BaseTokenChecker


class StringPrefixChecker(BaseTokenChecker):
    u"""
    Pylint TokenChecker for string literals.
    """

    __implements__ = (ITokenChecker,)

    name = u'stringprefix'
    msgs = {
        u'W5750': (
            u'Ambiguous string literal %s',
            u'ambiguous-string-literal',
            u'Used when a string literal does not contain a 'b' or 'u' prefix.'
        )
    }
    options = ()

    def _check_string(self, token, start_row):
        if token[0].lower() not in (u'b', u'u'):
            self.add_message(
                u'ambiguous-string-literal',
                line=start_row,
                args=(token,)
            )

    def process_tokens(self, tokens):
        u"""
        Iterate other tokens to find strings and ensure that they are prefixed.
        :param tokens:
        :return:
        """
        for (tok_type, token, (start_row, _), _, _) in tokens:
            if tok_type == tokenize.STRING:
                self._check_string(token, start_row)


def register(linter):
    u"""
    Register the string_prefix checker as Pylint plugin
    """
    linter.register_checker(StringPrefixChecker(linter))
