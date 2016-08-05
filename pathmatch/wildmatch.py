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


from abc import ABCMeta, abstractmethod

from six import text_type
import typing

from future.utils import with_metaclass
import paramiko

import re

import fnmatch

RegexType = type(re.compile(u''))

# POSIX character classes
# http://pubs.opengroup.org/onlinepubs/9699919799/functions/wctype.html
# http://pubs.opengroup.org/onlinepubs/009695399/basedefs/xbd_chap09.html#tag_09_03_05
_CHARACTER_CLASSES = {
    u'alnum': re.compile(u'[a-zA-Z0-9]'),
    u'alpha': re.compile(u'[a-zA-Z]'),
    u'blank': re.compile(u'[ \\t]'),
    u'cntrl': re.compile(u'[\\x00-\\x1f\\x7f]'),  # ASCII C0 (ECMA-48) characters and DEL (0x7f)
    u'digit': re.compile(u'[0-9]'),
    u'graph': re.compile(u'[\\x21-\\x7e]'),  # ASCII graphical characters (without C0, DEL and SP)
    u'lower': re.compile(u'[a-z]'),
    u'print': re.compile(u'[\\x20-\\x7e]'),  # ASCII printable characters (without C0 and DEL)
    u'punct': re.compile(u'[!"#$%&\'()*+,\\-./:;<=>?@[\\\\\\]^_`{|}~]'),  # Escaped characters: -\]
    u'space': re.compile(u'[ \\t\\r\\n\\v\\f]'),  # ASCII: SP, HT, CR, LF, VT, FF
    u'upper': re.compile(u'[A-Z]'),
    u'xdigit': re.compile(u'[A-Fa-f0-9]'),
}

# Wildmatch special characters
_SLASH = u'/'  # Directories separator
_PERIOD = u'.'
_ASTERISK = u'*'
_WILD_STAR = u'**'
_QUESTION_MARK = u'?'
_ESCAPE = u'\\'

# Bracket expression
_BE_OPEN = u'['
_BE_NON_MATCHING = u'!'  # Characters negating the bracket expression
_BE_NON_MATCHING2 = u'^'  # POSIX allows to use it as an alternative (git's `wildmatch` uses it)
_BE_CLOSE = u']'
_BE_CS_OPEN = u'[.'  # Collating symbol
_BE_ECE_OPEN = u'[='  # Equivalence class expression
_BE_CCE_OPEN = u'[:'  # Character class expression
_BE_CS_CLOSE = u'.]'  # Collating symbol
_BE_ECE_CLOSE = u'=]'  # Equivalence class expression
_BE_CCE_CLOSE = u':]'  # Character class expression
_BE_RANGE = u'-'


class _BracketExpression(object):
    u"""

    list contains one of the following:
    text_type: literal match, can be a multi-character string to represent some collating elements
    Tuple[text_type, text_type]: represents an inclusive range, the first item is the start
                                 collating element, the second is the end. Only single-character
                                 collating elements are supported.

    """
    def __init__(self, matching, list):
        self.matching = matching
        self.list = list


# Create a bracket expression item

def _create_be_collating_element(sequence):
    return u'collating_element', sequence


def _create_be_equivalence_class(representant):
    return u'equivalence_class', representant


def _create_be_character_class(name):
    return u'character_class', name


def _create_be_range(start, end):
    return u'range', start, end


def _create_be_empty_range():
    return u'_empty_range'


# Test a bracket expression item

def _is_be_collating_element(item):
    return item[0] == u'collating_element'


def _is_be_equivalence_class(item):
    return item[0] == u'equivalence_class'


def _is_be_character_class(item):
    return item[0] == u'character_class'


def _is_be_range(item):
    return item[0] == u'range'


def _is_be_empty_range(item):
    return item[0] == u'_empty_range'


# Read a bracket expression item

def _read_be_collating_element(item):
    return item[1]


def _read_be_equivalence_class(item):
    return item[1]


def _read_be_character_class(item):
    return item[1]


def _read_be_range(item):
    return item[1], item[2]


