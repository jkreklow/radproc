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

 .. toctree:: prebuilt/
   
   radproc.arcgis.raster_to_array
   radproc.arcgis.create_idraster_germany
   radproc.arcgis.clip_idraster
   radproc.arcgis.import_idarray_from_raster
   radproc.arcgis.create_idarray
   radproc.arcgis.export_to_raster
   radproc.arcgis.export_dfrows_to_gdb
   radproc.arcgis.attribute_table_to_df
   radproc.arcgis.join_df_columns_to_attribute_table
   radproc.arcgis.idTable_nineGrid
   radproc.arcgis.idTable_to_valueTable
   radproc.arcgis.valueTable_nineGrid
   radproc.arcgis.rastervalues_to_points
   radproc.arcgis.zonalstatistics
