# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2016-2018, Kreklow.
# Distributed under the MIT License. See LICENSE.txt for more info.

"""
Classification
==============

Module for classification of precipitation intervals.

.. autosummary::
   :nosignatures:
   :toctree: generated/

    FUNCS
   
   
.. module:: radproc.classification
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module classification
.. moduleauthor:: Jennifer Kreklow

"""


import pandas as pd
import numpy as np
import radproc.core as _core
import gc
from datetime import datetime


def classification_hours(value):
    if value == 0:
        return '0'
    elif pd.isnull(value):
        return 'NaN'
    elif value < 1:
        return '0.01 - 0.99'
    elif value < 2:
        return '1.00 - 1.99'
    elif value < 3:
        return '2.00 - 2.99'
    elif value < 4:
        return '3.00 - 3.99'
    elif value < 5:
        return '4.00 - 4.99'
    elif value < 6:
        return '5.00 - 5.99'
    elif value < 7:
        return '6.00 - 6.99'
    elif value < 8:
        return '7.00 - 7.99'
    elif value < 9:
        return '8.00 - 8.99'
    elif value < 10:
        return '9.00 - 9.99'
    elif value < 15:
        return '10.00 - 14.99'
    elif value < 20:
        return '15.00 - 19.99'
    elif value < 40:
        return '20.00 - 39.99'
    elif value >= 40:
        return '>= 40'
    
    
def classification_5min(value):
    if value == 0:
        return '0'
    elif pd.isnull(value):
        return 'NaN'
    elif value < 1:
        return '0.01 - 0.99'
    elif value < 2:
        return '1.00 - 1.99'
    elif value < 3:
        return '2.00 - 2.99'
    elif value < 4:
        return '3.00 - 3.99'
    elif value < 5:
        return '4.00 - 4.99'
    elif value < 6:
        return '5.00 - 5.99'
    elif value < 7:
        return '6.00 - 6.99'
    elif value < 8:
        return '7.00 - 7.99'
    elif value < 9:
        return '8.00 - 8.99'
    elif value < 10:
        return '9.00 - 9.99'
    elif value < 15:
        return '10.00 - 14.99'
    elif value < 20:
        return '15.00 - 19.99'
    elif value < 40:
        return '20.00 - 39.99'
    elif value >= 40:
        return '>= 40'
    
    
def classify_df(precDF, freq):
    #set classification frequency and function
    if freq == 60*pd.offsets.Minute() or freq == 'H':
        #classifyFunction = classifyHours
        # downsampling of data with higher temporal resolution
        if precDF.index.freq < 60*pd.offsets.Minute() and freq == 60*pd.offsets.Minute():
            precDF = precDF.resample('H').sum()
        classDF = precDF.applymap(classification_hours)
            
    elif freq == 5*pd.offsets.Minute() or freq == '5min':
        classDF = precDF.applymap(classification_5min)
        
    
    
    #leeren DataFrame mit allen Klassen einfügen, andernfalls werden nur die im ersten DF vorhandenen Klassen addiert!!!
    index = list(np.unique(classDF.values))
    #try:
        #index.remove('0')
        #index.remove('NaN')
    #except:
        #pass

    #Summe der Niederschläge für jede Klasse ermitteln und in Series abspeichern
    cells = {}
    for Class in index:
        cells[Class] = precDF[classDF==Class].sum(axis=0).fillna(0)

    classifiedPrecDepth = pd.DataFrame(cells).T
    classifiedPrecDuration = classDF.apply(pd.value_counts).fillna(0)
    return classifiedPrecDepth, classifiedPrecDuration


def summarize_columns(classifiedPrecDepth, classifiedPrecDuration, freq='H', dropna=True, percentage=True):
        
    durationSum = classifiedPrecDuration.sum(axis=1)
    depthSum = classifiedPrecDepth.sum(axis=1)
    
    if dropna == True:
        try:
            durationSum = durationSum.drop(['0','NaN'], axis = 0)
            depthSum = depthSum.drop(['0','NaN'], axis = 0)
        except:
            pass
        
    if percentage == True:
        durationSum = durationSum/durationSum.sum()*100
        depthSum = depthSum/depthSum.sum()*100
        
    return depthSum, durationSum



