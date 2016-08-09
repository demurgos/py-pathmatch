# Pathmatch

Python implementation of `git`'s `wildmatch` and [POSIX.1-2008](POSIX.1-2008) `fnmatch`.

The aim of this package is to provide a file matching module complying with the POSIX standard and
allow compatibility with `git`.

## Example

```python
from pathmatch import wildmatch

# Pattern matching auto-generated test files (extension .pyc, .pyo or .pyd inside `tests/`)
pattern = u'tests/**/*.py[cod]'

# Match single files:
wildmatch.match(pattern, u'tests/auto.pyc')  # True
wildmatch.match(pattern, u'auto.pyc')  # False

# Filter a collection:
files = [
    u'tests/deep/auto.pyd',
    u'tests/module.py',
    u'package/auto.pyc',
    u'tests/auto.pyo'
]
list(wildmatch.filter(pattern, files))  # [u'tests/deep/auto.pyd', u'tests/auto.pyo']

# Compile a pattern
compiled = wildmatch.WildmatchPattern(pattern)

compiled.match(u'tests/')  # False
```

## Features

### wildmatch

Currently, the following `wildmatch` features are supported:

- Wildstar `**` operator and associated semantics (`/` requires a literal match)
- Literal matching
- Question mark `?` (any character) and asterisk `*` (any string) operators
- Bracket expressions `[abc]` (character alternatives)
  - Negation (supports both `^` and `!` meta-characters)
  - Range expressions `a-z`
  - Collation Symbol `[.ch.]`
  - Equivalence classes syntax `[=e=]`, but fallback to collation symbol semantics

Limitations:

- `case_fold` (case insensitive) option is not supported
- `period` (require literal match for leading period) option is not supported
- Negated bracket expression with multi-character collating elements are not supported
- Character classes `[:alpha:]` for bracket expressions are not supported
- Exclusion of `/` from bracket expressions (including negated ones) is not performed.

**Contributions are welcomed**

See `test_wildmatch.py` for more details.

### fnmatch

The dedicated `fnmatch` module is not yet configured (this should just be a subset of wildmatch).

## References:
- [fnmatch](fnmatch-spec), see  also [pattern matching](pattern-matching)
- [wildmatch](wildmatch-implem-git) C implementation for `git`
- [wildmatch](wildmatch-implem-c) C implementation (alternative)
- [wildmatch](wildmatch-implem-js) Javascript implementation

## License

[MIT License, Copyright (c) 2016 Charles Samborski](./LICENSE.md)


[POSIX.1-2008]: http://pubs.opengroup.org/onlinepubs/9699919799/
[fnmatch-spec]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/fnmatch.html
[pattern-matching]: http://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_13
[wildmatch-implem-git]: https://github.com/git/git/blob/master/wildmatch.c
[wildmatch-implem-c]: https://github.com/davvid/wildmatch/blob/master/wildmatch/wildmatch.c
[wildmatch-implem-js]: https://github.com/vmeurisse/wildmatch/blob/master/src/wildmatch.js
