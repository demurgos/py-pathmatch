Pathmatch
=========

Python implementation of ``git``'s ``wildmatch`` and `POSIX.1-2008 <http://pubs.opengroup.org/onlinepubs/9699919799/>`_ ``fnmatch``.

The aim of this package is to provide a file matching module complying with the POSIX standard and
allow compatibility with ``git``.

Example
-------

.. code:: python

    from pathmatch import wildmatch

    # Pattern matching auto-generated test files (extension .pyc, .pyo or .pyd inside tests/)
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


Features
--------

wildmatch support
~~~~~~~~~~~~~~~~~

Currently, the following ``wildmatch`` features are supported:

- Wildstar ``**`` operator and associated semantics (``/`` requires a literal match)
- Literal matching
- Question mark ``?`` (any character) and asterisk ``*`` (any string) operators
- Bracket expressions ``[abc]`` (character alternatives)

Bracket expression features:

- Negation (supports both ``^`` and ``!`` meta-characters)
- Range expressions ``a-z``
- Collation Symbol ``[.ch.]``
- Equivalence classes syntax ``[=e=]``, but fallback to collation symbol semantics
- Supports the ``path_name`` flag to exclude ``/`` (which requires a literal match)

See ``test_wildmatch.py`` for more details.

Limitations:

- ``case_fold`` (case insensitive) option is not supported
- ``period`` (require literal match for leading period) option is not supported
- Negated bracket expression with multi-character collating elements are not supported
- Character classes ``[:alpha:]`` for bracket expressions are not supported

**Contributions are welcomed**

fnmatch support
~~~~~~~~~~~~~~~

The dedicated ``fnmatch`` module is not yet configured (this should just be a subset of wildmatch).

Contributing
------------

Tests
~~~~~

You can execute the tests with the following command:

.. code:: shell

    python -m unittest discover -s . -p test*.py


References:
-----------

- `fnmatch <http://pubs.opengroup.org/onlinepubs/9699919799/functions/fnmatch.html>`_, see  also `pattern matching <http://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_13>`_
- `wildmatch C implementation for git <https://github.com/git/git/blob/master/wildmatch.c>`_
- `wildmatch C implementation (alternative) <https://github.com/davvid/wildmatch/blob/master/wildmatch/wildmatch.c>`_
- `wildmatch Javascript implementation <https://github.com/vmeurisse/wildmatch/blob/master/src/wildmatch.js>`_

License
-------

MIT License, Copyright (c) 2016 Charles Samborski
