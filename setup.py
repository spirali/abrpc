#!/usr/bin/env python

import sys

from setuptools import setup

VERSION=0.1

setup(name='abrpc',
      version=VERSION,
      description='Asynchronous bidirectional RPC',
      long_description="""
      Asynchronous bidirectional RPC based on msgpack
      """,
      author='Stanislav Bohm',
      url='http://github.com/spirali/abrpc',
      packages=['abrpc'],
      install_requires=["msgpack"],
      classifiers=("Programming Language :: Python :: 3",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent"))
