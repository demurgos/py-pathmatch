# -*- coding: utf8 -*-

u"""
This module exposes file matching utilities using `wildmatch` patterns.

Many comments in the source code reference "collating elements", these are an abstraction over
characters and represent a "logical unit" for ordering. This is a locale dependent concept, most of
the time one character corresponds to one collating element but there are some multi-character
collating elements in some locales.
https://en.wikipedia.org/wiki/Collation
https://www.gnu.org/software/gnulib/manual/html_node/Collating-Elements-vs_002e-Characters.html
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import re
# noinspection PyCompatibility
import typing

from six import text_type, unichr

from pathmatch.pattern import Pattern


RegexType = type(re.compile(u''))


# POSIX character classes for ASCII.
# This is currently not used, ideally we would support unicode character classes
# http://pubs.opengroup.org/onlinepubs/9699919799/functions/wctype.html
# http://pubs.opengroup.org/onlinepubs/009695399/basedefs/xbd_chap09.html#tag_09_03_05
_CHARACTER_CLASSES = {
    u'alnum': u'[a-zA-Z0-9]',
    u'alpha': u'[a-zA-Z]',
    u'blank': u'[ \\t]',
    u'cntrl': u'[\\x00-\\x1f\\x7f]',  # ASCII C0 (ECMA-48) characters and DEL (0x7f)
    u'digit': u'[0-9]',
    u'graph': u'[\\x21-\\x7e]',  # ASCII graphical characters (without C0, DEL and SP)
    u'lower': u'[a-z]',
    u'print': u'[\\x20-\\x7e]',  # ASCII printable characters (without C0 and DEL)
    u'punct': u'[!"#$%&\'()*+,\\-./:;<=>?@[\\\\\\]^_`{|}~]',  # Escaped characters: -\]
    u'space': u'[ \\t\\r\\n\\v\\f]',  # ASCII: SP, HT, CR, LF, VT, FF
    u'upper': u'[A-Z]',
    u'xdigit': u'[A-Fa-f0-9]',
}

# When inserted in a pattern, this prevents the pattern to match anything.
_PY_IMPOSSIBLE_MATCH = u'(?:a\A)'

# Wildmatch special characters
_SLASH = u'/'  # Path separator
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

    items contains one of the following:
    text_type: literal match, can be a multi-character string to represent some collating elements
    Tuple[text_type, text_type]: represents an inclusive range, the first item is the start
                                 collating element, the second is the end. Only single-character
                                 collating elements are supported.

    """
    def __init__(self, matching, items):
        self.matching = matching
        self.items = items


# Create a node

def _create_bracket_expression(matching, items):
    return u'bracket_expression', matching, items


def _create_be_collating_element(sequence):
    return u'collating_element', sequence


def _create_be_equivalence_class(representant):
    return u'equivalence_class', representant


def _create_be_character_class(name):
    return u'character_class', name


def _create_be_range(start, end):
    return u'range', start, end


def _create_be_unmatched_range():
    return u'_unmatched_range',


# Test a node

def _is_bracket_expression(node):
    return node[0] == u'bracket_expression'


def _is_be_collating_element(item):
    return item[0] == u'collating_element'


def _is_be_equivalence_class(item):
    return item[0] == u'equivalence_class'


def _is_be_character_class(item):
    return item[0] == u'character_class'


def _is_be_range(item):
    return item[0] == u'range'


def _is_be_unmatched_range(item):
    return item[0] == u'_unmatched_range'


# Read a node
def _read_bracket_expression(node):
    return node[1], node[2]


def _read_be_collating_element(item):
    return item[1]


def _read_be_equivalence_class(item):
    return item[1]


def _read_be_character_class(item):
    return item[1]


def _read_be_range(item):
    return item[1], item[2]


