.. _ref-release-notes:

===============
 Release Notes
===============


.. _ref-v0-1-3:

Version 0.1.3
~~~~~~~~~~~~~

New Functions
-------------

- :py:func:`radproc.heavyrain.duration_sum` has been added. The function can calculate duration sums (Dauerstufen, e.g. D=15, 30, 60 or 120 minutes)
  from precipitation data in 5-minute resolution (e.g. RADOLAN YW). The output is saved in a new HDF5 file with the same monthly structure as the input data.
  Hence, this new file can be used as input for all other radproc functions accessing HDF5.
  
Changes and Bugfixes
--------------------

- The syntax and join method of :py:func:`radproc.arcgis.join_df_columns_to_attribute_table` has been revised.
  The parameter joinField has been renamed to fcJoinField and now only describes the name of the join field contained in the Feature Class.
  For the DataFrame, the index is now used as join field. Only in case the DataFrame contains a column with exactly the same name as fcJoinField,
  the join will be based on this column instead of the DataFrame index.
  Moreover, a bug, due to which columns of data type string could not be joined, was fixed.
  
- :py:func:`radproc.raw.radolan_binaries_to_dataframe`: A bug was fixed, which caused a failure of data import for some months and on some Python environments
  when setting the DataFrame frequency.
  


.. _ref-v0-1-2:

Version 0.1.2
~~~~~~~~~~~~~

Changes to licensing conditions. License provision for free re-use of modified software versions has been added to all source code files.
No changes to the source code itself.


.. _ref-v0-1-1:

Version 0.1.1
~~~~~~~~~~~~~

- In conjunction with changes in support docs at Climate Data Center, the RADOLAN projection file used for ID raster creation (stored in sampledata module) has been replaced.
  The new file contains the stereographic RADOLAN projection in meters instead of kilometers. This guarantees compatibility with RADOLAN ASCII files from CDC.

- Accordingly, the unit of the output coordinates of :py:func:`radproc.core.coordinates_degree_to_stereographic` has been changed to meter
  and the cellsize of :py:func:`radproc.arcgis.create_idraster_germany` has been set to 1000 instead of 1.
  
- :py:func:`radproc.raw.unzip_RW_binaries` and :py:func:`radproc.raw.unzip_YW_binaries`: outFolder will now be created if it doesn't exist, yet.

.. _ref-v0-1-0:

Version 0.1.0
~~~~~~~~~~~~~

First radproc release version.

www.pgweb.uni-hannover.de only hosts the docs for the latest release version.
If you need former versions, please check out the docs on https://radproc.readthedocs.io
Unfortunately, they don't contain the docs af the arcgis module due to technical problems with the installation of arcpy at readthedocs.