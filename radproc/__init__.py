# -*- coding: utf-8 -*-
# Radproc - A GIS-compatible Python-Package for automated RADOLAN Composite Processing and Analysis.
# Copyright (c) 2018, Jennifer Kreklow.
# DOI: https://doi.org/10.5281/zenodo.1313701
#
# Distributed under the MIT License (see LICENSE.txt for more information), complemented with the following provision:
# For the scientific transparency and verification of results obtained and communicated to the public after
# using a modified version of the work, You (as the recipient of the source code and author of this modified version,
# used to produce the published results in scientific communications) commit to make this modified source code available
# in a repository that is easily and freely accessible for a duration of five years after the communication of the obtained results.

"""
=========
 radproc
=========

"""
from .version import version as __version__

__all__ = ['radproc.api','radproc.heavyrain', 'radproc.core', 'radproc.wradlib_io', 'radproc.raw', 'radproc.arcgis', 'radproc.dwd_gauge', 'radproc.sampledata']

# import subpackages
from radproc.api import *