def _parse_bracket_expression(pattern, start=0, no_escape=False):
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
    while len(items) == 0 or pattern[i:i + len(_BE_CLOSE)] != _BE_CLOSE:
        if not no_escape and pattern[i:i+len(_ESCAPE)] == _ESCAPE:  # Literal escape \a
            i += len(_ESCAPE)
            if i >= len(pattern):
                raise ValueError(u'Invalid pattern, incomplete escape sequence')
            items.append(_create_be_collating_element(pattern[i:i + 1]))
            i += 1
        elif pattern[i:i+len(_BE_CS_OPEN)] == _BE_CS_OPEN:  # Collating symbol [.abc.]
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
            items.append(_create_be_unmatched_range())
            i += len(_BE_RANGE)
        else:  # Single-character collating element
            items.append(_create_be_collating_element(pattern[i:i+1]))
            i += 1

        if i >= len(pattern):
            raise ValueError(u'InvalidPattern, end of bracket expression not found')
    i += len(_BE_CLOSE)

    # Second pass: resolve ranges
    items_with_ranges = []
    j = 0
    while j < len(items):
        item = items[j]
        if not _is_be_unmatched_range(item):
            items_with_ranges.append(item)
        else:
            # From here, the current item is an unmatched range, we try to get the previous and next
            # item if they are collating elements
            if j == 0:
                prev_elem = None
            else:
                prev_elem = items_with_ranges[-1]
                if not _is_be_collating_element(prev_elem):
                    prev_elem = None
            if j == len(items) - 1:
                next_elem = None
            else:
                next_elem = items[j + 1]
                # case [a--], [---] or [[.a.]--]
                if prev_elem is not None and _is_be_unmatched_range(next_elem):
                    next_elem = _create_be_collating_element(_BE_RANGE)
                elif not _is_be_collating_element(next_elem):
                    next_elem = None

            # Unmatched dash between two collating elements
            if prev_elem is not None and next_elem is not None:
                # Note that we allow ranges between multi-character collating elements
                range_start = _read_be_collating_element(prev_elem)
                range_end = _read_be_collating_element(next_elem)
                # Equivalent to .pop then .append
                items_with_ranges[-1] = _create_be_range(range_start, range_end)
                j += 1  # Skip the next item (corresponds to the end of the range)
            # Add the dash as a collating element
            else:
                items_with_ranges.append(_create_be_collating_element(_BE_RANGE))
                _create_be_collating_element(_BE_RANGE)
        j += 1

    return _create_bracket_expression(matching, items_with_ranges), i - start


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
    if pattern[i:i + len(_BE_CS_OPEN)] != _BE_CS_OPEN:
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

    if pattern[i:i + len(_BE_ECE_OPEN)] != _BE_ECE_OPEN:
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

    if pattern[i:i + len(_BE_CCE_OPEN)] != _BE_CCE_OPEN:
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


def translate(pattern, no_escape=False, path_name=True, wild_star=True, period=False,
              case_fold=False, closed_regex=True):
    u"""
    Converts a wildmatch pattern to a regex

    Note that the EXTMATCH (ksh extended glob patterns) option is not available

    :type pattern: text_type
    :param pattern: A wildmatch pattern
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
    :type closed_regex: bool
    :param closed_regex: Includes anchors to match start and end of string. You might want to
                         disable this flag if you want to compose regular expressions.
    :rtype: RegexType
    :return: A compiled regex object
    """

    # wild_star implies path_name
    if wild_star:
        path_name = True

    if case_fold:
        raise NotImplementedError(u'case_fold is not supported by wildmatch.translate')

    if period:
        raise NotImplementedError(u'period is not supported by wildmatch.translate')

    result = []

    i = 0

    # head_wild_star = False  # Wildstar at the start of the string
    tail_wild_star = False  # Wildstar at the end of the string

    while i < len(pattern):
        # Literal escape \
        if not no_escape and pattern[i:i+len(_ESCAPE)] == _ESCAPE:
            i += len(_ESCAPE)
            if i >= len(pattern):
                raise ValueError(u'Invalid pattern, incomplete escape sequence')
            result.append(re.escape(pattern[i:i + 1]))
            i += 1

        # Bracket expression [a]
        elif pattern[i:i+len(_BE_OPEN)] == _BE_OPEN:
            be, be_len = _parse_bracket_expression(pattern, i, no_escape=no_escape)
            translated_be = _py_pattern_from_bracket_expression(be, path_name=path_name)
            result.append(translated_be)
            i += be_len

        # Wildstar ** (matched before asterisk)
        elif wild_star and pattern[i:i+len(_WILD_STAR)] == _WILD_STAR:
            if i == 0:
                # Uncomment the following line to detect wild stars at start of pattern
                # head_wild_star = True
                pass
            else:
                if pattern[i - 1] != _SLASH:
                    raise ValueError(u'Invalid pattern: wild star ** can only start pattern or '
                                     u'follow a slash')
            i += len(_WILD_STAR)
            while True:  # Consume stars, example: foo/**/****/***/bar is equivalent to foo/**/bar
                if i == len(pattern):
                    tail_wild_star = True
                    break
                if pattern[i:i+len(_ASTERISK)] == _ASTERISK:
                    i += len(_ASTERISK)
                    continue
                elif pattern[i:i+len(_SLASH)] == _SLASH:
                    if pattern[i:i + len(_SLASH) + len(_WILD_STAR)] == _SLASH + _WILD_STAR:
                        i += len(_ASTERISK) + len(_WILD_STAR)
                        continue
                    else:
                        i += len(_SLASH)
                        break
                else:
                    raise ValueError(u'Invalid pattern: wild star ** can only end pattern or '
                                     u'be followed by a slash')

            if tail_wild_star:  # Pattern like ** or foo/**:
                result.append(u'.*')
            else:  # Pattern like **/foo or foo/**/bar, the slash following ** is already consumed
                result.append(u'(?:.*\\/)?')

        # Asterisk *
        elif pattern[i:i+len(_ASTERISK)] == _ASTERISK:
            if path_name:
                result.append(u'[^/]*')
            else:
                result.append(u'.*')
            i += len(_ASTERISK)

        # Question mark ?
        elif pattern[i:i + len(_QUESTION_MARK)] == _QUESTION_MARK:
            if path_name:
                result.append(u'[^/]')
            else:
                result.append(u'.')
            i += len(_QUESTION_MARK)

        # Literal
        else:
            result.append(re.escape(pattern[i:i+1]))
            i += 1

        if i > len(pattern):
            raise ValueError(u'InvalidPattern: parse error, index out of bounds')

    pattern = u''.join(result)
    if closed_regex:
        pattern = u'\\A' + pattern + u'\\Z'
    return re.compile(pattern)


