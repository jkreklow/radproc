# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2016-2018, Kreklow.
# Distributed under the MIT License. See LICENSE.txt for more info.

"""
Heavy Rainfall Analysis
=======================

Module for heavy rainfall analysis.

.. autosummary::
   :nosignatures:
   :toctree: generated/

   find_heavy_rainfalls
   count_heavy_rainfall_intervals
   
   
.. module:: radproc.heavyrain
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module heavyrain
.. moduleauthor:: Jennifer Kreklow

"""


import pandas as pd
import numpy as np
import math
import radproc.core as _core
import gc





def find_heavy_rainfalls_old(HDFFile, year_start, year_end, thresholdValue, minArea, season):
    """
    Creates a DataFrame containing all heavy rainfalls (intervals) exceeding a specified threshold intensity value.
    
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
            Minimum area where intensity threshold value has to be exceeded.
        season : string or list
            Season / Time period to analyse. Can be a list with integer values from 1 to 12 or a string describing the season. The following strings are possible:
            ["Year" | "April - September" | "October - March" | "January/December" | "Jan" | "Feb" | "Mar" | "Apr" | "May" | "Jun" | "Jul" | "Aug" | "Sep" | "Oct" | "Nov" | "Dec"]
    
    
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
    df = _core.load_months_from_hdf5(HDFFile=HDFFile, year=years[0], months=months)
    exceedances = df.apply(_exceeding, axis = 1, args=(thresholdValue, minArea)) #Anzahl Überschreitungen pro Stundenraster
    heavy_rains = df.loc[exceedances == True]
    #exceedances = np.sum(df >= thresholdValue, axis = 0)
    for year in years[1:]:
        df = _core.load_months_from_hdf5(HDFFile=HDFFile, year=year, months=months)
        exceedances = df.apply(_exceeding, axis = 1, args=(thresholdValue, minArea))
        #try to append dataframe with identified heavy rainfall intervals
        try:
            heavy_rains = heavy_rains.append(df.loc[exceedances == True])
        # for the first year, heavy_rains is not yet defined, which causes a NameError. In this case, a new DataFrame is created instead of appending data.
        except NameError:
            heavy_rains = df.loc[exceedances == True]
            
    return heavy_rains


def find_heavy_rainfalls(HDFFile, year_start, year_end, thresholdValue, minArea, season):
    """
    Creates a DataFrame containing all heavy rainfalls (intervals) exceeding a specified threshold intensity value.
    
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
            Minimum area where intensity threshold value has to be exceeded.
        season : string or list
            Season / Time period to analyse. Can be a list with integer values from 1 to 12 or a string describing the season. The following strings are possible:
            ["Year" | "April - September" | "October - March" | "January/December" | "Jan" | "Feb" | "Mar" | "Apr" | "May" | "Jun" | "Jul" | "Aug" | "Sep" | "Oct" | "Nov" | "Dec"]
    
    
    :Returns:
    ---------
    
        heavy_rains : pandas DataFrame
            containing all intervals meeting the given criteria.
    """
    if season == "Year":
        months = [1,2,3,4,5,6,7,8,9,10,11,12]
    elif season == "April - September":
        months = [4,5,6,7,8,9]
    elif season == "October - March":
        months = [1,2,3,10,11,12]
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
            ["Year" | "April - September" | "October - March" | "January/December" | "Jan" | "Feb" | "Mar" | "Apr" | "May" | "Jun" | "Jul" | "Aug" | "Sep" | "Oct" | "Nov" | "Dec"]
    
    
    :Returns:
    ---------
    
        interval_count : pandas DataFrame
            containing the sum of all intervals meeting the given criteria.
            Temporal resolution depending on the given season.
    """

    #Define frequency for data aggregation depending on selected season
    if season == "Year" or season == [1,2,3,4,5,6,7,8,9,10,11,12]:
        freq = "A-DEC"
    elif season == "April - September":
        freq = "A-SEP"
    elif season == "October - March":
        freq = "A-MAR"
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
    # Calculate the sum of exceedances per cell in the given time period by resampling.
    # Choose syntax for resample method depending on pandas version. how = "sum" is deprecated in newer version, but ArcGIS has an older version of pandas.    
    if pd_version >= 19:    
        interval_count = hr_intervals_bool.resample(freq, closed = 'right', label = 'right').sum().dropna()
    elif pd_version < 19:
        interval_count = hr_intervals_bool.resample(freq, how = "sum", closed = 'right', label = 'right').dropna()
    return interval_count


#if __name__ == '__main__':
    #import radproc.arcgis as _arcgis
    #Rg, Ng = annual_R_factor_gauge(HDFFile=r"P:\JENNY\FORSCHUNG\Daten\HDF5\Ombrometer.h5", dataset_path="gesamt/freq5min", year_start=2001, year_end=2015, max_nan_days=30)
    #R, N = annual_R_factor(HDFFile=r"P:\JENNY\FORSCHUNG\Daten\HDF5\RW_rea.h5", year_start=2001, year_end = 2014, max_nan_days=30)
    #_arcgis.export_dfrows_to_gdb(dataDF=R, idRaster=r"P:\JENNY\FORSCHUNG\Daten\GIS_Daten\Basisdaten\radproc_GIS\radproc_data.gdb\idras_hessen", outGDBPath=r"P:\JENNY\FORSCHUNG\Daten\GIS_Daten\R_Faktor", GDBName="R_annual_0114")
    #Rm, Nm = monthly_R_factor(HDFFile=r"P:\JENNY\FORSCHUNG\Daten\HDF5\RW_rea.h5", year_start=2011, year_end = 2014, max_nan_days=30)
    #_arcgis.export_rows_to_gdb(dataDF=Rm/Rm.sum() * 100, idRaster=r"P:\JENNY\FORSCHUNG\Daten\GIS_Daten\Basisdaten\radproc_GIS\radproc_data.gdb\idras_hessen", outGDBPath=r"P:\JENNY\FORSCHUNG\Daten\GIS_Daten\R_Faktor", GDBName="Rpercentage_1114")
