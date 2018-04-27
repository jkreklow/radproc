# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2016-2017, Kreklow.
# Distributed under the MIT License. See LICENSE.txt for more info.

"""
Heavy rainfall and erosivity analysis
=====================================

Module for heavy rainfall and erosivity analysis.

.. autosummary::
   :nosignatures:
   :toctree: generated/

   calc_I30
   calc_R_factor
   monthly_R_factor
   annual_R_factor
   annual_R_factor_gauge
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


def calc_I30(NArr, freq_min):
    """
    Calculates maximum 30-minutes intensity I30.
    
    :Parameters:
    ------------
    
        NArr : one-dimensional numpy-array
            containing a the time series of an erosive rain as float values.
        freq_min : integer
            Frequency of precipitation time series in minutes.
        
    Returns
    -------
        I30 : float
            maximum 30-minutes intensity I30
    """
    
    # frequency value: <5 * Minutes>
    if freq_min == 60:
        I30 = np.nanmax(NArr)
    else:
        window = 30/freq_min
        # if rain lasts up to 30 min: I30 = sum * 2
        if len(NArr) <= window:
            I30 = np.nansum(NArr)
        else:
            I30 = np.nansum(NArr[0:window])
            for i in xrange(1, len(NArr)-window+1):
                N30 = np.nansum(NArr[i:i+window])
                if N30 > I30:
                    I30 = N30
        I30 *= 2
    return I30




def calc_R_factor(column, freq_min, max_nan_days): # Column has to be 1D-Array for numba!  Can be created by series.values
    """
    Calculates R-factor [kJ/m^2 * mm/h] and number of erosive rains for precipitation time series of one column (raster cell or gauge).
    
    :Parameters:
    ------------
    
        column : one-dimensional numpy-array
            containing a precipitation time series as float values.
            The length of the time series (array) defines the temporal resolution of the output,
            e.g. an array covering one year will result in an annual R-factor for this year.
        freq_min : integer
            Frequency of precipitation time series in minutes.    
        max_nan_days : integer
            Maximum number of days without precipitation values.
            If number of NoData intervals equal to the specified number of days is exceeded, return values are set to NaN.
                
    :Returns:
    ---------
    
        (R, n_rains) : Tuple
            containing R-Factor [kJ/m^2 * mm/h] as float value
            and number of erosive rains as integer value.
    
    .. _calc_R_factor:    
    :Notes:
    -------
    
    Calculations according to Schwertmann et al. (1990).
    
    Definition erosive rain:
        Precipitation sum >= 10 mm or maximum I30 intensity > 10 mm/h.
        Rains separated by less than six hours are regarded as one rain.
        
    Definition R-factor:
        Sum of all products E * I30 for all erosive rains in specified time period with
            * E = cumulated kinetic energy density [kJ/m^2] of erosive rain and
            * I30 = maximum 30-minutes precipitation intensity, which is doubled to obtain mm/h 
    """
    
    global _numba_available
    #for date, value in column.iteritems():
    i = 0
    R = 0.0
    n_rains = 0
    # number of intervals equal to 6 hours
    six_hours = 6 * 60/freq_min
    # number of intervals equal to 30 minutes window
    window = 30/freq_min
    # number of intervals equal to maximum allowed NaN days
    max_nan_intervals = max_nan_days * (60/freq_min) * 24
    
    # if number of NoData intervals equal to the specified number of days is exceeded,
    # return values are set to NaN and all calculations skipped.
    if np.isnan(column).sum() > max_nan_intervals:
        R = np.nan
        n_rains = np.nan
    else:
        #---outer loop--------
        while i < len(column):            
            if column[i] > 0.0:
                #start_time = column.index[i] # alternative pandas version to keep dates
                # save start time (index) of first precipitation
                start_time = i
                rain_pause = 0
                
                #---inner loop (during rain events)------------------------
                # loop here within rain event. Loops stops six hours after last rain and function jumps to R-factor calculation.
                while rain_pause <= six_hours:
                    # raise i here instead of outer loop to get next precipitation value
                    i += 1
                    # if i reaches end of array: end inner loop
                    if i == len(column):
                        rain_pause = six_hours
                    # if rain occurs: reset rain pause variable to 0
                    elif column[i] > 0.0:
                        rain_pause = 0
                    # if no rains occurs: raise rain pause by 1
                    else:
                        rain_pause += 1
                        
                #---end of inner loop------------------------------------------
                
                # continue here after rain event (rain pause == six hours) 
                # create view of last rain event to calculate R-factor
                # i - six hours --> cut off the zero values after end of rain and reduce amount of following calculations
                end_time = i - six_hours
                N = column[start_time:end_time]
                E = 0
                I30 = 0
                
                # this check is needed to prevent ValueErrors on empty arrays in case there aren't any erosive rains 
                if len(N) > 0:
                    # if frequency of time series is 60 minutes, I30 is the maximum value of the rain (No doubling because unit is already mm/h))
                    if freq_min == 60:
                        I30 = np.nanmax(N)
                    else:
                        
                        # if rain lasts up to 30 min: I30 = precipitation sum * 2
                        if len(N) <= window:
                            I30 = np.nansum(N)
                        else:
                            # "rolling window" calculation of 30 minutes precipitation sum,
                            # highest sum is saved and doubled to obtain I30
                            I30 = np.nansum(N[0:window])
                            for k in xrange(1, len(N)-window+1):
                                N30 = np.nansum(N[k:k+window])
                                if N30 > I30:
                                    I30 = N30
                        I30 *= 2
                    
                # Check if rain is erosive. If not, skip and continue in outer while-loop.
                # Additional condition I30 <= 40 can be set to remove outliers with return interval > 30 years
                # According to KOSTRA this threshold can be at about 40 mm/h    
                    if ((I30 > 10) or (np.nansum(N) >= 10.0)) and I30 <= 40:
                    # rain is erosive, raise n_rains by one and calculate R-factor
                        n_rains += 1
                        for j in xrange(0, len(N)):
                            # calculate intensity I in mm/h
                            I = N[j] * (60/freq_min)
                            if ((I > 0.05) and (I < 76.2)):
                            # log(z)- natürlicher Logarithmus von z im math Modul
                                E += (11.89 + 8.73 * math.log10(I)) * N[j] * (10**(-3))
                            elif (N[j] >= 76.2):
                                E += 28.33 * N[j] * (10**(-3))
                        # at end of every erosive rain:
                        # calculate E * I30 for this rain and add product to total R
                        R += E * I30
                        
            # -----continue outer loop------------------------------
            # if column[i] == 0: no calculations, just raise i by one        
            i += 1
        
    return R, n_rains



# try to import numba and do just-in-time compilation of function calc_R_factor to machine code
# compiled function accelerates processing speed by factor 100 to 1000 but is not compatible to ArcGIS!
# if numba is not available, the functions defined below use the uncompiled and much slower function.
try:
    from numba import jit
    #calc_I30_jit = jit(calc_I30)
    calc_R_factor_jit = jit(calc_R_factor)
    _numba_available = True
except:
    _numba_available = False
    


def monthly_R_factor(HDFFile, year_start, year_end, max_nan_days):
    """
    Calcutes the monthly mean R-factor and number of erosive rains for precipitation data stored as monthly pandas DataFrames in a HDF5 file.
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly pandas DataFrames with precipitation data.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer
            Last year for which data are to be loaded.   
        max_nan_days : integer
            Maximum number of days without precipitation values.
            If number of NoData intervals equal to the specified number of days is exceeded, return values are set to NaN.
                
    :Returns:
    ---------
    
        (RmonthmeanDF, NmonthmeanDF) : tuple with two DataFrame objects of shape (12, n_columns)
            containing mean monthly R-Factors [kJ/m^2 * mm/h] as float value for each month and column (raster cell or gauge) of input DataFrames
            and number of erosive rains as integer value for each column.
        
    :Notes:
    -------
    
    See documentation of function calc_R_factor_ for further details on calculation method and definitions.
    
    :Examples:
    ----------
    
    >>> import radproc as rp
    >>> Rm, Nm = rp.monthly_R_factor(HDFFile="P:/Data/HDF5/RW_rea.h5", year_start=2011, year_end=2014, max_nan_days=30)
    # export mean R-factor for June to raster:
    >>> rp.export_to_raster(series=Rm.loc[6,:], idRaster="P:/Data/GIS_Data/radproc_GIS/radproc_data.gdb/idras", outRaster="P:/Data/GIS_Data/R_june")
    # calculate mean percentage share of every month on total R-factor and visualize as barplot
    >>> perc = Rm.mean(1)/Rm.mean(1).sum() * 100
    >>> perc.plot(kind='bar')
    # calculate percentage share of every month on total R-factor for each column
    >>> percDF = Rm/Rm.sum() * 100
    """
    
    global _numba_available

    if year_start > year_end:
        year_end = year_start
        
    # create numpy-arrays of years and months    
    years = np.arange(year_start, year_end + 1)
    months = np.arange(1, 13)
    # Load dataframe of first month to get shape and frequency information
    df = _core.load_months_from_hdf5(HDFFile = HDFFile, year = years[0],  months = [months[0]])
    # create empty output DataFrames: one row per month, same number of columns and column names as input DataFrame
    RmonthmeanDF = pd.DataFrame(np.empty((len(months),df.shape[1])), index = months, columns = df.columns)
    NmonthmeanDF = pd.DataFrame(np.empty((len(months),df.shape[1])), index = months, columns = df.columns)
    # read out frequency of input DataFrame and convert to minutes
    freq_min = df.index.freq.delta.seconds/60
    
    # for every month...
    for month in months:
        # for every year... (First, january is loaded for every year, mean R and number of rains in this month are calculated. Second, february...)
        # initialize accumulation array with zeros, length equal to number of columns
        Rsum = np.zeros(df.shape[1], dtype=np.float32)
        Nsum = np.zeros(df.shape[1], dtype=np.float32)
        for year in years:
            df = _core.load_months_from_hdf5(HDFFile = HDFFile, year = year,  months = [month])
            # if numba is available use compiled function for R-factor calculation, else use normal function
            # function is vectorized and applied to all columns of input DataFrame concurrently and independently
            # Note: input has to be a two-dimensional numpy-array and must NOT be a DataFrame! --> df.values
            # output variables R and N are arrays with one value per input column
            if _numba_available == True:
                R, N = np.apply_along_axis(calc_R_factor_jit, 0, df.values, freq_min, max_nan_days)
            else:
                R, N = np.apply_along_axis(calc_R_factor, 0, df.values, freq_min, max_nan_days)
            # add resulting arrays to sum arrays
            Rsum += R
            Nsum += N
            
        #---end of inner (year) loop------------
        # after last year calculate mean R and N arrays for current month
        # and insert resulting mean arrays in output DataFrames as rows for the corresponding month
        Rmean = Rsum / len(years)
        Nmean = Nsum / len(years)
        RmonthmeanDF.loc[month,:] = Rmean
        NmonthmeanDF.loc[month,:] = Nmean
            
    return RmonthmeanDF, NmonthmeanDF
            

#DEPRECATED due to data size, calculation of R factor for entire years only possible for small areas or short periods
# Alternative function for YW needed with less data at the same time!       
def annual_R_factor_whole_years(HDFFile, year_start, year_end, max_nan_days):
    """
    Calcutes the annual R-factor and number of erosive rains **for precipitation data stored as monthly pandas DataFrames** in a HDF5 file.
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly pandas DataFrames with precipitation data.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer
            Last year for which data are to be loaded.   
        max_nan_days : integer
            Maximum number of days without precipitation values.
            If number of NoData intervals equal to the specified number of days is exceeded, return values are set to NaN.
                
    :Returns:
    ---------
    
        (RannualDF, NannualDF) : tuple with two DataFrame objects of shape (n_years, n_columns)
            containing annual R-Factors [kJ/m^2 * mm/h] as float value for each year and column (raster cell or gauge) of input DataFrames
            and number of erosive rains as integer value for each year and column.
        
    :Notes:
    -------
        See documentation of function calc_R_factor_ for further details on calculation method and definitions.
    
    :Examples:
    ----------
    
    >>> import radproc as rp
    >>> Ra, Na = rp.annual_R_factor(HDFFile=r"P:\Data\HDF5\RW_rea.h5", year_start=2011, year_end=2014, max_nan_days=30)
    # export mean annual R-factor to raster:
    >>> rp.export_to_raster(series=Ra.mean(), idRaster=r"P:\Data\GIS_Data*\radproc_GIS*\radproc_data.gdb\idras", outRaster=r"P:\Data\GIS_Data\R_mean")
    """
    
    global _numba_available
    if year_start > year_end:
        year_end = year_start
    
    # create numpy-arrays of years and months    
    years = np.arange(year_start, year_end + 1)
    months = np.arange(1, 13)
    # Load and merge monthly dataframes of first year to get shape and frequency information
    df = _core.load_months_from_hdf5(HDFFile = HDFFile, year = years[0], months = months)
    # create empty output DataFrames: one row per year, same number of columns and column names as input DataFrame
    RannualDF = pd.DataFrame(np.empty((len(years),df.shape[1])), index = years, columns = df.columns)
    NannualDF = pd.DataFrame(np.empty((len(years),df.shape[1])), index = years, columns = df.columns)
    # read out frequency of input DataFrame and convert to minutes
    freq_min = df.index.freq.delta.seconds/60
    
    for year in years:
        # don't load DataFrame of first year again
        if year != years[0]:
            df = _core.load_months_from_hdf5(HDFFile = HDFFile, year = year, months = months)
        # if numba is available use compiled function for R-factor calculation, else use normal function
        # function is vectorized and applied to all columns of input DataFrame concurrently and independently
        # Note: input has to be a two-dimensional numpy-array and must NOT be a DataFrame! --> df.values
        # output variables R and N are arrays with one value per input column
        if _numba_available == True:
            R, N = np.apply_along_axis(calc_R_factor_jit, 0, df.values, freq_min, max_nan_days)
        else:
            R, N = np.apply_along_axis(calc_R_factor, 0, df.values, freq_min, max_nan_days)
        
        # insert resulting arrays in output DataFrames as rows for the corresponding year
        RannualDF.loc[year,:] = R
        NannualDF.loc[year,:] = N
            
    return RannualDF, NannualDF
#---------------------------------------------------------------------------


def annual_R_factor(HDFFile, year_start, year_end, max_nan_days):
    """
    Calcutes the annual R-factor and number of erosive rains **for precipitation data stored as monthly pandas DataFrames** in a HDF5 file.
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly pandas DataFrames with precipitation data.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer
            Last year for which data are to be loaded.   
        max_nan_days : integer
            Maximum number of days without precipitation values.
            If number of NoData intervals equal to the specified number of days is exceeded, return values are set to NaN.
                
    :Returns:
    ---------
    
        (RannualDF, NannualDF) : tuple with two DataFrame objects of shape (n_years, n_columns)
            containing annual R-Factors [kJ/m^2 * mm/h] as float value for each year and column (raster cell or gauge) of input DataFrames
            and number of erosive rains as integer value for each year and column.
        
    :Notes:
    -------
        See documentation of function calc_R_factor_ for further details on calculation method and definitions.
    
    :Examples:
    ----------
    
    >>> import radproc as rp
    >>> Ra, Na = rp.annual_R_factor(HDFFile=r"P:\Data\HDF5\RW_rea.h5", year_start=2011, year_end=2014, max_nan_days=30)
    # export mean annual R-factor to raster:
    >>> rp.export_to_raster(series=Ra.mean(), idRaster=r"P:\Data\GIS_Data*\radproc_GIS*\radproc_data.gdb\idras", outRaster=r"P:\Data\GIS_Data\R_mean")
    """
    
    global _numba_available
    if year_start > year_end:
        year_end = year_start
    
    # create numpy-arrays of years and months    
    years = np.arange(year_start, year_end + 1)
    months = np.arange(1, 13)
    max_nan_days = max_nan_days/12
    # Load and merge monthly dataframes of first year to get shape and frequency information
    df = _core.load_month(HDFFile = HDFFile, year = years[0], month = months[0])
    # create empty output DataFrames: one row per year, same number of columns and column names as input DataFrame
    RannualDF = pd.DataFrame(np.empty((len(years),df.shape[1])), index = years, columns = df.columns)
    NannualDF = pd.DataFrame(np.empty((len(years),df.shape[1])), index = years, columns = df.columns)
    # read out frequency of input DataFrame and convert to minutes
    freq_min = df.index.freq.delta.seconds/60
    
    for year in years:
        if year != years[0]:
            df = _core.load_month(HDFFile = HDFFile, year = year, month = months[0])
        # if numba is available use compiled function for R-factor calculation, else use normal function
        # function is vectorized and applied to all columns of input DataFrame concurrently and independently
        # Note: input has to be a two-dimensional numpy-array and must NOT be a DataFrame! --> df.values
        # output variables R and N are arrays with one value per input column
        if _numba_available == True:
            Ryear, Nyear = np.apply_along_axis(calc_R_factor_jit, 0, df.values, freq_min, max_nan_days)
        else:
            Ryear, Nyear = np.apply_along_axis(calc_R_factor, 0, df.values, freq_min, max_nan_days)
        
        
        for month in months[1:]:
            df = _core.load_month(HDFFile = HDFFile, year = year, month = month)

            if _numba_available == True:
                R, N = np.apply_along_axis(calc_R_factor_jit, 0, df.values, freq_min, max_nan_days)
            else:
                R, N = np.apply_along_axis(calc_R_factor, 0, df.values, freq_min, max_nan_days)
            Ryear += R
            Nyear += N
        
        # insert resulting arrays in output DataFrames as rows for the corresponding year
        RannualDF.loc[year,:] = Ryear
        NannualDF.loc[year,:] = Nyear
            
    return RannualDF, NannualDF



def annual_R_factor_gauge(HDFFile, dataset_path, year_start, year_end, max_nan_days):
    """
    Calcutes the annual R-factor and number of erosive rains **for precipitation data stored as one single pandas DataFrame** in a HDF5 file.
    
    Usually only usable for rain gauge data due to huge DataFrame size.
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing the pandas DataFrame with precipitation data.
        dataset_path : string
            Path and name of dataset (DataFrame) which is to be loaded from HDF5 file.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer
            Last year for which data are to be loaded.   
        max_nan_days : integer
            Maximum number of days without precipitation values.
            If number of NoData intervals equal to the specified number of days is exceeded, return values are set to NaN.
                
    :Returns:
    ---------
    
        (RannualDF, NannualDF) : tuple with two DataFrame objects of shape (n_years, n_columns)
            containing annual R-Factors [kJ/m^2 * mm/h] as float value for each year and column (raster cell or gauge) of input DataFrame
            and number of erosive rains as integer value for each year and column.
        
    :Notes:
    -------
    
    See documentation of function calc_R_factor_ for further details on calculation method and definitions.
    
    :Examples:
    ----------
    
    >>> import radproc as rp
    >>> Ra, Na = rp.annual_R_factor_gauge(HDFFile=r"P:\Data\HDF5\Gauge_data.h5", dataset_path="all_gauges/freq5min", year_start=2011, year_end=2014, max_nan_days=30)
    # mean annual R-factor:
    >>> Ra.mean()
    """
    
    global _numba_available

    if year_start > year_end:
        year_end = year_start
    
    # load DataFrame from HDF5 file
    f = pd.HDFStore(HDFFile, "r")
    df = f[dataset_path]
    f.close()
    
    years = np.arange(year_start, year_end + 1)
    # truncate DataFrame to selected years
    df = df[str(years[0]):str(years[-1])]
    # create empty output DataFrames: one row per year, same number of columns and column names as input DataFrame
    RannualDF = pd.DataFrame(np.empty((len(years),df.shape[1])), index = years, columns = df.columns)
    NannualDF = pd.DataFrame(np.empty((len(years),df.shape[1])), index = years, columns = df.columns)
    # read out frequency of input DataFrame and convert to minutes
    freq_min = df.index.freq.delta.seconds/60
    
    for year in years:
        # if numba is available use compiled function for R-factor calculation, else use normal function
        # function is vectorized and applied to all columns of input DataFrame concurrently and independently
        # Note: input has to be a two-dimensional numpy-array and must NOT be a DataFrame! --> df.values
        # output variables R and N are arrays with one value per input column
        if _numba_available == True:
            R, N = np.apply_along_axis(calc_R_factor_jit, 0, df[str(year)].values, freq_min, max_nan_days)
        else:
            R, N = np.apply_along_axis(calc_R_factor, 0, df[str(year)].values, freq_min, max_nan_days)
        
        # insert resulting arrays in output DataFrames as rows for the corresponding year
        RannualDF.loc[year,:] = R
        NannualDF.loc[year,:] = N

    return RannualDF, NannualDF


def _exceeding(rowseries, thresholdValue, minArea):
    minYcellsgreqXmm_bool = np.count_nonzero(rowseries >= thresholdValue) > minArea
    return minYcellsgreqXmm_bool


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
