#!/usr/bin/env python
from distutils.core import setup

setup(name='Reporter',
      version='1.0',
      description='Reporting in LaTeX',
      author='Jan-Jaap Korpershoek',
      author_email='jjkorpershoek96@gmail.com',
      install_requires=[
        'jinja2',
        'pyyaml',
        'deepmerge',
        'cvss',
      ],
      entry_points={
        'console_scripts': ['reporter=reporter:main'],
      },
      py_modules=["reporter"],
      )

