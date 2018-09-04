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
========================
 ArcGIS-based Functions
========================

Collection of all functions based on arcpy.

    - Generate and clip ID-raster
    - Import ID-raster to ID-array
    - Export pandas Series to raster
    - Export all rows of a DataFrame to rasters in a File-Geodatabase,
        optionally calculating statistics rasters (mean, sum, max, ...)
    - Import attribute table or dbf table to DataFrame
    - Join DataFrame columns to attribute table of a Feature Class
    - Extract values from rasters at point locations and the eight surrounding cells
    - Extract values from rasters to new fields in a Point Feature Class
    - Calculate zonal statistics and join to zone Feature Class

.. autosummary::
   :nosignatures:
   :toctree: generated/

   
   raster_to_array
   create_idraster_germany
   clip_idraster
   import_idarray_from_raster
   create_idarray
   export_to_raster
   export_dfrows_to_gdb
   attribute_table_to_df
   join_df_columns_to_attribute_table
   idTable_nineGrid
   idTable_to_valueTable
   valueTable_nineGrid
   rastervalues_to_points
   zonalstatistics


.. module:: radproc.arcgis
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module arcgis
.. moduleauthor:: Jennifer Kreklow
"""
from __future__ import division, print_function

import numpy as np
import pandas as pd
import os
import radproc.core as _core

try:
    import arcpy
except ImportError:
    print("Import Error! Module arcpy not found")


class LicenseError(Exception):
    pass

try:
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        # raise a custom exception
        raise LicenseError
except LicenseError:
    print("Spatial Analyst license is unavailable")



def raster_to_array(raster):
    """
    Imports all values of a raster and converts them to one-dimensional array.
    
    :Parameters:
    ------------
    
        raster : string
            Path to raster dataset (e.g. containing ID values).
        
    :Returns:
    ---------
    
        arr : one-dimensional numpy array
            containing all values of study area without surrounding NoData values.
    """  
    
    # Import ID raster to Raster object and check properties
    rasObj = arcpy.Raster(raster)
    X = rasObj.extent.XMin
    Y = rasObj.extent.YMin
    ncols = rasObj.width
    nrows = rasObj.height
    
    # Convert ID raster object to one-dimensional array. Marginal cells which are not located within the investigation area have value -9999.
    # Attention: Functions take arguments in different order by default! --> reshape(nrows, ncols), RasterToNumPyArray(..., ncols, nrows)
    arr_incl_nodata = arcpy.RasterToNumPyArray(rasObj, arcpy.Point(X, Y), ncols, nrows, -9999).reshape(nrows * ncols)
    # Remove all NoData values (-9999) to keep only ID values --> only cells located in investigation area   
    arr = arr_incl_nodata[arr_incl_nodata != -9999]
    return arr


def create_idraster_germany(projectionFile, outRaster, extendedNationalGrid = True):
    """
    Creates an ID raster in stereographic projection for the extended national RADOLAN grid (900 x 1100 km) or the national grid (900 x 900 km).
    
    ID values range from 0 in the upper left corner to 989999 in the lower right corner for the extended national grid
    and to 809999 in the national grid.
    
    :Parameters:
    ------------
    
        projectionFile : string
            Path to a file containing stereographic projection definition. File type may be Feature Class, Shapefile, prj-file or grid.
        outRaster : string
            Path and name for the output ID raster to be created.
        extendedNationalGrid : bool (optional, default: True)
            True: extended 900 x 1100 national RADOLAN grid, False: 900x900 national grid.
        
    :Returns:
    ---------
    
        outRaster : string
            Path and name of the generated output raster.
            
    :Note:
    ------
        
    To use the custom RADOLAN projection as projectionFile for the output ID raster, you can specify the prj-file provided in radproc.sampledata:
        
        >>> from radproc.sampledata import get_projection_file_path
        >>> projectionFile = get_projection_file_path()
        
    """
    
    if extendedNationalGrid == True:
        x, y = _core.coordinates_degree_to_stereographic(Lambda_degree = 4.6759, Phi_degree = 46.1929)
        # Create 1D-numpy-Array with values from 0 to 989999 and reshape it to 2D-Array according to raster size.
        # Attention: reshape takes arguments in order reshape(nrows, ncolumns)
        idArr = np.arange(0,1100*900).reshape(1100,900)
    elif extendedNationalGrid == False:
        x, y = _core.coordinates_degree_to_stereographic(Lambda_degree = 3.5889, Phi_degree = 46.9526)
        idArr = np.arange(0,900*900).reshape(900,900)
    else:
        # Create extended raster in case of incorrect parameter
        x, y = _core.coordinates_degree_to_stereographic(Lambda_degree = 4.6759, Phi_degree = 46.1929)
        idArr = np.arange(0,1100*900).reshape(1100,900)
        
        
    idRaster = arcpy.NumPyArrayToRaster (idArr, arcpy.Point(x, y), 1000, 1000, -9999)
    
    if projectionFile.endswith(".prj"):
        spatialRef = projectionFile
    else:
        spatialRef = arcpy.Describe(projectionFile).spatialReference

    arcpy.DefineProjection_management (idRaster, spatialRef)
    idRaster.save(outRaster)
    return outRaster


def clip_idraster(idRaster, clipFeature, outRaster):
    """
    Clips a raster to the extent of the clip feature.
    
    :Parameters:
    ------------
    
        idRaster : string
            Path to the raster dataset to be clipped. Also defines the projection of the output raster.
        clipFeature : string
            Path to the clip feature defining the extent of the output raster. File type may be Shapefile or Feature Class.
            The clip Feature does not need to be provided in the RADOLAN projection. See below for further details.
        outRaster : string
            Path and name for the output raster to be created.
        
    :Returns:
    ---------
    
        outRaster : string
            Path and name of the generated output raster.
            
    :Note:
    ------
    
    .. note:: The RADOLAN data are provided in a custom stereographic projection defined by the DWD.
    As there is no transformation method available yet, it is not possible to directly perform
    any geoprocessing tasks with RADOLAN and geodata with other spatial references.
    Nevertheless, ArcGIS is able to perform a correct on-the-fly transformation to display the data together.
    The clip function uses this as a work-around solution to "push" the clip feature into the RADOLAN projection.
    Hence, the function works with geodata in different projections, but the locations of the cells might be slightly inaccurate.
        
    """
    
    # Mask raster and reduce extent to clip feature 
    arcpy.env.mask = clipFeature
    arcpy.env.extent = arcpy.Describe(clipFeature).extent
    # Snap output raster to input raster to avoid dislocation of cells in output raster
    arcpy.env.snapRaster = idRaster
    idRaster_clipped = arcpy.sa.ApplyEnvironment(idRaster)
    idRaster_clipped.save(outRaster)
    return outRaster


def import_idarray_from_raster(idRaster):
    """
    Imports all values of raster and converts them to one-dimensional array.
    
    :Parameters:
    ------------
    
        idRaster : string
            Path to raster dataset containing ID values.
        
    :Returns:
    ---------
    
        idArr : one-dimensional numpy array
            containing ID values of dtype int32
            
    """  
    
    idArr = raster_to_array(raster=idRaster)
    return idArr.astype('int32')


def create_idarray(projectionFile, idRasterGermany, clipFeature, idRaster, extendedNationalGrid=True):
    """
    Creates an ID-Array for a study area.
    
    Creates a new ID-raster for Germany, clips it to study area and exports the raster to a one-dimensional numpy-array.
    
    :Parameters:
    ------------
    
        projectionFile : string
            Path to a file containing stereographic projection definition. File type may be Feature Class, Shapefile, prj-file or grid.
        idRasGermany : string
            Path and name for the output ID raster of Germany to be created.
        clipFeature : string
            Path to the clip feature defining the extent of the study area. File type may be Shapefile or Feature Class.
        idRas : string
            Path and name for the output ID raster of the study area to be created.
        extendedNationalGrid : bool (optional, default: True)
            True: extended 900 x 1100 national RADOLAN grid, False: 900x900 national grid.
        
    :Returns:
    ---------
    
        idArr : one-dimensional numpy array
            containing ID values of dtype int32
            
    :Note:
    ------
        
    .. note::
    
        The RADOLAN data are provided in a custom stereographic projection defined by the DWD.
        As there is no transformation method available yet, it is not possible to directly perform
        any geoprocessing tasks with RADOLAN and geodata with other spatial references.
        Nevertheless, ArcGIS is able to perform a correct on-the-fly transformation to display the data together.
        The clip function uses this as a work-around solution to "push" the clip feature into the RADOLAN projection.
        Hence, the function works with geodata in different projections, but the locations of the cells might be slightly inaccurate.
    

    To use the custom RADOLAN projection as projectionFile for the output ID raster, you can specify the prj-file provided in radproc.sampledata:
        
        >>> from radproc.sampledata import get_projection_file_path
        >>> projectionFile = get_projection_file_path()
                            
    """

    idRasGermany = create_idraster_germany(projectionFile=projectionFile, outRaster=idRasterGermany, extendedNationalGrid=extendedNationalGrid)
    idRas = clip_idraster(idRaster=idRasGermany, clipFeature=clipFeature, outRaster=idRaster)
    idArr = import_idarray_from_raster(idRaster=idRas)
    return idArr



def export_to_raster(series, idRaster, outRaster):
    """
    Exports series to raster by inserting target values at their corresponding ID values in the ID raster.
    
    :Parameters:
    ------------
    
        series : pandas Series or DataFrame row/column
            containing values to be exported and an index with ID values.
        idRaster : string
            Path to raster dataset containing ID values. Also defines the projection of the output raster.
        outRaster : string
            Path and name for the output raster to be created.
        
    :Returns:
    ---------
    
        outRaster : string
            Path and name of the generated output raster.
    """
    
    # Import ID raster to Raster object and check properties 
    rasObj = arcpy.Raster(idRaster)
    X = rasObj.extent.XMin
    Y = rasObj.extent.YMin
    ncols = rasObj.width
    nrows = rasObj.height
    cellWidth = rasObj.meanCellWidth
    cellHeight = rasObj.meanCellHeight
    
    # Convert ID raster object to one-dimensional array. Marginal cells which are not located within the investigation area have NoData value -9999.
    idArr_incl_nodata = arcpy.RasterToNumPyArray(rasObj, arcpy.Point(X, Y), ncols, nrows, -9999).reshape(nrows * ncols)
    
    # if series is a DataFrame row (a one-dimensional DataFrame with length == 1)
    if len(series) == 1:
         # it has to be converted (squeezed) to a Series
        series = series.squeeze()
        
    # Reindex series with ID array
    # Values of series are inserted in the ID array at their corresponding index/ID value and nodata cells are filled with -9999
    series = series.reindex(idArr_incl_nodata).fillna(-9999)
    # Reshape reindexed series to two-dimensional array with the number of rows and columns of the ID raster object and create new raster object
    outRasObj = arcpy.NumPyArrayToRaster (series.values.reshape(nrows, ncols), arcpy.Point(X, Y), cellWidth, cellHeight, -9999)
    
    # Create describe object of ID raster object to access its spatial reference and project the output raster  
    desc = arcpy.Describe(rasObj)
    arcpy.DefineProjection_management (outRasObj, desc.spatialReference)
    outRasObj.save(outRaster)
    return outRaster


def export_dfrows_to_gdb(dataDF, idRaster, outGDBPath, GDBName, statistics=""):
    """
    Exports all rows of a DataFrame to rasters in a File-Geodatabase.
    
    Up to the last ten elements of row index are used as raster name.
    
    :Parameters:
    ------------
    
        dataDF : pandas DataFrame
            containing rows to be exported. Column names must be ID values.
        idRaster : string
            Path to raster dataset containing ID values. Also defines the projection of the output raster.
        outGDBPath : string
            Path for the File-Geodatabase to be created.
        GDBName : string
            Name for the File-Geodatabase to be created.
        statistics : list of strings (optional)
            Types of statistics rasters, that are to be calculated out of all DataFrame rows.
            e.g. "Mean" will calculate the average of all rows for every raster cell.
            The following strings are possible as parameters:
                ["mean" | "sum" | "min" | "max" | "median" | "std" | "range"]
        
    :Returns:
    ---------
    
        No return value
        
        Function creates File-Geodatabase at directory specified in outGDBPath.

    """
    gdb = arcpy.CreateFileGDB_management(outGDBPath, GDBName)
    n = 0
    for index, row in dataDF.iterrows():
        if dataDF.index.is_all_dates == True:
            if dataDF.index.is_year_end.all() == True or dataDF.index.is_year_start.all() == True:
                outRaster = "R_%i" % (index.year)
            elif dataDF.index.is_month_end.all() == True or dataDF.index.is_month_start.all() == True:
                outRaster = "R_%i%02i" % (index.year, index.month)            
            elif dataDF.index.hour.all() != 0:
                outRaster = "R_%i%02i%02i" % (index.year, index.month, index.day)
            else:
                outRaster = "R_%i%02i%02i_%02i%02i" % (index.year, index.month, index.day, index.hour, index.minute)
        else:
            index = str(index)
            if len(index) > 10:
                index = index[:11]
            if "-" in index:
                index = index.replace("-", "_")
            if ":" in index:
                index = index.replace(":", "_")
            if " " in index:
                index = index.replace(" ", "_")
            if "+" in index:
                index = index.replace("+", "_")
            if "." in index:
                index = index.replace(".", "")
            if ">=" in index:
                index = index.replace(">=", "ge")
            if "<=" in index:
                index = index.replace("<=", "le")
            if "___" in index:
                index = index.replace("___", "_")
            if "__" in index:
                index = index.replace("__", "_")
            outRaster = "R_" + index
        
        try:
            export_to_raster(series=row, idRaster=idRaster, outRaster=os.path.join(gdb.getOutput(0), outRaster))
            n += 1
        except:
            arcpy.AddMessage("Grid with name %s could not be generated!" % (outRaster))

    #Calculation of statistic rasters    
    if type(statistics) == list:
        for stat in statistics:
            if stat == "mean":            
                export_to_raster(dataDF.mean(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
            elif stat == "sum":            
                export_to_raster(dataDF.sum(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
            elif stat == "min":            
                export_to_raster(dataDF.min(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
            elif stat == "max":            
                export_to_raster(dataDF.max(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
            elif stat == "median":            
                export_to_raster(dataDF.median(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
            elif stat == "std":            
                export_to_raster(dataDF.std(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
            elif stat == "range":            
                export_to_raster(dataDF.max()-dataDF.min(), idRaster, outRaster=os.path.join(gdb.getOutput(0), stat))
                n += 1
    
    arcpy.AddMessage("Generated %i grids in geodatabase %s!" % (n, gdb.getOutput(0)))
    


def attribute_table_to_df(inFC):
    """
    Load data from dbf table into a pandas DataFrame for subsequent analysis.
    
    :Parameters:
    ------------
    
        inFC: String
            Path and name of ArcGIS Feature Class, Shapefile or dbf table.
        
    :Returns:
    ---------
    
        df : pandas DataFrame
            containing data from attribute table
            
    """
    # Field Shape has to be excluded because it contains a list which is not supported as array element for DataFrame conversion
    field_list = [f.name for f in arcpy.ListFields(inFC) if not f.name == "Shape"]
    
    df = pd.DataFrame(arcpy.da.FeatureClassToNumPyArray(
            in_table=inFC,
            field_names=field_list,
            skip_nulls=False,
            null_value=-99999
        )
    )
    return df


def idTable_nineGrid(inPointFC, idRaster, outPointFC, indexField):
    """
    Gets the IDs of point locations from an ID raster and calculates the IDs of the eight surrounding cells for every point.
    
    Scientific background: Hydrometeors detected by the radar in higher altitudes do not necessarily reach the ground in the same pixel area due to wind drift.
    Consequently, it may be necessary to take the surrounding cells into account when comparing radar and gauge measurements.
    For instance, this nine cell grid is used by the German Weather Service (DWD) to compare weather radar and gauge measurements.    
    The DWD uses the pixel from the nine cell grid with the least absolute difference between radar and gauge measurement
    to calculate the adjustment factors/differences.
    
    :Parameters:
    ------------
    
        inPointFC: String
            Path and name of ArcGIS Point Feature Class or Shapefile defining the point locations,
            e.g. rain gauges, wind energy plants.
        idRaster : string
            Path to raster dataset containing ID values.
        outPointFC : String
            Path and name of the output point Feature Class to be created.
        indexField : String
            Field from inPointFC containing the index values for the point locations, e.g. the station names.
            
        
    :Returns:
    ---------
    
        idTable : pandas DataFrame
            containing the nine cell IDs (columns) for every point.    
    
    """
    #get ID values at point locations
    ResObj = arcpy.sa.ExtractValuesToPoints (in_point_features=inPointFC, in_raster=idRaster, out_point_features=outPointFC)
    df = attribute_table_to_df(ResObj)
    #Array of unique raster values on point locations
    IDs = df["RASTERVALU"]
    gridSize=9
    #Build 2D-Array through repetition from which ID-Dataframe is calculated
    grid = IDs.values.repeat(gridSize).reshape(len(IDs),gridSize)
    gridValues = np.array([-901,-900,-899,-1,0,1,899,900,901])
    nineGrid = grid + gridValues
    idTable = pd.DataFrame(data=nineGrid, index=df[indexField])
    
    #---in case other gridsizes are needed in future:---
    #import math
    #gridLength = math.sqrt(gridSize)
    #cols = np.arange(1,gridLength+1)
    #rows = np.arange(1,gridLength+1)
    #centerline_horiz = np.arange(-(len(cols)-np.median(cols)), len(cols)-np.median(cols)+1)
    #[-2*900, -1*900, 0*900, 1*900, 2*900], centerline
    #centerline_vert = centerline_horiz*900 
    #centerline_vert.reshape(len(centerline_vert),1) +centerline_horiz
    #centerline_vert.reshape(len(centerline_vert),1) + centerline_horiz
    #---------------------------------------------------
    return idTable


def idTable_to_valueTable(idTable, dataSeries):
    """
    Selects the values defined in an ID Table from a data Series.
    
    For further information see documentation of idTable_nineGrid().
    
    :Parameters:
    ------------
    
        idTable : pandas DataFrame
            containing the cell IDs (as columns) for every point.
        dataSeries : pandas Series
            containing (precipitation) values to select depending on the IDs in the index.
            
        
    :Returns:
    ---------
        valueTable : pandas DataFrame
            of the same format as idTable. IDs are replaced by the corresponding values from dataSeries.
    
    """
    
    selectedValues = dataSeries[idTable.values.reshape(idTable.shape[0]*idTable.shape[1])]
    valueTable = pd.DataFrame(selectedValues.values.reshape(idTable.shape[0],idTable.shape[1]),index = idTable.index)
    return valueTable


def valueTable_nineGrid(inPointFC, idRaster, outPointFC, indexField, dataSeries):
    """
    Selects the values of a nine cell grid around point locations.
    
    First, the IDs of point locations are identified from an ID raster and the IDs of the eight surrounding cells are calculated for every point.
    Second, the values corresponding to the IDs of the nine cell grid are selected from dataSeries.
    
    Scientific background: Hydrometeors detected by the radar in higher altitudes do not necessarily reach the ground in the same pixel area due to wind drift.
    Consequently, it may be necessary to take the surrounding cells into account when comparing radar and gauge measurements.
    For instance, this nine cell grid is used by the German Weather Service (DWD) to compare weather radar and gauge measurements.    
    The DWD uses the pixel from the nine cell grid with the least absolute difference between radar and gauge measurement
    to calculate the adjustment factors/differences.
    
    :Parameters:
    ------------
    
        inPointFC: String
            Path and name of ArcGIS Point Feature Class or Shapefile defining the point locations,
            e.g. rain gauges, wind energy plants.
        idRaster : string
            Path to raster dataset containing ID values.
        outPointFC : String
            Path and name of the output point Feature Class to be created.
        indexField : String
            Field from inPointFC containing the index values for the point locations, e.g. the station names.
        dataSeries : pandas Series
            containing (precipitation) values to select depending on the IDs in the index.
            
        
    :Returns:
    ---------
    
        valueTable : pandas DataFrame
            containing the (precipitation) values of the nine cell grid around every point.
            
    """
    
    idTable = idTable_nineGrid(inPointFC, idRaster, outPointFC, indexField)
    valueTable = idTable_to_valueTable(idTable, dataSeries)
    return valueTable


def rastervalues_to_points(inPointFC, inRasterList, newFieldNameList, outPointFC):
    """
    Extract values from a list of rasters to new fields in a point Feature Class.
    
    :Parameters:
    ------------
    
        inPointFC: String
            Path and name of ArcGIS Point Feature Class or Shapefile defining the point locations,
            e.g. rain gauges, wind energy plants.
            The input file is not altered by this function.
        inRasterList : List of Strings
            containing paths and names of all rasters to extract values from.
        newFieldNameList : List of Strings
            containing the names for the new fields which are created in the output Feature Class.
            Values from the rasters are written into the new fields in corresponding order.
        outPointFC : String
            Path and name of the output point Feature Class to be created.
            
        
    :Returns:
    ---------
    
        ResObj : arcpy Result Object
            of the output point Feature Class    
        