def classification(HDFFile, year_start, year_end, months=list(np.arange(1,13)), freq='H', dropna=True, percentage=True, dataSelection=[]):
    years = np.arange(year_start, year_end + 1)
    classLabels_hour = ['0', '0.01 - 0.99', '1.00 - 1.99', '2.00 - 2.99', '3.00 - 3.99', '4.00 - 4.99', '5.00 - 5.99', '6.00 - 6.99',\
'7.00 - 7.99', '8.00 - 8.99', '9.00 - 9.99', '10.00 - 14.99', '15.00 - 19.99', '20.00 - 39.99', '>= 40', 'NaN']
    #classLabels_5min = [TO DO]

    if freq == 60*pd.offsets.Minute() or freq == 'H': 
        classLabels = classLabels_hour
        
    # create empty output DataFrames
    df = _core.load_month(HDFFile = HDFFile, year = years[0], month = months[0])
    spatialPrecDepthSum = pd.DataFrame(np.zeros((len(classLabels),df.shape[1])), index = classLabels, columns = df.columns)
    spatialPrecDurationSum = pd.DataFrame(np.zeros((len(classLabels),df.shape[1])), index = classLabels, columns = df.columns)
    
    dummyStart = datetime(years[0]-1,months[0],1).strftime('%Y-%m-%d')
    temporalPrecDepthSum = pd.DataFrame(np.zeros((len(classLabels),1)), index = classLabels, columns = [dummyStart])
    temporalPrecDurationSum = pd.DataFrame(np.zeros((len(classLabels),1)), index = classLabels, columns = [dummyStart])
    
    for year in years:
        for month in months:
            # Load data for one month
            df = _core.load_month(HDFFile = HDFFile, year = year, month = month)
            
            if len(dataSelection) > 0:
                try:
                    df = df[dataSelection]
                except:
                    print "dataSelection failed! Please pass a list with suitable column names, e.g. an ID-Array or a list of gauge names!"
                    raise
            
            # calculate everything: classify intervals,calculate number of intervals per class (duration) and precipitation sum per class (depth)
            # once as detailed spatial information for raster export, once as an aggregated areal sum
            classifiedPrecDepth, classifiedPrecDuration = classify_df(df, freq)            
            depthArealSum, durationArealSum = summarize_columns(classifiedPrecDepth, classifiedPrecDuration, freq, dropna, percentage)
            
            if dropna == True:
                try:
                    classifiedPrecDepth = classifiedPrecDepth.drop(['0','NaN'], axis = 0)
                    classifiedPrecDuration = classifiedPrecDuration.drop(['0','NaN'], axis = 0)
                except:
                    pass
        
            if percentage == True:
                classifiedPrecDepth = classifiedPrecDepth/classifiedPrecDepth.sum(axis=0)*100
                classifiedPrecDuration = classifiedPrecDuration/classifiedPrecDuration.sum(axis=0)*100
            
            # Add results to output DataFrames
            spatialPrecDepthSum = spatialPrecDepthSum.add(other = classifiedPrecDepth, fill_value = 0)
            spatialPrecDurationSum = spatialPrecDurationSum.add(other = classifiedPrecDuration, fill_value = 0)
            
            temporalPrecDepthSum[datetime(year, month,1)] = depthArealSum
            temporalPrecDurationSum[datetime(year, month,1)] = durationArealSum
            

            
            print "%i-%i done!" %(year, month)
            del df, classifiedPrecDepth, classifiedPrecDuration
            gc.collect()
    
    # formatting of output DataFrames
    spatialPrecDurationSum = spatialPrecDurationSum.reindex(classLabels)
    spatialPrecDepthSum = spatialPrecDepthSum.reindex(classLabels)
    # sort classes, transpose, delete first dummy index        
    temporalPrecDepthSum = temporalPrecDepthSum.reindex(classLabels).T.drop(dummyStart, axis=0)
    temporalPrecDurationSum = temporalPrecDurationSum.reindex(classLabels).T.drop(dummyStart, axis=0)
            
    return spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum


if __name__ == "__main__":
    """import time
    start_time = time.time()
    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\RW_rea003_Hessen.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=False, percentage=False)
    
    print time.time() - start_time

    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("RW003/spatial/abs/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("RW003/spatial/abs/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("RW003/temporal/abs/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("RW003/temporal/abs/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()

    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\RW_rea003_Hessen.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=True, percentage=True)
    
    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("RW003/spatial/percentage/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("RW003/spatial/percentage/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("RW003/temporal/percentage/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("RW003/temporal/percentage/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()

    
    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\DWD_gauges.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=False, percentage=False)
    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("DWD_Gauges/spatial/abs/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("DWD_Gauges/spatial/abs/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("DWD_Gauges/temporal/abs/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("DWD_Gauges/temporal/abs/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()
    
    
    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\DWD_gauges.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=True, percentage=True)
    
    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("DWD_Gauges/spatial/percentage/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("DWD_Gauges/spatial/percentage/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("DWD_Gauges/temporal/percentage/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("DWD_Gauges/temporal/percentage/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()
    

    
    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\HLNUG_gauges.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=False, percentage=False)
    
    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("HLNUG_Gauges/spatial/abs/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("HLNUG_Gauges/spatial/abs/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("HLNUG_Gauges/temporal/abs/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("HLNUG_Gauges/temporal/abs/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()
    
    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\HLNUG_gauges.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=True, percentage=True)
    
    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("HLNUG_Gauges/spatial/percentage/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("HLNUG_Gauges/spatial/percentage/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("HLNUG_Gauges/temporal/percentage/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("HLNUG_Gauges/temporal/percentage/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()
    """
    
    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\RW_rea002_Hessen.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=False, percentage=False)

    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("RW002/spatial/abs/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("RW002/spatial/abs/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("RW002/temporal/abs/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("RW002/temporal/abs/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()

    spatialPrecDepthSum, spatialPrecDurationSum, temporalPrecDepthSum, temporalPrecDurationSum = classification( \
    HDFFile=r"O:\KLIMPRAX\HDF5\RW_rea002_Hessen.h5", year_start=2001, year_end=2014, months = np.arange(1,13), freq = 'H', dropna=True, percentage=True)
    
    f = pd.HDFStore(r"O:\KLIMPRAX\HDF5\Einzelintervallanalyse.h5", mode = "a")        
    f.put("RW002/spatial/percentage/depth0114", spatialPrecDepthSum, data_columns = True, index = True)
    f.put("RW002/spatial/percentage/duration0114", spatialPrecDurationSum, data_columns = True, index = True)
    f.put("RW002/temporal/percentage/depth0114", temporalPrecDepthSum, data_columns = True, index = True)
    f.put("RW002/temporal/percentage/duration0114", temporalPrecDurationSum, data_columns = True, index = True)
    f.close()