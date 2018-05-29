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
   
   radproc.arcgis.raster_to_array.html
   radproc.arcgis.create_idraster_germany.html
   radproc.arcgis.clip_idraster.html
   radproc.arcgis.import_idarray_from_raster.html
   radproc.arcgis.create_idarray.html
   radproc.arcgis.export_to_raster.html
   radproc.arcgis.export_dfrows_to_gdb.html
   radproc.arcgis.attribute_table_to_df.html
   radproc.arcgis.join_df_columns_to_attribute_table.html
   radproc.arcgis.idTable_nineGrid.html
   radproc.arcgis.idTable_to_valueTable.html
   radproc.arcgis.valueTable_nineGrid.html
   radproc.arcgis.rastervalues_to_points.html
   radproc.arcgis.zonalstatistics.html
