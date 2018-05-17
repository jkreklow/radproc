# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2016-2018, Kreklow.
# Distributed under the MIT License. See LICENSE.txt for more info.

"""
=============================
 Core Functions and Data I/O
=============================

Core functions like coordinate conversion and import of ID-array from textfile. 
Data import from HDF5-file and temporal data aggregation.

.. autosummary::
   :nosignatures:
   :toctree: generated/

   coordinates_degree_to_stereographic
   save_idarray_to_txt
   import_idarray_from_txt
   load_months_from_hdf5
   load_month
   load_years_and_resample
   hdf5_to_years
   hdf5_to_months
   hdf5_to_days
   hdf5_to_hours
   hdf5_to_hydrologicalSeasons


.. module:: radproc.core
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module core
.. moduleauthor:: Jennifer Kreklow
"""

from __future__ import division, print_function
import numpy as np
import pandas as pd
import sys


def coordinates_degree_to_stereographic(Lambda_degree, Phi_degree):
    """
    Converts geographic coordinates [°] to cartesian coordinates [km] in stereographic RADOLAN projection.
    
    :Parameters:
    ------------
    
        Lambda_degree : float
            Degree of latitude [°N / °S]
        Phi_degree : Float
            Degree of longitude [°E / °W]
    
    :Returns:
    ---------
    
        (x, y) : Tuple with two elements of type float
            Cartesian coordinates x and y in stereographic projection [km]
            
    """
    
    from math import sin, cos, pi
    # Earth Radius in km
    R = 6370.04
    
    # Convert decimal degrees to radian
    Phi = Phi_degree * pi/180 
    Lambda = Lambda_degree * pi/180
    
    # Phi0 = 60°N --> Plane of projection subtends terrestrial sphere at 60°N 
    # Lambda0 = 10°E --> Cartesian coordinate system is aligned at 10°E meridian
    phi0 = 60 * pi/180
    lambda0 = 10 * pi/180
    # M = Stereographic Scaling Factor
    M = (1 + sin(phi0))/(1 + sin(Phi)) 
    
    x = R * M * cos(Phi) * sin(Lambda - lambda0)
    y = -R * M * cos(Phi) * cos(Lambda - lambda0)
    return (x, y)


def save_idarray_to_txt(idArr, txtFile):
    """
    Write cell ID values to text file.
    
    :Parameters:
    ------------
    
        idArr : one-dimensional numpy array
            containing ID values of dtype int32    
        txtFile : string
            Path and name of a new textfile to write cell ID values into. Writing format: One value per line.
    
    :Returns:
    ---------
    
        No return value
        
    """
    
    with open(txtFile, "w") as f:
        for ID in idArr:
            f.write("%i\n" %ID)


def import_idarray_from_txt(txtFile):
    """
    Imports cell ID values from text file into one-dimensional numpy-array.
    
    :Parameters:
    ------------
    
        txtFile : string
            Path to a textfile containing cell ID values. Format: One value per line.
    
    :Returns:
    ---------
    
        idArr : one-dimensional numpy-array of dtype int32
    """
    
    with open(txtFile, "r") as f:
        ID_list = []
        lines = f.readlines()

    for line in lines:
        ID_list.append(int(line))
    
    idArr = np.asarray(ID_list, dtype = np.int32)
    return idArr


  
def load_months_from_hdf5(HDFFile, year,  months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]):
    """
    Imports the specified months of one year and merges them to one DataFrame.

    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year : integer
            Year for which data are to be loaded.    
        months : list of integers (optional, default: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
            Months for which data are to be loaded.
                
    :Returns:
    ---------
    
        df : pandas DataFrame
    """
    
    with pd.HDFStore(HDFFile, "r") as f:
        # Dataset des ersten Monats in DataFrame importieren
        dataset = "%4i/%i" % (year,months[0])
        df = f[dataset]
        fr = df.index.freq
        # Datasets aller weiteren Monate importieren und an DataFrame anhängen
        for i in range(1,len(months)):
            dataset = "%4i/%i" % (year,months[i])
            df = df.append(f[dataset])
            df = df.asfreq(fr)
    
    return df


def load_month(HDFFile, year, month):
    """
    Imports the dataset of specified month from HDF5.

    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year : integer
            Year for which data are to be loaded.    
        month : integer
            Month for which data are to be loaded.
                
    :Returns:
    ---------
    
        df : pandas DataFrame
    """

    with pd.HDFStore(HDFFile, "r") as f:
        # Dataset des ersten Monats in DataFrame importieren
        dataset = "%4i/%i" % (year, month)
        df = f[dataset]
    
    return df


