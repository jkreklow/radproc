.. radproc documentation master file, created by
   sphinx-quickstart on Wed Apr 26 15:39:34 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

radproc: An ArcGIS-compatible Library for RADOLAN Composite Processing and Analysis
===================================================================================

:Release: |release|
:Date: |today|

Radproc is an open source Python library intended to faciliate precipitation data processing and analysis for ArcGIS-users.
It provides functions for processing, analysis and export of RADOLAN (Radar Online Adjustment) composites and rain gauge data in MR90 format.
The German Weather Service (DWD) provides the RADOLAN RW composites for free in the Climate Data Center
but the data processing represents a big challenge for many potential users.
radproc's goal is to lower the barrier for using these data, especially in conjunction with ArcGIS.
Therefore, radproc provides an ArcGIS-compatible data processing workflow based on pandas DataFrames and HDF5.
Moreover, radproc's arcgis module includes a collection of functions for data exchange between pandas and ArcGIS.

radproc's main features 
~~~~~~~~~~~~~~~~~~~~~~~

Raw Data processing
-------------------
	
	* Support for the reanalyzed RADOLAN products RW (60 min), YW and RY (both 5 min. resolution)
	* Automatically reading in all binary RADOLAN composites from a predefined directory structure
	* Optionally clipping the composites to a study area in order to reduce data size
	* Default data structure: Monthly pandas DataFrames with full support for time series analysis and spatial location of each pixel
	* Efficient data storage in HDF5 format with fast data access
	* Easy downsampling of time series
	* Reading in DWD rain gauge data in MR90 format into the same data structure as RADOLAN.

Data Exchange with ArcGIS
-------------------------

	* Export of single RADOLAN composites or analysis results into projected raster datasets or ESRI grids for your study area
	* Export of all DataFrame rows into raster datasets in a new file geodatabase, optionally including several statistics rasters.
	* Import of dbf tables (stand-alone or attribute tables of feature classes) into pandas DataFrames
	* Joining DataFrame columns to attribute tables
	* Extended value extraction from rasters to points (optionally including the eight surrounding cells)
	* Extended zonal statistics
	
Analysis
--------

	* Calculation of precipitation sums for arbitrary periods of time
	* Data quality assessment
	* Comparison of RADOLAN and rain gauge data
	* Heavy rainfall analysis, e.g. identification and export of rainfall intervals exceeding a defined threshold
	* Erosivity analysis, e.g. calculation of monthly, seasonal or annual R-factors

.. toctree::
   :maxdepth: 2
   
   gettingstarted
   reference   
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
