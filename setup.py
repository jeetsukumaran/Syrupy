#! /usr/bin/env python

############################################################################
##  setup.py
##
##  Copyright 2008 Jeet Sukumaran.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. If not, see <http://www.gnu.org/licenses/>.
##
############################################################################

"""
Package setup and installation.
"""

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup
from setuptools import find_packages

import sys
import os
import subprocess

version = "1.1.4"

setup(name='Syrupy',
      version=version,     
      author='Jeet Sukumaran',
      author_email='jeetsukumaran@gmail.com',
      description="""\
System resource usage profiler""",
      license='GPL 3+',
      packages=[],
      package_dir={},
      package_data={},
      scripts=['scripts/syrupy.py'],   
      include_package_data=True,         
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,      
      long_description="""\
System resource usage profiler: logs the CPU and
memory usage of a process at pre-specified intervals.""",
      classifiers = [
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU Library or  General Public License (GPL)",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            ],
      keywords='profiler memory',      
      )
