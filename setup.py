#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(name     = 'varsomdata',
      author   = 'NVE',
      description = 'Methods and modules for accessing RegObs APIs',
      version  = '1.0.0',
      license  = 'MIT',
      url      = 'https://github.com/NVE/varsomdata',
      install_requires = ['numpy>1.12.0', 'pandas>1.0.0', 'matplotlib>3.0.0'],
      packages = find_packages(),
      include_package_data=True, # check MANIFEST.in for explicit rules
     )
