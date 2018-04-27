# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2016-2018, Kreklow.
# Distributed under the MIT License. See LICENSE.txt for more info.
"""
radproc API
===========
"""
global _numba_available

from radproc.core import coordinates_degree_to_stereographic, import_idarray_from_txt 
from radproc.core import load_months_from_hdf5, load_month, load_years_and_resample, hdf5_to_years, hdf5_to_months, hdf5_to_days, hdf5_to_hours, hdf5_to_hydrologicalSeasons

from radproc.raw import unzip_RW_binaries, unzip_YW_binaries, radolan_binaries_to_dataframe, radolan_binaries_to_hdf5, create_idraster_and_process_radolan_data, process_radolan_data

from radproc.wradlib_io import read_RADOLAN_composite

from radproc.erosivity import calc_I30, calc_R_factor, monthly_R_factor, annual_R_factor, annual_R_factor_gauge
from radproc.heavyrain import find_heavy_rainfalls, count_heavy_rainfall_intervals

try:
    from radproc.heavyrain import calc_R_factor_jit
    _numba_available = True
except:
    _numba_available = False


from radproc.dwd_gauge import stationfile_to_df, summarize_metadata_files, dwd_gauges_to_hdf5  

try:
    from radproc.arcgis import create_idraster_germany, clip_idraster, raster_to_array, import_idarray_from_raster, save_idarray_to_txt
    from radproc.arcgis import create_idarray, export_to_raster, export_dfrows_to_gdb, attribute_table_to_df, join_df_columns_to_attribute_table
    from radproc.arcgis import idTable_nineGrid, idTable_to_valueTable, valueTable_nineGrid, rastervalues_to_points, zonalstatistics
except:
    # here, additional imports for future QGIS or GDAL functions might be possible
    print "ArcGIS is unavailable!"




    