"""    
    i = 0    
    #avoid errors if only a string for one raster is specified
    if type(inRasterList) != list:
        inRasterList = [inRasterList]
    if type(newFieldNameList) != list:
        newFieldNameList = [newFieldNameList]
    
    for inRaster, newField in zip(inRasterList, newFieldNameList):
        #for the first raster in the list, the function can be executed normally
        if i == 0:
            ResObj = arcpy.sa.ExtractValuesToPoints(inPointFC, inRaster, outPointFC, "", "")
        #for every following raster, a copy of the first output point feature class has to be made,
        #since it is input and output at the same time, copy is deleted afterwards
        else:
            if outPointFC.endswith(".shp"):
                temp = os.path.join(os.path.split(outPointFC)[0], "temp.shp")
            else:
                temp = os.path.join(os.path.split(outPointFC)[0], "temp")
            arcpy.Copy_management(in_data=outPointFC, out_data=temp)
            ResObj = arcpy.sa.ExtractValuesToPoints(in_point_features=temp, in_raster=inRaster, out_point_features=outPointFC)
            arcpy.Delete_management(in_data=temp)
        
        #add field, copy raster values inside and delete RASTERVALU field. Otherwise next loop run would fail.
        i += 1
        arcpy.AddField_management(ResObj, newField, "DOUBLE")
        arcpy.CalculateField_management(in_table=ResObj, field=newField, expression="!RASTERVALU!",expression_type="PYTHON")
        arcpy.DeleteField_management(in_table=ResObj, drop_field="RASTERVALU")
    return ResObj


    
def zonalstatistics(inZoneData, zoneField, inRaster, outTable, outFC):
    """
    Calculate Zonal Statistics as Table, join output to copy of zone Feature Class and import resulting table into DataFrame.
    
    :Parameters:
    ------------
    
        inZoneData: String
            Path and name of ArcGIS Polygon Feature Class or Shapefile defining the zones,
            e.g. counties, watersheds or buffer areas around rain gauges.
            File is copied within the same directory and copy is called "zonalstat" to avoid changing the input dataset.
        zoneField : String
            Name of field containing the zone names, also used as join field.
        inRaster : String
            Path and name of grid or raster dataset to calculate statistics for, e.g. precipitation raster.
            All available statistics are calculated (COUNT, MIN, MAX, MEAN, SUM, RANGE, STD).
        outTable : String
            Path and name of dbf table to be created.
        outFC : String
            Path and name of Feature Class to be created. Feature Class will be a copy of inZoneData with outDBF joined to its attribute table.
        
    :Returns:
    ---------
    
        df : pandas DataFrame
            containing data from attribute table    
    
    