def _parse_bracket_expression(pattern, start=0):
    u"""

    :type pattern: text_type
    :param pattern:
    :param start:
    :return:
    """
    i = start

    if pattern[i:i+len(_BE_OPEN)] != _BE_OPEN:
        raise ValueError(u'Expected {}'.format(repr(_BE_OPEN)))
    i += len(_BE_OPEN)

    # fnmatch builds on top of POSIX, but uses `!` while POSIX uses `^`
    if pattern[i:i+len(_BE_NON_MATCHING)] == _BE_NON_MATCHING:
        matching = False
        i += len(_BE_NON_MATCHING)
    elif pattern[i:i+len(_BE_NON_MATCHING2)] == _BE_NON_MATCHING2:
        matching = False
        i += len(_BE_NON_MATCHING2)
    else:
        matching = True


    # We iterate other the items twice, first we get the tokens and parse most of it except for
    # ranges. Then, we resolve ranges by joining collating elements separated by an empty range
    # marker

    # Items in this bracket expression
    items = []

    # First pass: tokenize
    while len(list) == 0 or pattern[i:i + len(_BE_CLOSE)] != _BE_CLOSE:
        if pattern[i:i+len(_BE_CS_OPEN)] == _BE_CS_OPEN:  # Collating symbol [.abc.]
            cs, cs_len = _parse_be_collating_symbol(pattern, i)
            items.append(_create_be_collating_element(cs))
            i += cs_len
        elif pattern[i:i+len(_BE_ECE_OPEN)] == _BE_ECE_OPEN:  # Equivalence class expression [=abc=]
            # Currently, equivalence classes are a synonym for collating symbols because we do not
            # support equivalence classes. The difference is that we have to prevent them from
            # ending ranges to eventually add support for equivalence classes in the future
            ec_repr, ece_len = _parse_be_equivalence_class_expression(pattern, i)
            items.append(_create_be_equivalence_class(ec_repr))
            i += ece_len
        elif pattern[i:i+len(_BE_CCE_OPEN)] == _BE_CCE_OPEN:  # Character class expression [:alpha:]
            cc_name, cce_len = _parse_be_character_class_expression(pattern, i)
            items.append(_create_be_character_class(cc_name))
            i += cce_len
        elif pattern[i:i + len(_BE_RANGE)] == _BE_RANGE:  # Range a-c
            items.append(_create_be_empty_range())
            i += len(_BE_RANGE)
        else:  # Single-character collating element
            items.append(_create_be_collating_element(pattern[i:i+1]))
            i += 1

        if i >= len(pattern):
            raise ValueError(u'InvalidPattern, end of bracket expression not found')

    # Second pass: resolve ranges
    items_with_ranges = []
    for j in range(len(items)):
        item = items[j]
        if not _is_be_empty_range(item):
            items_with_ranges.append(item)
            continue
        if j == 0 or j == len(items) - 1:
            # _BE_RANGE at start or end of bracket expression: literal match
            # The item creation uses implicitly len(_BE_RANGE) == 1
            items_with_ranges.append(_create_be_collating_element(_BE_RANGE))
            continue
        # We now know that there are items before and after:
        before = items_with_ranges[-1]
        after = items[j + 1]
        if _is_be_collating_element(before) and _is_be_collating_element(after):
            start_seq = _read_be_collating_element(before)
            end_seq = _read_be_collating_element(after)
            # We currently allow ranges between multi-character collating elements
            items_with_ranges.append(_create_be_range(start_seq, end_seq))
        elif _is_be_range(before):  # Example: [a-b-c]
            raise ValueError(u'InvalidPattern: forbidden chained ranges')
        else:
            # TODO:
            # [--a] means range from `-` to `a`
            # [a--] means range from `a` to `-` (valid syntax, invalid semantic)
            # [a--b] is invalid
            # [[:alpha:]--a] is valid
            # [b-c--a] is valid
            pass


def _parse_be_collating_symbol(pattern, start=0):
    # POSIX allows to define local-dependent digraphs and other groups of characters that
    # should be treated as a single character. We do not support it because this is a local
    # dependant behavior. For example, if a locale defines the digraph 'ch' as a
    # collating symbol, both expressions should match the text 'echo':
    # e[[.ch.]]o
    # e?o
    # Since translation to the python regex pattern syntax for multi-character collating
    # symbols is not well defined yet, we only support single character symbols and let them
    # match themselves. An idea would be to translate e[a[.ch.]b]e to e(?:[ab]|ch)o but this
    # does not solve the translation of e?o unless we know all the collating symbols, this
    # would give something like e(?:.|ch|ae|symb)o where 'ch', 'ae' and 'symb' are all the
    # collating symbols of the current locale.

    i = start

    if pattern[i:i + len(_BE_CS_OPEN)] == _BE_CS_OPEN:
        raise ValueError(u'Expected {}'.format(repr(_BE_CS_OPEN)))
    i += len(_BE_CS_OPEN)

    ce_start = i  # Start of collating element

    while pattern[i:i + len(_BE_CS_CLOSE)] != _BE_CS_CLOSE:
        i += 1
        if i >= len(pattern):
            raise ValueError(u'Invalid pattern, end of collating symbol not found')

    ce_end = i  # End of collating element
    i += len(_BE_CS_CLOSE)

    return pattern[ce_start:ce_end], i - start


