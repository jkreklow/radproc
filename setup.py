from setuptools import setup
#from setuptools import find_packages
#from distutils.core import setup
import os

version = '0.1.0'

def write_version_py(filename='radproc/version.py'):
    content = "# THIS FILE IS GENERATED FROM RADPROC SETUP.PY\nversion = '%s'" % version
    with open(filename, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    write_version_py()

    CLASSIFIERS = """\
    Development Status :: 5 - Production/Stable
    Intended Audience :: Science/Research
    Intended Audience :: Developers
    Intended Audience :: Education
    License :: OSI Approved :: MIT License
    Programming Language :: Python
    Programming Language :: Python :: 2
    Programming Language :: Python :: 2.7
    Topic :: Scientific/Engineering
    Topic :: Scientific/Engineering :: Atmospheric Science
    Topic :: Scientific/Engineering :: GIS
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
    Operating System :: Microsoft :: Windows
    """
    
    with open('requirements.txt', 'r') as f:
        INSTALL_REQUIRES = [rq for rq in f.read().split('\n') if rq != '']
    
    setup(
      name = 'radproc',
      #packages = ['radproc'], # this must be the same as the name above
      #packages = find_packages(),
      packages = ['radproc', 'radproc.sampledata'],
      package_data={'radproc': ['sampledata/radolan_proj.prj']},
      include_package_data = True,
      version = version,
      description = 'Library for RADOLAN composite processing, analysis and data exchange with ArcGIS.',
      #long_description=open('README.rst').read(),
      author = 'Jennifer Kreklow',
      author_email = 'kreklow@phygeo.uni-hannover.de',
      url = 'https://github.com/jkreklow/radproc', # use the URL to the github repo
      download_url = 'https://github.com/jkreklow/radproc/blob/master/dist/radproc-0.1.0-py2-none-any.whl', 
      license = 'MIT',
      keywords = ['RADOLAN', 'weather radar', 'ArcGIS', 'precipitation', 'heavy rainfall'], 
      classifiers = [],
      #py_modules = ['radproc.api','radproc.heavyrain', 'radproc.core', 'radproc.wradlib_io', 'radproc.raw', 'radproc.arcgis', 'radproc.dwd_gauge'],
      install_requires = INSTALL_REQUIRES
    )