def _py_pattern_from_bracket_expression(bracket_expression, path_name):
    u"""
    This does not handle exclusion of separators in the bracket expression when pathname is True
    :param bracket_expression:
    :return:
    """
    single_chars = set()
    multi_chars = set()
    ranges = set()
    matching, items = _read_bracket_expression(bracket_expression)
    for item in items:
        if _is_be_range(item):
            start_seq, end_seq = _read_be_range(item)
            if len(start_seq) != 1 or len(end_seq) != 1:
                raise ValueError(u'Ranges are only supported between single-char collating elems')
            ranges.add((start_seq, end_seq))
        elif _is_be_character_class(item):
            # TODO: handle character classes...
            # Idea: (?:[single r-an-ge-!]|multi1|multi2|[class1]|[class2])
            raise ValueError(u'Character classes are not supported')
        else:
            if _is_be_collating_element(item):
                sequence = _read_be_collating_element(item)
            elif _is_be_equivalence_class(item):
                sequence = _read_be_equivalence_class(item)
            else:
                raise ValueError(u'Unexpected item {}'.format(item))

            if len(sequence) == 0:
                raise ValueError(u'Empty string is not a valid collating element')
            elif len(sequence) == 1:
                single_chars.add(sequence)
            else:
                multi_chars.add(sequence)

    if path_name:  # bracket expression cannot match /
        if not matching:
            single_chars.add(_SLASH)  # Pretty easy!
        else:  # Remove slash from single_chars and ranges (we do not check multi_chars)
            if _SLASH in single_chars:
                single_chars.remove(_SLASH)

            slash_code_point = ord(_SLASH)
            cleared_ranges = set()
            for be_range in ranges:
                start_seq, end_seq = be_range
                if len(start_seq) != 1 or len(end_seq) != 1:
                    raise ValueError(u'Only ranges between single characters are supported in '
                                     u'bracket expression with the path_name flag')
                start_code_point = ord(start_seq)
                end_code_point = ord(end_seq)
                if start_code_point > end_code_point:
                    raise ValueError(u'Invalid range, wrong order of bounds: {}'.format(be_range))
                if slash_code_point < start_code_point or slash_code_point > end_code_point:
                    cleared_ranges.add(be_range)
                else:
                    if start_seq == slash_code_point:
                        if end_code_point == slash_code_point:  # /-/
                            continue
                        else:  # start = slash < end
                            start_seq = unichr(start_code_point + 1)
                            cleared_ranges.add((start_seq, end_seq))
                    else:
                        if end_code_point == slash_code_point:  # start < slash = end
                            end_seq = unichr(end_code_point - 1)
                            cleared_ranges.add((start_seq, end_seq))
                        else:  # start < slash < end
                            before_slash = unichr(slash_code_point - 1)
                            after_slash = unichr(slash_code_point + 1)
                            cleared_ranges.add((start_seq, before_slash))
                            cleared_ranges.add((after_slash, end_seq))
            ranges = cleared_ranges

    if len(single_chars) > 0 or len(ranges) > 0:
        primary_pattern = [u'['] if matching else [u'[^']

        for char in single_chars:
            primary_pattern.append(_escape_bracket_expression_character(char))

        for start, end in ranges:
            primary_pattern.append(_escape_bracket_expression_character(start))
            primary_pattern.append(u'-')
            primary_pattern.append(_escape_bracket_expression_character(end))

        primary_pattern.append(u']')
        primary_pattern = u''.join(primary_pattern)
    else:
        primary_pattern = None

    if len(multi_chars) > 0:
        if not matching:
            raise ValueError(u'Cannot perform negative match on bracket expression containing '
                             u'multi-character collating elements')
        alternate_pattern = u'|'.join(re.escape(seq) for seq in multi_chars)
    else:
        alternate_pattern = None

    if alternate_pattern is None:
        if primary_pattern is None:  # Can happen when removing characters
            return _PY_IMPOSSIBLE_MATCH
        else:
            return primary_pattern
    else:
        if primary_pattern is not None:
            alternate_pattern = primary_pattern + u'|' + alternate_pattern
        return u'(?:{})'.format(alternate_pattern)