def load_years_and_resample(HDFFile, year_start, year_end=0, freq="years"):
    """Imports all months of the specified years, merges them together to one DataFrame \
    and resamples the latter to [annual | monthly | daily | hourly] precipitation sums. 
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer (optional, default: start_year)
            Last year for which data are to be loaded.
        freq : string (optional, default: "years")
            Target frequency.
            Available frequencies for downsampling:
                "years", "months", "days", "hours"
            
    :Returns:
    ---------
    
        df : pandas DataFrame
            resampled to the target frequency and containing [annual | monthly | daily | hourly] precipitation sums.
        
    
    :Examples:
    ----------
    
    The mean annual precipitation sum can be calculated with the following syntax:
            
        >>> import radproc as rp
        >>> meanPrecip = rp.load_years_and_resample(r"C:\Data\RADOLAN.h5", 2010, 2015, "years").mean()
        # The resulting pandas Series can be exported to an ESRI Grid:    
        >>> rp.export_to_raster(series=meanPrecip, idRaster=rp.import_idarray_from_raster(r"C:\Data\idras"), outRaster=r"P:\GIS_data\N_mean10_15")
    
    .. note::
        
    All resampling functions set the label of aggregated intervals at the right,
    hence every label describes the precipitation accumulated in the previous interval period.
    
    """  
    
    if freq.lower() == "years":
        frequency = 'A-DEC'
    elif freq.lower() == "months":
        frequency = 'M'
    elif freq.lower() == "days":
        frequency = 'D'
    elif freq.lower() == "hours":
        frequency = 'H'
    else:
        print('No valid frequency! Please enter one of the following arguments: \
        "years", "months", "days", "hours"')
        sys.exit()
        
    try:
        if year_end == 0 or (year_end != 0 and year_start > year_end):
            year_end = year_start
            print("year_end set to year_start.")
        years = np.arange(year_start, year_end + 1)
        
        with pd.HDFStore(HDFFile, "r") as f:
        
            pd_version = int(pd.__version__.split('.')[-2])
            
            for year in years:
                # Load dataset of first month into DataFrame
                dataset = "%4i/%i" % (year,1)
                df = f[dataset]
                #reduce data size by resampling
                if pd_version < 19 and frequency != 'A-DEC':
                    df = df.resample(frequency, how = 'sum', closed = 'right', label = 'right')
                elif pd_version >= 19 and frequency != 'A-DEC':
                    df = df.resample(frequency, closed = 'right', label = 'right').sum()
                # resample to months if years are target frequency
                elif pd_version < 19 and frequency == 'A-DEC':
                    df = df.resample('M', how = 'sum', closed = 'right', label = 'right')
                elif pd_version >= 19 and frequency == 'A-DEC':  
                    df = df.resample('M', closed = 'right', label = 'right').sum()
                
                # Load datasets of other months, resample and append to DataFrame of first month
                for month in range(2,13):
                    dataset = "%4i/%i" % (year,month)
                    dfm = f[dataset]
                    
                    if pd_version < 19 and frequency != 'A-DEC':
                        dfm = dfm.resample(frequency, how = 'sum', closed = 'right', label = 'right')
                    elif pd_version >= 19 and frequency != 'A-DEC':
                        dfm = dfm.resample(frequency, closed = 'right', label = 'right').sum()
                    # resample to months if years are target frequency
                    elif pd_version < 19 and frequency == 'A-DEC':
                        dfm = dfm.resample('M', how = 'sum', closed = 'right', label = 'right')
                    elif pd_version >= 19 and frequency == 'A-DEC':  
                        dfm = dfm.resample('M', closed = 'right', label = 'right').sum()                    
                    
                    df = df.append(dfm)
                    
                # Check for pandas version and apply appropriate syntax for resample method
                # to keep compatibility to older versions and avoid FutureWarnings in newer versions.
                if int(pd.__version__.split('.')[-2]) < 19:
                    df = df.resample(frequency, how = 'sum', closed = 'right', label = 'right')
                else:
                    df = df.resample(frequency, closed = 'right', label = 'right').sum()
                
                # for first year: copy to new year DataFrame
                if year == years[0]:
                    dfY = df.copy()
                    del df
                # for following years: append to year DataFrame
                else:
                    dfY = dfY.append(df)
            
            try:
                # set frequency
                dfY = dfY.asfreq(frequency)
            except ValueError:
                # for gauge data, "ValueError: cannot reindex from a duplicate axis" occurs, obviously due to duplicate index labels.
                # To avoid this, rows with duplicate labels are removed and only the first occurrence is kept.
                # the ~ operator reverses the boolean values from the duplicated method in order to keep only NOT duplicated labels.
                dfY = dfY[~dfY.index.duplicated(keep='first')]
                dfY = dfY.asfreq(frequency)
            
            # Years and months have default setting to set index at end of definded interval.
            # Day Index uses date of last interval (next day at ~6h) which is confusing. So shift index back to correct day.
            if frequency == 'D' and dfY.index.day[0] == 2:
                dfY.index = dfY.index.shift(-1)
            
        return dfY

    except IOError:
        print("Error! HDF5 file can not be opened!\n \
Please check if directory path is correct and file is currently used by any other application.")
    except KeyError:
        print('Error at %i/%i' %(year, month))
    except TypeError:
        print('Error! Please enter years as integer numbers and path to HDF5 file as string!\n \
Example: rp.load_years_and_resample(r"P:\User\Data\HDF5\RW.h5", 2008, 2010)')
    except UnboundLocalError:
        print('Error! Sorry, this function only works for entire years starting in January! \n \
To resample smaller time periods, you can import the months with load_months_from_hdf5() and resample them with df.resample()')
    except:
        print("An unexpected error occurred")
        raise


