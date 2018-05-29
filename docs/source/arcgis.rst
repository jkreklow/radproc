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

 .. toctree:: generated/

   
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
