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
=========================
 Heavy Rainfall Analysis
=========================

Module for heavy rainfall analysis.

    - identify and select all intervals in which a specified precipitation threshold is exceeded
    - count the number of threshold exceedances
    - calculate duration sums

.. autosummary::
   :nosignatures:
   :toctree: generated/

   find_heavy_rainfalls
   count_heavy_rainfall_intervals
   duration_sum
   
   
.. module:: radproc.heavyrain
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module heavyrain
.. moduleauthor:: Jennifer Kreklow

"""

from __future__ import division, print_function
import pandas as pd
import numpy as np
import radproc.core as _core
import gc
import warnings, tables


def _exceeding(rowseries, thresholdValue, minArea):
    minYcellsgreqXmm_bool = np.count_nonzero(rowseries >= thresholdValue) > minArea
    return minYcellsgreqXmm_bool


def find_heavy_rainfalls(HDFFile, year_start, year_end, thresholdValue, minArea, season):
    """
    Creates a DataFrame containing all heavy rainfalls (intervals) exceeding a specified threshold intensity value.
    
    Search parameters are
    ---------------------
        * rainfall intensity
        * minimum area (number of cells) where intensity has to be exceeded
        * season / time period
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly pandas DataFrames with precipitation data.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer
            Last year for which data are to be loaded.
        thresholdValue : integer
            Rainfall intensity threshold value.
        minArea : integer
            Minimum area where intensity threshold value has to be exceeded.
        season : string or list
            Season / Time period to analyse. Can be a list with integer values from 1 to 12 or a string describing the season. The following strings are possible:
            ["Year" | "May - October" | "November - April" | "January/December" | "Jan" | "Feb" | "Mar" | "Apr" | "May" | "Jun" | "Jul" | "Aug" | "Sep" | "Oct" | "Nov" | "Dec"]
    
    
    :Returns:
    ---------
    
        heavy_rains : pandas DataFrame
            containing all intervals meeting the given criteria.
    """
    if season == "Year":
        months = [1,2,3,4,5,6,7,8,9,10,11,12]
    elif season == "May - October":
        months = [5,6,7,8,9,10]
    elif season == "November - April":
        months = [1,2,3,4,11,12]
    elif season == "January/December":
        months = [1,12]
    elif season == "Jan":
        months = [1]
    elif season == "Feb":
        months = [2]
    elif season == "Mar":
        months = [3]
    elif season == "Apr":
        months = [4]
    elif season == "May":
        months = [5]
    elif season == "Jun":
        months = [6]
    elif season == "Jul":
        months = [7]
    elif season == "Aug":
        months = [8]
    elif season == "Sep":
        months = [9]
    elif season == "Oct":
        months = [10]
    elif season == "Nov":
        months = [11]
    elif season == "Dec":
        months = [12]
    
    years = np.arange(year_start,year_end + 1)
        
    for year in years:
        for month in months:
            df = _core.load_month(HDFFile=HDFFile, year=year, month=month)
            #create a Series with a Bool for each row, True == criteria fulfilled and interval identified as heavy rainfall.
            exceedances = df.apply(_exceeding, axis = 1, args=(thresholdValue, minArea))
            #select all rows for which the calculated Bool evaluates to True and
            #try to append these data to the dataframe with identified heavy rainfall intervals
            try:
                heavy_rains = heavy_rains.append(df.loc[exceedances == True])
            # for the first month, heavy_rains is not yet defined, which causes a NameError. In this case, a new DataFrame is created instead of appending data.
            except NameError:
                heavy_rains = df.loc[exceedances == True]
                
            del df
            gc.collect()
            
    return heavy_rains


def count_heavy_rainfall_intervals(HDFFile, year_start, year_end, thresholdValue, minArea, season):
    """
    Creates a DataFrame containing the sum of all heavy rainfalls intervals exceeding a specified threshold intensity value.
    
    Search parameters are
        * rainfall intensity
        * minimum area (number of cells) where intensity has to be exceeded
        * season / time period
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly pandas DataFrames with precipitation data.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer
            Last year for which data are to be loaded.
        thresholdValue : integer
            Rainfall intensity threshold value.
        minArea : integer
            Minimum area (number of cells) where intensity threshold value has to be exceeded.
        season : string or list
            Season / Time period to analyse. Can be a list with integer values from 1 to 12 or a string describing the season. The following strings are possible:
            ["Year" | "May - October" | "November - April" | "January/December" | "Jan" | "Feb" | "Mar" | "Apr" | "May" | "Jun" | "Jul" | "Aug" | "Sep" | "Oct" | "Nov" | "Dec"]
    
    
    :Returns:
    ---------
    
        interval_count : pandas DataFrame
            containing the sum of all intervals meeting the given criteria.
            Temporal resolution depending on the given season.
    """

    #Define frequency for data aggregation depending on selected season
    if season == "Year" or season == [1,2,3,4,5,6,7,8,9,10,11,12]:
        freq = "A-DEC"
    elif season == "May - October":
        freq = "A-OCT"
    elif season == "November - April":
        freq = "A-APR"
    elif season == "January/December":
        freq = "A-JAN"
    elif season in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]:
        freq = "M"
    elif type(season) == list:
        freq = "M"

    pd_version = int(pd.__version__.split('.')[-2])

    #Find all intervals in which a rainfall intensity of x mm is exceeded in y raster cells.
    #Returns boolean raster with True == threshold value exceeded and  False for not exceeded.
    hr_intervals_bool = find_heavy_rainfalls(HDFFile, year_start, year_end, thresholdValue, minArea, season) >= thresholdValue
    # Convert booleans to 0/1
    hr_intervals = hr_intervals_bool.astype('int32')
    # Calculate the sum of exceedances per cell in the given time period by resampling.
    # Choose syntax for resample method depending on pandas version. how = "sum" is deprecated in newer version, but ArcGIS has an older version of pandas.
      
    if pd_version >= 19:    
        interval_count = hr_intervals.resample(freq, closed = 'right', label = 'right').sum().dropna()
    elif pd_version < 19:
        interval_count = hr_intervals.resample(freq, how = "sum", closed = 'right', label = 'right').dropna()
    return interval_count


def duration_sum(inHDFFile, D, year_start, year_end, outHDFFile, complevel=9):
    """
    Calculate duration sum (Dauerstufe) of a defined time window D.
    The output time series will have the same frequency as the input data,
    but will contain the rolling sum of the defined time window with the label on the right,
    e.g. for D = 15 the time step at 10:15 contains the precipitation sum from 10:00 until 10:15 o'clock.
    Calculation can only be carried out for entire years since time windows between consecutive months are considered and included in calculations.
    Output data will be saved in a new HDF5 file with the same  monthly structure as the input data.
    Consequently, the duration sum data can be loaded and processed with the same functions as the other precipitation data stored in HDF5.

    :Parameters:
    ------------
    
    inHDFFile : string
        Path and name of the input HDF5 file containing precipitation data with a temporal resolution of 5 minutes.
    D : integer
        Duration (length of time window) in minutes. Value must be divisible by 5.
    year_start : integer
        First year for which duration sums are to be calculated.    
    year_end : integer
        Last year for which duration sums are to be calculated.
    outHDFFile : string
        Path and name of the output HDF5 file.
        If the specified HDF5 file already exists, the new dataset will be appended; if the HDF5 file doesn't exist, it will be created. 
    complevel : integer (optional, default: 9)
        defines the level of compression for the output HDF5 file.
        complevel may range from 0 to 9, where 9 is the highest compression possible.
        Using a high compression level reduces data size significantly,
        but writing data to HDF5 takes more time and data import from HDF5 is slighly slower.
        
    :Returns:
    ---------
    
        No return value
        
    """
    
    warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)


    months = [m for m in range(1,13)]
    years = [y for y in range(year_start, year_end+1)]
    freqYW = 5
    duration = '%smin' % D
    
    for year in years:
        for month in months:
                #---only for first month in first year: initiate process----------------
                if year == years[0] and month == months[0]:                    
                    # open outHDF, only month for which the previous month shall not be considered
                    # calculate number of intervals at end of month, which need to be passed to following month
                    # this only works for durations that can be divided by 5!
                    nIntervalsAtEndOfMonth = D/freqYW - 1
                    df = _core.load_month(HDFFile=inHDFFile, month=month, year=year)
                    # to be able to perform calculations on other than 5 min data in future: freq = df.index.freq
                    # set up rolling window of size=duration and calculate the sum of every window
                    # shift index 5 min forwards (to label = right). needed because index label is at beginning of 5 min interval in YW
                    # consequently, without shifting, the label describes the end of the duration interval - 5 minutes
                    durDF = df.rolling(duration).sum().shift(periods=1, freq = '5min')
                    HDFDataset = "%s/%s" %(year, month)
                    durDF.to_hdf(path_or_buf=outHDFFile, key=HDFDataset, mode="a", format="fixed", data_columns = True, index = True, complevel=complevel, complib="zlib")
                    del durDF
                    gc.collect()
                    print("%s-%s done!" %(year, month))
                    # continue in next loop iteration (next month) and skip remaining statements
                    continue
                #-----------------------------------------------------------------------    
                # Only keep end of month (e.g. last two intervals for D=15 min) and append next month to it
                df = df.iloc[-nIntervalsAtEndOfMonth: , ]
                df = df.append(_core.load_month(HDFFile=inHDFFile, month=month, year=year)).asfreq('5min')
                # rolling window of specified duration. sum is calculated for each window with label on the right (+5 minutes / shift(1), see above)
                # remove first intervals (number equal to the intervals taken from previous month) with incorrect results due to missing data (intervals contained in previous month)
                durDF = df.rolling(duration).sum().shift(periods=1, freq = '5min').iloc[nIntervalsAtEndOfMonth: , ]
                HDFDataset = "%s/%s" %(year, month)
                durDF.to_hdf(path_or_buf=outHDFFile, key=HDFDataset, mode="a", format="fixed", data_columns = True, index = True, complevel=complevel, complib="zlib")
                del durDF
                gc.collect()
                print("%s-%s done!" %(year, month))
                
                
                
                