# Wrapper functions to faciliate resampling and avoid errors:
#------------------------------------------------------------    
def hdf5_to_years(HDFFile, year_start, year_end=0):
    """
    Wrapper for load_years_and_resample() to import all months of the specified years, merge them together to one DataFrame \
    and resample the latter to annual precipitation sums. 
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer (optional, default: start_year)
            Last year for which data are to be loaded.
            
    :Returns:
    ---------
    
        df : pandas DataFrame
            resampled to annual precipitation sums.
    """
    return load_years_and_resample(HDFFile, year_start, year_end, freq = "years")


def hdf5_to_months(HDFFile, year_start, year_end=0):
    """
    Wrapper for load_years_and_resample() to import all months of the specified years, merge them together to one DataFrame \
    and resample the latter to monthly precipitation sums. 
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer (optional, default: year_start)
            Last year for which data are to be loaded.
            
    :Returns:
    ---------
    
        df : pandas DataFrame
            resampled to monthly precipitation sums.
            
    .. note::
    
    All resampling functions set the label of aggregated intervals at the right,
    hence every label describes the precipitation accumulated in the previous interval period.
    
    """
    return load_years_and_resample(HDFFile, year_start, year_end, freq = "months")


def hdf5_to_days(HDFFile, year_start, year_end=0):
    """
    Wrapper for load_years_and_resample() to import all months of the specified years, merge them together to one DataFrame \
    and resample the latter to daily precipitation sums. 
    
    :Parameters:
    ------------
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer (optional, default: start_year)
            Last year for which data are to be loaded.
            
    :Returns:
    ---------
    
        df : pandas DataFrame
            resampled to daily precipitation sums.
            
    .. note::
        
    All resampling functions set the label of aggregated intervals at the right,
    hence every label describes the precipitation accumulated in the previous interval period.
    
    """
    return load_years_and_resample(HDFFile, year_start, year_end, freq = "days")


def hdf5_to_hours(HDFFile, year_start, year_end=0):
    """
    Wrapper for load_years_and_resample() to import all months of the specified years, merge them together to one DataFrame \
    and resample the latter to hourly precipitation sums. 
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year_start : integer
            First year for which data are to be loaded.    
        year_end : integer (optional, default: start_year)
            Last year for which data are to be loaded.
            
    :Returns:
    ---------
    
        df : pandas DataFrame
            resampled to hourly precipitation sums.
            
    .. note::
        
    All resampling functions set the label of aggregated intervals at the right,
    hence every label describes the precipitation accumulated in the previous interval period.
    
    .. note::
        
    For comparisons between hourly RW data and gauge data/YW data resampled to hours,
    keep in mind, that hours in RW always start at hh-1:50 whereas the resampled hours begin at hh:00.
    
    """
    return load_years_and_resample(HDFFile, year_start, year_end, freq = "hours")

#-----------------------------------------------------------------------------------

def hdf5_to_hydrologicalSeasons(HDFFile, year_start, year_end=0):
    """
    Calculates the precipitation sums of the hydrological summer and winter seasons (May - October and November - April).
    
    Imports all months of the specified years, resamples them to monthly precipitation sums, merges them together to one DataFrame \
    and resamples the latter to half-annual precipitation sums.
    Note: The Data are truncated to the period May of year_start to October of year_end before resampling! 
    
    :Parameters:
    ------------
    
        HDFFile : string
            Path and name of the HDF5 file containing monthly datasets.
        year_start : integer
            First year for which data are to be loaded. The months January to April of this year are not contained in the precipitation sums!    
        year_end : integer (optional, default: start_year)
            Last year for which data are to be loaded. The months November and December of this year are not contained in the precipitation sums!
            
    :Returns:
    ---------
    
        df : pandas DataFrame
            resampled to precipitation sums of hydrological summer and winter seasons.
            In contrast to most other resampling functions from radproc, the index labels the beginning of each resampling period,
            e.g. the index 2001-05-01 describes the period from May to October 2001.
            
    .. note::
        
    All resampling functions set the label of aggregated intervals at the right,
    hence every label describes the precipitation accumulated in the previous interval period.
    
    """
    if year_end == 0 or (year_end != 0 and year_start > year_end):
        year_end = year_start
        print("year_end set to year_start.")
    
    dfm = hdf5_to_months(HDFFile, year_start, year_end)
    dfm = dfm.truncate('%i-05' % year_start,'%i-10' % year_end)
    
    # Check for pandas version and apply appropriate syntax for resample method
    # to keep compatibility to older versions and avoid FutureWarnings in newer versions.
    if int(pd.__version__.split('.')[-2]) < 19:
        df = dfm.resample('2QS-MAY', how = 'sum', label = 'left')
    else:
        df = dfm.resample('2QS-MAY', label = 'left').sum()
        
    return df
        
        
        
        