def _escape_bracket_expression_character(unsafe_char):
    if unsafe_char == u'^':
        return u'\\^'
    elif unsafe_char == u']':
        return u'\\]'
    elif unsafe_char == u'-':
        return u'\\-'
    elif unsafe_char == u'\\':
        return u'\\\\'
    else:
        return unsafe_char


def match(pattern, text, no_escape=False, path_name=True, wild_star=True, period=False,
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

    regex = translate(pattern, no_escape=no_escape, path_name=path_name, wild_star=wild_star,
                      period=period, case_fold=case_fold, closed_regex=True)
    return regex.match(text) is not None


# noinspection PyShadowingBuiltins
def filter(pattern, texts, no_escape=False, path_name=False, wild_star=False, period=False,
           case_fold=False):
    u"""
    A returns a generator yielding the elements of `texts` matching the pattern with the supplied
    options.

    :type pattern: text_type
    :param pattern: A wildmatch pattern
    :type texts: typing.Iterable[text_type]
    :param texts: An iterable collection of texts to match
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
    :rtype: typing.Iterable[text_type]
    :return: A generator of filtered elements.
    """
    regex = translate(pattern, no_escape=no_escape, path_name=path_name, wild_star=wild_star,
                      period=period, case_fold=case_fold, closed_regex=True)
    return (text for text in texts if regex.match(text) is not None)


class WildmatchPattern(Pattern):
    def __init__(self, pattern, no_escape=False, path_name=True, wild_star=True, period=False,
                 case_fold=False):
        u"""
        :type pattern: text_type
        :param pattern: A wildmatch pattern
        :type no_escape: bool
        :param no_escape: Disable backslash escaping
        :type path_name: bool
        :param path_name: Separator (slash) in text cannot be matched by an asterisk, question-mark
                          nor bracket expression in pattern (only a literal).
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
        :rtype: None
        """

        self.pattern = pattern
        self.flags = {
            u'no_escape': no_escape,
            u'path_name': path_name,
            u'wild_star': wild_star,
            u'period': period,
            u'case_fold': case_fold
        }
        self.regex = translate(pattern, closed_regex=True, **self.flags)

    def translate(self, closed_regex=True):
        u"""
        Returns a Python regular expression allowing to match
        :return:
        """
        if closed_regex:
            return self.regex
        else:
            return translate(self.pattern, closed_regex=False, **self.flags)

    def match(self, text):
        u"""
        Matches `text` against the current pattern.

        :type text: text_type
        :param text: A text to match against this pattern
        :rtype: bool
        :return: Result of the match
        """
        return self.regex.match(text) is not None

    __call__ = match

    def filter(self, texts):
        u"""
        Returns a generator yielding the elements of `texts` matching this pattern.

        :type texts: typing.Iterable[text_type]
        :param texts: An iterable collection of texts to match
        :rtype: typing.Iterable[text_type]
        :return: A generator of filtered elements.
        """
        return (text for text in texts if self.regex.match(text) is not None)
