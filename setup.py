from setuptools import setup
#from setuptools import find_packages
import os

version = '0.1.0dev0'

def write_version_py(filename='radproc/version.py'):
    content = "# THIS FILE IS GENERATED FROM RADPROC SETUP.PY\nversion = '%s'" % version
    f = open(filename, 'w')
    f.write(content)
    f.close()

write_version_py()
    
setup(
  name = 'radproc',
  packages = ['radproc'], # this must be the same as the name above
  version = version,
  description = 'Library for RADOLAN composite processing, analysis and data exchange with ArcGIS.',
  #long_description=open('README.txt').read(),
  author = 'Jennifer Kreklow',
  author_email = 'kreklow@phygeo.uni-hannover.de',
  #url = 'https://github.com/peterldowns/mypackage', # use the URL to the github repo
  #download_url = 'https://github.com/peterldowns/mypackage/archive/0.1.tar.gz', # I'll explain this in a second
  license = 'MIT',
  keywords = ['RADOLAN', 'weather radar', 'ArcGIS', 'precipitation', 'heavy rainfall', 'erosivity', ], 
  classifiers = [],
  #packages = ['radproc.heavyrain', 'radproc.io', 'radproc.wradlib_io'],
  py_modules = ['radproc.api','radproc.heavyrain', 'radproc.core', 'radproc.wradlib_io', 'radproc.raw', 'radproc.arcgis', 'radproc.dwd_gauge'],
  install_requires = ['numpy', 'pandas', 'tables', 'future']
)
