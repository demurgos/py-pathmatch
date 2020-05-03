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
with codecs.open(os.path.join(PROJECT_ROOT, u'README.rst'), encoding=u'UTF-8') as f:
    LONG_DESCRIPTION = f.read().replace('\r\n', '\n').replace('\r', '\n')

setup(
    name=u'pathmatch',
    version=u'0.2.2',
    description=u'Path matching utilities',
    long_description=LONG_DESCRIPTION,
    author=u'Charles Samborski',
    author_email=u'demurgos.net@gmail.com',
    license=u'MIT License',
    url = 'https://github.com/demurgos/py-pathmatch',
    download_url = 'https://github.com/demurgos/py-pathmatch/tarball/v0.2.2',
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        u'Development Status :: 3 - Alpha',
        u'Intended Audience :: Developers',
        u'License :: OSI Approved :: MIT License',
        u'Operating System :: OS Independent',
        u'Programming Language :: Python :: 2.7',
        u'Programming Language :: Python :: 3.5',
        u'Topic :: Utilities'
    ],
    keywords=[u'fnmatch', u'wildmatch', u'gitignore'],
    packages=find_packages(exclude=[u'contrib', u'docs', u'tests', u'tools']),
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
