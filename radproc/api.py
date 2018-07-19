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
=============
 radproc API
=============
"""
from __future__ import print_function

from radproc.core import coordinates_degree_to_stereographic, save_idarray_to_txt, import_idarray_from_txt 
from radproc.core import load_months_from_hdf5, load_month, load_years_and_resample, hdf5_to_years, hdf5_to_months, hdf5_to_days, hdf5_to_hours, hdf5_to_hydrologicalSeasons

from radproc.raw import unzip_RW_binaries, unzip_YW_binaries, radolan_binaries_to_dataframe, radolan_binaries_to_hdf5, create_idraster_and_process_radolan_data, process_radolan_data

from radproc.wradlib_io import read_RADOLAN_composite

from radproc.heavyrain import find_heavy_rainfalls, count_heavy_rainfall_intervals

from radproc.dwd_gauge import stationfile_to_df, summarize_metadata_files, dwd_gauges_to_hdf5  

try:
    from radproc.arcgis import create_idraster_germany, clip_idraster, raster_to_array, import_idarray_from_raster, create_idarray 
    from radproc.arcgis import export_to_raster, export_dfrows_to_gdb, attribute_table_to_df, join_df_columns_to_attribute_table
    from radproc.arcgis import idTable_nineGrid, idTable_to_valueTable, valueTable_nineGrid, rastervalues_to_points, zonalstatistics
except:
    # here, additional imports for future QGIS or GDAL functions might be possible
    print("ArcGIS is unavailable!")




    