"""    
    arcpy.sa.ZonalStatisticsAsTable (inZoneData, zoneField, inRaster, outTable, ignore_nodata="DATA", statistics_type="ALL")
    #ras = ZonalStatistics (in_zone_data=shp, zone_field=field, in_value_raster=rw, statistics_type=statistic, ignore_nodata="DATA")
    #ras.save(outras)
    path, name = os.path.split(inZoneData)
    arcpy.Copy_management(inZoneData, outFC)
     # Join the zone feature class to zonal statistics table
    arcpy.JoinField_management (in_data=outFC, in_field=zoneField, join_table=outTable, join_field=zoneField)
    try:
        df = attribute_table_to_df(outFC)
        df.index = df[zoneField]
        return df
    except:
        pass


def join_df_columns_to_attribute_table(df, columns, fc, fcJoinField):
    """
    Join DataFrame columns to attribute table of a feature flass or Shapefile.
    The fields are added to the existing feature class, which will not be copied.
    
    :Parameters:
    ------------

         df : pandas DataFrame
             with data columns to be joined to attribute table.
             The join will be based on the DataFrame index by default.
             But if the DataFrame contains a column with exactly the same name as fcJoinField,
             the join will be based on this column instead of the index.
         columns : List of Strings or pandas column Index object
             containing names of columns which are to be joined to feature class.
             The column list may also be a pandas column index generated by calling df.columns
         fc : String
             Path and Name of feature class or shapefile.
         fcJoinField : String
             Name of the join field in the feature class.
             If a column with exactly the same name as fcJoinField is contained in the DataFrame,
             the join will be based on this column instead of the index.
             
    :Returns:
    ---------
    
        None
    
    """
    
    # convert column index object to list if necessary
    if type(columns) == pd.core.indexes.base.Index:
        columns = list(df.columns)
    
    # if fcJoinField is already contained in column list, delete it
    if fcJoinField in columns:
        del columns[columns.index(fcJoinField)]
    
    #  set name of join field to first position in column list
    columns.insert(0, fcJoinField)
    
    # if the DataFrame does not contain a column names equal to fcJoinField, this column is generated from the index
    # else, the existing column will be used
    if not fcJoinField in df.columns:
        df[fcJoinField] = df.index
    
    # select columns from column list
    df = df[columns]
    
    # check if column names contain integers and replace them by Strings to avoid errors in AddField 
    df.columns = ["F%s" % col if type(col) in [np.int64, np.int32, int] else col for col in df.columns]
    columns = ["F%s" % col if type(col) in [np.int64, np.int32, int] else col for col in columns]
    
    n = len(columns)
    # [1:] to exclude column fcJoinField which was inserted ar first position
    for column in columns[1:]:
        # check data type of each column an add field of same type in fc
        # 
        column_dtype = str(type(df[column].values[1]))
        if "float" in column_dtype:
            fieldType = "DOUBLE"
        elif "str" in column_dtype or "unicode" in column_dtype:
            fieldType = "TEXT"
        else:
            fieldType = "LONG"
        
        try:
            arcpy.AddField_management (in_table=fc, field_name=column, field_type=fieldType)
        except:
            arcpy.DeleteField_management (in_table=fc, drop_field=column)
            arcpy.AddField_management (in_table=fc, field_name=column, field_type=fieldType)
    
    for index, dfrow in df.iterrows():
        
        with arcpy.da.UpdateCursor(fc, columns) as cursor:
            for fcrow in cursor:
                # check index/join field values and insert corresponding row values
                if fcrow[0] == dfrow[fcJoinField]:
                    for i in range(1,n):
                        # try to check if value is not nan --> insert, else set to 0 to avoid nan in attribute table
                        # will only work for numeric data. strings will be inserted "as is" in case of exception
                        try:                            
                            if np.isnan(dfrow[columns[i]]) == False:
                                fcrow[i] = dfrow[columns[i]]
                            else:
                                fcrow[i] = 0
                        except:                            
                            fcrow[i] = dfrow[columns[i]]
                    cursor.updateRow(fcrow)
                    break
                