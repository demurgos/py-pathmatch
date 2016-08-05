# -*- coding: utf8 -*-

u"""
Setup module to install the pathmatch package.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import os
from setuptools import setup, find_packages


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with codecs.open(os.path.join(PROJECT_ROOT, u'README.md'), encoding=u'UTF-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name=u'pathmatch',
    version=u'0.0.1',
    description=u'Path matching utilities',
    long_description=LONG_DESCRIPTION,
    author=u'Charles Samborski',
    author_email=u'samborski.charles@gemalto.com',
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        u'Development Status :: 2 - Pre-Alpha',
        u'Intended Audience :: Developers',
        u'Operating System :: OS Independent',
        u'Programming Language :: Python :: 2.7'
    ],
    keywords=u'sample setuptools development',
    packages=find_packages(exclude=[u'contrib', u'docs', u'tests']),
    install_requires=[
        u'six>=1.10.0',
        u'typing>=3.5.2',
    ],
    extras_require={
        u'dev': [u'pylint>=1.5.6'],
        u'test': [],
    },
    package_data={},
    data_files=[],
    entry_points={},
)
