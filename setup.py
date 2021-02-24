#!/usr/bin/env python3
from setuptools import setup

setup(name     = 'varsomdata',
      author   = 'NVE',
      description = 'Methods and modules for accessing RegObs APIs',
      version  = '1.0.0',
      license  = 'MIT',
      url      = 'https://github.com/NVE/varsomdata',

      packages = ['utilities',
                  'varsomdata',
                  'varsomscripts'],

      install_requires = ['numpy>1.12.0', 'pandas>1.0.0', 'matplotlib>3.0.0']
     )