def _parse_be_equivalence_class_expression(pattern, start=0):
    # POSIX allows to define local dependant equivalences between collating symbols (see above).
    # For example, 'e', 'é', 'è' and 'ê' are members of the same equivalence class in the french
    # locale so the pattern [[=e=]][[=e=]][[=e=]][[=e=]] matches the text 'eéèê'.
    # We do not support equivalence classes, a equivalence class expression only matches itself.
    # For the same reason as collating symbols, we do not support multi-character sequences.

    i = start

    if pattern[i:i + len(_BE_ECE_OPEN)] == _BE_ECE_OPEN:
        raise ValueError(u'Expected {}'.format(repr(_BE_ECE_OPEN)))
    i += len(_BE_ECE_OPEN)

    elem_start = i  # Start of collating element

    while pattern[i:i + len(_BE_ECE_CLOSE)] != _BE_ECE_CLOSE:
        i += 1
        if i >= len(pattern):
            raise ValueError(u'Invalid pattern, end of equivalence class expression not found')

    elem_end = i  # End of collating element
    i += len(_BE_ECE_CLOSE)

    return pattern[elem_start:elem_end], i - start


def _parse_be_character_class_expression(pattern, start=0):
    # [:alpha:]

    i = start

    if pattern[i:i + len(_BE_CCE_OPEN)] == _BE_CCE_OPEN:
        raise ValueError(u'Expected {}'.format(repr(_BE_CCE_OPEN)))
    i += len(_BE_CCE_OPEN)

    ce_start = i  # Start of collating element

    while pattern[i:i + len(_BE_CCE_CLOSE)] != _BE_CCE_CLOSE:
        i += 1
        if i >= len(pattern):
            raise ValueError(u'Invalid pattern, end of character class expression not found')

    ce_end = i  # End of collating element
    i += len(_BE_CCE_CLOSE)

    return pattern[ce_start:ce_end], i - start


def translate(pattern, casefold=False, pathname=True):
    u"""
    Converts a wildmatch pattern to a regex

    :type pattern: text_type
    :param pattern: A wildmatch pattern
    :rtype: RegexType
    :return: A compiled regex object
    """
    raise NotImplementedError(u'translate')


def match(pattern, text, no_escape=False, path_name=False, wild_star=False, period=False,
          case_fold=False):
    u"""
    Matches text against the supplied wildmatch pattern.

    To get git's behavior, use the `wild_star` flag.

    Note that the EXTMATCH (ksh extended glob patterns) option is not available

    :type pattern: text_type
    :param pattern: A wildmatch pattern
    :type text: text_type
    :param text: The text to match
    :type no_escape: bool
    :param no_escape: Disable backslash escaping
    :type path_name: bool
    :param path_name: Separator (slash) in text cannot be matched by an asterisk, question-mark nor
                      bracket expression in pattern (only a literal).
    :type wild_star: bool
    :param wild_star: A True value forces the `path_name` flag to True. This allows the
                      double-asterisk `**` to match any (0 to many) number of directories
    :type period: bool
    :param period: A leading period in text cannot be matched by an asterisk, question-mark nor
                   bracket expression in pattern (only a literal). A period is "leading" if:
                   - it is the first character of `text`
                   OR
                   - path_name (or wild_star) is True and the previous character is a slash
    :type case_fold: bool
    :param case_fold: Perform a case insensitive match (GNU Extension)
    :rtype: bool
    :return: Result of the match
    """

    pattern_length = len(pattern)
    text_length = len(text)
    pattern_pos = 0
    text_pos = 0



    return False


def filter(pattern, texts, casefold=False, pathname=True):
    return (text for text in texts if match(pattern, text, casefold, pathname))



class WildmatchPattern(object):
    def __init__(self, pattern):
        u"""
        :type pattern: text_type
        :param pattern: A valid pathmatch pattern
        """
        self.pattern = pattern

    def translate(self, text):
        return translate(self.pattern)

    def match(self, text):
        return match(self.pattern, text)

    def filter(self, texts):
        return filter(self.pattern, texts)
