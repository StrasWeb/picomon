#!/usr/bin/env python3

from distutils.core import setup

setup(name='Picomon',
      version='0.1',
      description='Picomon is a very small and minimal alerting tool',
      author='Jonathan Michalon',
      license='GNU GPLv3',
      url='http://gitlab.netlib.re/arn/picomon/',
      packages=['picomon', 'picomon.subprocess_compat'],
      scripts=['bin/picomon', 'bin/picomon-watchdog'],
      data_files=[('etc/picomon/', ['config-sample.py'])],
     )
