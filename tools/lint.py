# -*- coding: utf8 -*-

u"""
This module lints the current sagessh project and displays the report.
It checks the `sagessh` and `tools` packages and the `setup.py` module.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import os

import pylint.lint


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), u'..'))
os.chdir(PROJECT_ROOT)

pylint.lint.Run([
    u'--load-plugins', u'tools.lint_string_prefix',
    u'--py3k',
    u'pathmatch', u'tools', u'setup.py'
])
