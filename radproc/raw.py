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
=====================
 Raw Data Processing
=====================

Functions for raw data processing.

Unzip, import, clip and convert RADOLAN raw data and write DataFrames to HDF5.

.. autosummary::
   :nosignatures:
   :toctree: generated/
   
   unzip_RW_binaries
   unzip_YW_binaries
   radolan_binaries_to_dataframe
   radolan_binaries_to_hdf5
   create_idraster_and_process_radolan_data
   process_radolan_data
   
   
.. module:: radproc.raw
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module raw
.. moduleauthor:: Jennifer Kreklow
"""
from __future__ import division, print_function

import numpy as np
import pandas as pd
import os, sys

import tarfile as _tarfile
import gzip as _gzip
import shutil as _shutil
from datetime import datetime

#from radproc.wradlib_io import read_RADOLAN_composite
#from radproc.sampledata import get_projection_file_path
import radproc.wradlib_io as _wrl_io
import radproc.sampledata as _sampledata

import warnings, tables


def unzip_RW_binaries(zipFolder, outFolder):
    """
    Unzips RADOLAN RW binary data saved in monthly .tar or tar.gz archives (e.g. RWrea_200101.tar.gz, RWrea_200102.tar.gz).
    
    If necessary, extracted binary files are zipped to .gz archives to save memory space on disk.
    Creates directory tree of style
    
    *<outFolder>/<year>/<month>/<binaries with hourly data as .gz files>*
        
    :Parameters:
    ------------
    
        zipFolder : string
            Path of directory containing RW data as monthly tar / tar.gz archives to be unzipped.
            Archive names must contain year and month at end of basename: RWrea_200101.tar or RWrea_200101.tar.gz 
        outFolder : string
            Path of output directory.  Will be created if it doesn't exist, yet.
        
    :Returns:
    ---------
    
        No return value
    """
            
    if not os.path.exists(outFolder):
        os.mkdir(outFolder)
    
    # create list of all tar files and identify years
    tarFileList = os.listdir(zipFolder)
    years = np.unique([f[-10:-6] if f.endswith(".tar") else f[-13:-9] for f in tarFileList])
    
    for year in years:
        # only select files of current year
        tarFilesYear = [f for f in tarFileList if year in f]
        # create new folder for current year
        yearFolder = os.path.join(outFolder, year)
        os.mkdir(yearFolder)
        for monthTarFile in tarFilesYear:
            # create month folder for every month archive
            if monthTarFile.endswith('.tar.gz'):
                month = str(int(monthTarFile[-9:-7]))
            elif monthTarFile.endswith('.tar'):
                month = str(int(monthTarFile[-6:-4]))
            monthFolder = os.path.join(yearFolder, month)
            os.mkdir(monthFolder)
            
            # open tar archive and extract all files to month folder
            with _tarfile.open(name = os.path.join(zipFolder,monthTarFile), mode = 'r') as tar_ref:
                tar_ref.extractall(monthFolder)
            binaryList = os.listdir(monthFolder)
            
            # if extracted files are already .gz archives: skip, else: zip binary files to .gz archives and delete unzipped files
            if not binaryList[0].endswith(".gz"):
                for binaryName in binaryList:
                    binaryFile = os.path.join(monthFolder, binaryName)
                    with open(binaryFile, 'rb') as f_in, _gzip.open(os.path.join(monthFolder, binaryName + ".gz"), 'wb') as f_out:
                        _shutil.copyfileobj(f_in, f_out)
                    os.remove(binaryFile)



def unzip_YW_binaries(zipFolder, outFolder):
    """
    Unzips RADOLAN YW binary data.
    Data have to be saved in monthly .tar or tar.gz archives (e.g. YWrea_200101.tar.gz, YWrea_200102.tar.gz),
    which contain daily archives with binary files.
    
    If necessary, extracted binary files are zipped to .gz archives to save memory space on disk.
    Creates directory tree of style
    
    *<outFolder>/<year>/<month>/<binaries with data in temporal resolution of 5 minutes as .gz files>*
        
    :Parameters:
    ------------
    
        zipFolder : string
            Path of directory containing YW data as monthly tar / tar.gz archives to be unzipped.
            Archive names must contain year and month at end of basename: YWrea_200101.tar or YWrea_200101.tar.gz 
        outFolder : string
            Path of output directory. Will be created if it doesn't exist, yet. 
        
    :Returns:
    ---------
    
        No return value
    """   
            
    if not os.path.exists(outFolder):
        os.mkdir(outFolder)
    
    # create list of all tar files
    tarFileList = os.listdir(zipFolder)
    years = np.unique([f[-10:-6] if f.endswith(".tar") else f[-13:-9] for f in tarFileList])
    
    for year in years:
        # only select files of current year
        tarFilesYear = [f for f in tarFileList if year in f]
        # create new folder for current year
        yearFolder = os.path.join(outFolder, year)
        os.mkdir(yearFolder)
        # for every month...
        for monthTarFile in tarFilesYear:
            # create month folder for every month archive
            if monthTarFile.endswith('.tar.gz'):
                month = str(int(monthTarFile[-9:-7]))
            elif monthTarFile.endswith('.tar'):
                month = str(int(monthTarFile[-6:-4]))
            monthFolder = os.path.join(yearFolder, month)
            os.mkdir(monthFolder)
            
            # open tar archive and extract all daily gz archives to month folder
            with _tarfile.open(name = os.path.join(zipFolder,monthTarFile), mode = 'r') as tar_ref:
                tar_ref.extractall(monthFolder)
            
            # for every day...
            dayTarFileList = os.listdir(monthFolder)
            for dayTarFile in dayTarFileList:
                with _tarfile.open(name = os.path.join(monthFolder, dayTarFile), mode = 'r') as tar_ref:
                    tar_ref.extractall(monthFolder)
                os.remove(os.path.join(monthFolder, dayTarFile))
                
            binaryList = os.listdir(monthFolder)
            # if extracted files are already .gz archives: skip, else: zip binary files to .gz archives and delete unzipped files
            if not binaryList[0].endswith(".gz"):
                for binaryName in binaryList:
                    binaryFile = os.path.join(monthFolder, binaryName)
                    with open(binaryFile, 'rb') as f_in, _gzip.open(os.path.join(monthFolder, binaryName + ".gz"), 'wb') as f_out:
                        _shutil.copyfileobj(f_in, f_out)
                    os.remove(binaryFile)


def radolan_binaries_to_dataframe(inFolder, idArr=None):
    """
    Import all RADOLAN binary files in a directory into a pandas DataFrame,
    optionally clipping the data to the extent of an investigation area specified by an ID array.
    
    :Parameters:
    ------------
        inFolder : string
            Path to the directory containing RADOLAN binary files.
            All files ending with '-bin' or '-bin.gz' are read in.
            The input folder path does not need to have any particular directory structure.
        idArr : one-dimensional numpy array (optional, default: None)
            containing ID values to select RADOLAN data of the cells located in the investigation area.
            If no idArr is specified, the ID array is automatically generated from RADOLAN metadata
            and RADOLAN precipitation data are not clipped to any investigation area.
        
    :Returns:
    ---------
        (df, metadata) : tuple with two elements:            
            df : pandas DataFrame containing...
                - RADOLAN data of the cells located in the investigation area
                - datetime row index with defined frequency depending on the RADOLAN product and time zone UTC
                - ID values as column names
            metadata : dictionary
                containing metadata from the last imported RADOLAN binary file
                
        In case any binary files could not be read in due to processing errors,
        these are skipped and the respective intervals are filled with NoData (NaN) values.
        A textfile with the names and error messages for the respective monthly input data folder is written for information.
        For example, errors due to obviously corrupted file formats are known for the RADOLAN RW dataset
        in July and August 2005 and May 2007.
                
    
    :Format description and examples:
    ---------------------------------    
        
        Every row of the output DataFrame equals a precipitation raster of the investigation area at the specific date.
        Every column equals a time series of the precipitation at a specific raster cell.
        
        Data can be accessed and sliced with the following Syntax:
            
        **df.loc[row_index, column_name]**
        
        with row index as string in date format 'YYYY-MM-dd hh:mm' and column names as integer values
            
        **Examples:**
            
        >>> df.loc['2008-05-01 00:50',414773] #--> returns single float value of specified date and cell
        >>> df.loc['2008-05-01 00:50', :] #--> returns entire row (= raster) of specified date as one-dimensional DataFrame
        >>> df.loc['2008-05-01', :] #--> returns DataFrame with all rows of specified day (because time of day is omitted)
        >>> df.loc[, 414773] #--> returns time series of the specified cell as Series
        
    """    
     
    try:    
        # List all files in directory
        files = os.listdir(inFolder)
    except:
        print("Directory %s can not be found. Please check your input parameter!" % inFolder)
        sys.exit()
    ind = []
    
    # Check file endings. Only keep files ending on -bin or -bin.gz which are the usual formats of RADOLAN binary files
    files = [f for f in files if f.endswith('-bin') or f.endswith('-bin.gz')]
    
    # Load first binary file to access header information
    try:
        data, metadata = _wrl_io.read_RADOLAN_composite(os.path.join(inFolder, files[0]))
        del data
    except:
        # if file could not be read, try next file until metadata of one file could be accessed
        got_metadata = False
        i=0
        while got_metadata == False:
            print("Can not open %s to access metadata. Trying next file." % files[i])
            i+=1
            try:
                data, metadata = _wrl_io.read_RADOLAN_composite(os.path.join(inFolder, files[i]))
                del data
                got_metadata = True
            except:
                got_metadata = False
                # interrupt after first 100 files to avoid infinite loops
                if i == 100:
                    print('Could not read the first 100 files in. Exit script. Please check your input files and parameters.')
                    raise
    
    # different RADOLAN products have different grid sizes (e.g. 900*900 for the RADOLAN national grid,
    # 1100*900 for the extended national grid used for RADKLIM)
    gridSize = metadata['nrow'] * metadata['ncol']
    
    # if no ID array is specified, generate it from metadata
    if idArr is None:        
        idArr = np.arange(0, gridSize)
    
    # Create two-dimensiona array of dtype float32 filled with zeros. One row per file in inFolder, one column per ID in idArr.
    dataArr = np.zeros((len(files), len(idArr)), dtype = np.float32)
    
    skipped_files = []
    error_messages = []
    # For each file in directory...
    for i in range(0, len(files)):
        # Read data and header of RADOLAN binary file
        try:
            data, metadata = _wrl_io.read_RADOLAN_composite(os.path.join(inFolder, files[i]))
            # append datetime object to index list. Pandas automatically interprets this list as timeseries.
            ind.append(metadata['datetime'])
         
            # binary data block starts in the lower left corner but ESRI Grids are created starting in the upper left corner by default
            # [::-1] --> reverse row order of 2D-array so the first row ist located in the geographic north
            # reshape(gridSize,) --> convert to one-dimensional array
            data = data[::-1].reshape(gridSize,)
        
            # Replace NoData values with NaN
            data[data == metadata['nodataflag']] = np.nan
               
            # Clip data to investigation area by selecting all values with a corresponding ID in idArr
            # and insert data as row in the two-dimensional data array.
            dataArr[i,:] = data[idArr]
        
        except Exception, e:
            skipped_files.append(files[i])
            error_messages.append(str(e))
            # extract datetime from filename instead of metadata
            date_str = files[i].split("-")[2]
            datetime_obj = datetime.strptime(date_str, '%y%m%d%H%M')
            # some early RADOLAN intervals start at HH:45, but in file name stands HH:50
            if ind[0].minute == 45:
                datetime_obj = datetime_obj.replace(minute=45)
            # append extracted date to index and insert NaN to all cells of the skipped interval
            ind.append(datetime_obj)
            dataArr[i,:] = np.zeros((1, len(idArr)), dtype=np.float32).fill(np.nan)
            
    # Convert 2D data array to DataFrame, set timeseries index and column names and localize to time zone UTC 
    df = pd.DataFrame(dataArr, index = ind, columns = idArr) 
    df.columns.name = 'Cell-ID'
    df.index.name = 'Date (UTC)'
    df.index = df.index.tz_localize('UTC')
    #df = df.tz_localize('UTC')
    
    metadata['timezone'] = 'UTC'
    metadata['idArr'] = idArr
    
    # check for RADOLAN product type and set frequency of DataFrame index
    # lists can be extended for other products...    
    if metadata['producttype'] in ["RW"]:
        try:
            # try to prevent dataframe copying by .asfreq(). this does not seem to work in all pandas versions --> try - except
            df.index.freq = pd.tseries.offsets.Hour()            
        except:
            df = df.asfreq('H')
    elif metadata['producttype'] in ["RY", "RZ", "YW"]:
        try:            
            df.index.freq = 5 * pd.tseries.offsets.Minute()
        except:
            df = df.asfreq('5min')
    
    # export list of skipped files and corresponding error messages to txt file
    # if any errors occurred
    if len(skipped_files) > 0:
        two_dirs_up = os.path.split(os.path.split(inFolder)[0])[0]
        outtxt = os.path.join(two_dirs_up, 'skipped_files_%i_%i.txt' % (datetime_obj.year, datetime_obj.month))
        print('%i files had to be skipped due to processing errors.\nIntervals were filled with NaN' % len(skipped_files))
        print('Please check skipped files and error list in created text file %s' % outtxt)
        txt = open(outtxt, 'w')
        for skipped_file, error_message in zip(skipped_files, error_messages):
            txt.write('%s\n%s\n\n' %(skipped_file, error_message))        
        txt.close()
    return df, metadata
    
    
def radolan_binaries_to_hdf5(inFolder, HDFFile, idArr=None, complevel=9):
    """
    Wrapper for radolan_binaries_to_dataframe() to import and **clip all RADOLAN binary files of one month in a directory** into a pandas DataFrame
    and save the resulting DataFrame as a dataset to an HDF5 file. The name for the HDF5 dataset is derived from the names of the input folder (year and month).
    
    :Parameters:
    ------------
    
        inFolder : string
            Path to the directory containing RADOLAN binary files.
            As the function derives the HDF5 group and dataset names from the directory path, the latter is expected to have the following format:
            
                >>> inFolder = "C:/path/to/binaryData/YYYY/MM"  # --> e.g. C:/Data/RADOLAN/2008/5
            
            In this example for May 2008, the output dataset will have the path '2008/5' within the HDF5 file.
        HDFFile : string
            Path and name of the HDF5 file.
            If the specified HDF5 file already exists, the new dataset will be appended; if the HDF5 file doesn't exist, it will be created. 
        idArr : one-dimensional numpy array (optional, default: None)
            containing ID values to select RADOLAN data of the cells located in the investigation area.
            If no idArr is specified, the ID array is automatically generated from RADOLAN metadata
            and RADOLAN precipitation data are not clipped to any investigation area.
        complevel : integer (optional, default: 9)
            defines the level of compression for the output HDF5 file.
            complevel may range from 0 to 9, where 9 is the highest compression possible.
            Using a high compression level reduces data size significantly,
            but writing data to HDF5 takes more time and data import from HDF5 is slighly slower.
        
    :Returns:
    ---------
    
        No return value
        
        Function creates dataset in HDF5 file specified in parameter HDFFile.
        
        In case any binary files could not be read in due to processing errors,
        these are skipped and the respective intervals are filled with NoData (NaN) values.
        A textfile with the names and error messages for the respective monthly input data folder is written for information.
        For example, issues due to obviously corrupt file formats are known for the RADOLAN RW dataset
        in July and August 2005 and May 2007.
        
    """    
  
    # Split directory path to prepare node creation in HDF5 file
    # x is a list with all individual directories in inFolder
    if "\\" in inFolder:    
        x = inFolder.split("\\")
    elif "/" in inFolder:
        x = inFolder.split("/")
    else:
        print("Directory %s can not be found. Please check your input parameter!" % inFolder)
        sys.exit()
    
    # Deduce group names from directory path
    # (years: 4 characters, months: 1-2 characters) 
    # Paths can end with / or \\ depending on delimiter
    # Path .../2008/5 --> last element x[-1] is the month
    if len(x[-1]) == 1 or len(x[-1]) == 2:
        month = x[-1]
    # Path .../2008/5/ --> second to last element x[-2] is the month,
    # Last element is an empty string of length zero --> x = [...,"2008","5",""]
    elif len(x[-2]) == 1 or len(x[-2]) == 2:
        month = x[-2]
    # Path ...\\2008\\5\\ --> third to last element x[-3] is the month,
    # Last two elements are empty strings of length zero --> x = [...,"2008","","5","",""]
    elif len(x[-3]) == 1 or len(x[-3]) == 2:
        month = x[-3]
    else:
        print("No suitable directory path format! Month could not be found!")
        sys.exit()
    
    # Identify years in the same way but one element further in front of list x 
    if len(x[-2]) == 4:
        year = x[-2]
    elif len(x[-3]) == 4:
        year = x[-3]
    elif len(x[-4]) == 4:
        year = x[-4]
    else:
        print("No suitable directory path format! Year could not be found!")
        sys.exit()
    
    # Path (Group) and Label of HDF5 dataset to be created
    HDFDataset = "/".join([year,month])
    
    # Call function radolan_binaries_to_dataframe() to import, clip and convert RADOLAN binary files from inFolder to DataFrame
    df, metadata = radolan_binaries_to_dataframe(inFolder, idArr)



    # Save DataFrame to HDF5 file in fixed format --> No slicing on disk, entire dataset has to be loaded into memory
    # Note: Saving in table format (which allows slicing datasets on disk) is not possible since HDF5 is a row oriented data format,
    # which offers only 64kb memory for column names (supporting up to about 2000 columns)    
    # pandas HDFStore is based on pytables and allows to save DataFrames to HDF5 with index and column names
    # Disadvantage: Opening this custom format without any problems is only possible using pandas functions    
    with pd.HDFStore(HDFFile, mode = "a", complevel=complevel) as f:        
        f.put(HDFDataset, df, data_columns = True, index = True)


#--------Automization---------------------------------------------------

def _process_year(yearFolder, HDFFile, idArr, complevel):
    monthFolders = [os.path.join(yearFolder, monthDir) for monthDir in os.listdir(yearFolder)]
    monthFolders = [monthDir for monthDir in monthFolders if os.path.isdir(monthDir)]
    failed = []
    
    # create directory for every month
    # import all binary files of month directory, cut them to study area and merge to DataFrame
    # if an error occurs, the month will be skipped and added to a list of fails
    for monthFolder in monthFolders:
        try:
            radolan_binaries_to_hdf5(inFolder=monthFolder, HDFFile=HDFFile, idArr=idArr, complevel=complevel)
            print(monthFolder + " processed")
        except:
            print("Error at " + monthFolder)
            failed.append(monthFolder)
            #raise
            continue
    return failed



def create_idraster_and_process_radolan_data(inFolder, HDFFile, clipFeature=None, complevel=9):
    """
    Convert all RADOLAN binary data in directory tree into an HDF5 file with monthly DataFrames for a given study area.
    
    First, an ID raster is generated and - if you specified a Shapefile or Feature-Class as clipFeature - clipped to your study area.
    The national ID Raster (idras_ger) and the clipped one (idras) are saved in directory of HDF5 file.
    
    Afterwards, all RADOLAN binary files in a directory tree are imported, 
    clipped to study area, converted into monthly pandas DataFrames and stored in an HDF5 file.
    
    The names for the HDF5 datasets are derived from the names of the input folders (year and month).
    The directory tree containing the raw binary RADOLAN data is expected to have the following format:
    
    *<inFolder>/<year>/<month>/<binaries with RADOLAN data>*
    
    --> *<inFolder>*/YYYY/MM
        
    --> *<inFolder>*/2008/5 or *<inFolder>*/2008/05
        
    --> e.g. *C:/Data/RW*/2008/5
    
    In this example, the output dataset will have the path 2008/5 within the HDF5 file.
    The necessary format is automatically generated by the functions :func:`radproc.raw.unzip_RW_binaries` and :func:`radproc.raw.unzip_YW_binaries`.
    
    If necessary, a textfile containing all directories which could not be processed due to data format errors is created in directory of HDF5 file.
    
    :Parameters:
    ------------
    
        inFolder : string
            Path to the **directory tree** containing RADOLAN binary files. The directory tree is expected to have the following structure:
            *<inFolder>*/YYYY/MM --> *C:/Data/RADOLAN*/2008/5
        HDFFile : string
            Path and name of the HDF5 file.
            If the specified HDF5 file already exists, the new dataset will be appended; if the HDF5 file doesn't exist, it will be created. 
        clipFeature : string (optional, default: None)
            Path to the clip feature defining the extent of the study area. File type may be Shapefile or Feature Class.
            The clip Feature does not need to be provided in the RADOLAN projection. See below for further details.
            Default: None (Data are not clipped to any study area)
        complevel : interger (optional, default: 9)
            defines the level of compression for the output HDF5 file.
            complevel may range from 0 to 9, where 9 is the highest compression possible.
            Using a high compression level reduces data size significantly,
            but writing data to HDF5 takes more time and data import from HDF5 is slighly slower.
        
    :Returns:
    ---------
    
        No return value
        Function creates datasets for every month in HDF5 file specified in parameter HDFFile.
        Additionally, two ID Rasters are created in the directory of the HDF5 file.
        
        In case any binary files could not be read in due to processing errors,
        these are skipped and the respective intervals are filled with NoData (NaN) values.
        A textfile with the names and error messages for the respective monthly input data folder is written
        and stored in inFolder for information.
        For example, issues due to obviously corrupt file formats are known for the RADOLAN RW dataset
        in July and August 2005 and May 2007.

    
    .. seealso:: See :ref:`ref-filesystem` for further details on data processing.
                 If you already have an ID Array available, use :func:`radproc.raw.process_radolan_data` instead.
    
    .. note:: The RADOLAN data are provided in a custom stereographic projection defined by the DWD
              and both ID rasters will automatically be generated in this projection by this function.
              As there is no transformation method available yet, it is not possible to directly perform
              any geoprocessing tasks with RADOLAN and geodata with other spatial references.
              Nevertheless, ArcGIS is able to perform a correct on-the-fly transformation to display the data together.
              The clip function implemented in radproc uses this as a work-around solution to "push" the clip feature into the RADOLAN projection.
              Hence, the clipping works with geodata in different projections, but the locations of the cells might be slightly inaccurate.
    
    
    :Format description and examples:
    ---------------------------------    
        
        After the import, individual DataFrames can be loaded into memory from the generated HDF5 file using :func:`radproc.core.load_month` or
        several DataFrames within the same year can be loaded together using :func:`radproc.core.load_months_from_hdf5`
    
        Every row of the output DataFrames equals a precipitation raster of the investigation area at the specific date.
        Every column equals a time series of the precipitation at a specific raster cell.
        
        Data can be accessed and sliced with the following Syntax:
            
        **df.loc[row_index, column_name]**
        
        with row index as string in date format 'YYYY-MM-dd hh:mm' and column names as integer values
            
        **Examples:**
            
        >>> dataHDF5 = r'C:\Data\HDF5\RW.h5'
        >>> df = radproc.load_month(HDFFile=dataHDF5, year=2008, month=5)
        >>> df.loc['2008-05-01 00:50',414773] #--> returns single float value of specified date and cell
        >>> df.loc['2008-05-01 00:50', :] #--> returns entire row (= raster) of specified date as one-dimensional DataFrame
        >>> df.loc['2008-05-01', :] #--> returns DataFrame with all rows of specified day (because time of day is omitted)
        >>> df.loc[, 414773] #--> returns time series of the specified cell as Series
    
    """    
    
    # Ignore NaturalNameWarnings --> Group/Dataset names begin with number,
    # doesn't affect generation and access
    warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)
    
    try:
        import radproc.arcgis as _arcgis        
    except:
        # QGIS could be used instead some day...
        print("ArcGIS not available! Exit script!")
        sys.exit()
    
    # get RADOLAN binary file of first month in first year and read it in
    # needed to obtain the RADOLAN metadata
    yearFolders = [os.path.join(inFolder, yearDir) for yearDir in os.listdir(inFolder)]
    yearFolders = [yearDir for yearDir in yearFolders if os.path.isdir(yearDir)]
    
    firstMonthFolder = os.path.join(yearFolders[0], os.listdir(yearFolders[0])[0])
    dummyFile = os.path.join(firstMonthFolder, os.listdir(firstMonthFolder)[0])
    # Load first binary file to access header information
    data, metadata = _wrl_io.read_RADOLAN_composite(dummyFile)
    del data
    
    # different RADOLAN products have different grid sizes (e.g. 900*900 for the RADOLAN-Online national grid,
    # 1100*900 for the extended national grid used in the RADOLAN reanalysis)
    gridSize = metadata['nrow'] * metadata['ncol']
    
    idRasGermany = os.path.join(os.path.split(HDFFile)[0], "idras_ger")
    idRas = os.path.join(os.path.split(HDFFile)[0], "idras")
    
    projectionFile = _sampledata.get_projection_file_path()
    
    if gridSize == 900*1100:        
        extendedNationalGrid = True
    elif gridSize == 900*900:
        extendedNationalGrid = False
    
    idArr = _arcgis.create_idarray(projectionFile=projectionFile, idRasterGermany=idRasGermany, idRaster=idRas, clipFeature=clipFeature, extendedNationalGrid=extendedNationalGrid)
    
    # For every year folder...
    for yearFolder in yearFolders:
        _process_year(yearFolder=yearFolder, HDFFile=HDFFile, idArr=idArr, complevel=complevel)




def process_radolan_data(inFolder, HDFFile, idArr=None, complevel=9):
    """
    Converts all RADOLAN binary data into an HDF5 file with monthly DataFrames for a given study area without generating a new ID raster.
    
    All RADOLAN binary files in a directory tree are imported, 
    clipped to study area, converted into monthly pandas DataFrame and stored in an HDF5 file.
    
    The names for the HDF5 datasets are derived from the names of the input folders (year and month).
    The directory tree containing the raw binary RADOLAN data is expected to have the following format:
    
    *<inFolder>/<year>/<month>/<binaries with RADOLAN data>*
    
    --> *<inFolder>*/YYYY/MM
    
    --> *C:/Data/RADOLAN*/2008/5
    
    In this example, the output dataset will have the path 2008/5 within the HDF5 file.
    
    Additionally, a textfile containing all directories which could not be processed due to data format errors is created in directory of HDF5 file.
    
    
    :Parameters:
    ------------
    
        inFolder : string
            Path to the directory containing RADOLAN binary files stored in directory tree of following structure::
            *<inFolder>*/YYYY/MM --> *C:/Data/RADOLAN*/2008/5
        HDFFile : string
            Path and name of the HDF5 file.
            If the specified HDF5 file already exists, the new dataset will be appended; if the HDF5 file doesn't exist, it will be created. 
        idArr : one-dimensional numpy array (optional, default: None)
            containing ID values to select RADOLAN data of the cells located in the investigation area.
            If no idArr is specified, the ID array is automatically generated from RADOLAN metadata
            and RADOLAN precipitation data are not clipped to any investigation area.
        complevel : interger (optional, default: 9)
            defines the level of compression for the output HDF5 file.
            complevel may range from 0 to 9, where 9 is the highest compression possible.
            Using a high compression level reduces data size significantly,
            but writing data to HDF5 takes more time and data import from HDF5 is slighly slower.
        
    :Returns:
    ---------
    
        No return value
        Function creates datasets for every month in HDF5 file specified in parameter HDFFile.
        Additionally, a textfile containing all directories which could not be processed due to data format errors is created in HDFFolder.
        
    :Notes:
    -------
    See :ref:`ref-filesystem` for further details on data processing.
    
    This function can be used to process RADOLAN data without having ArcGIS installed.
    
    :Format description and examples:
    ---------------------------------    
        After the import, individual DataFrames can be loaded into memory from the generated HDF5 file using :func:`radproc.core.load_month` or
        several DataFrames within the same year can be loaded together using :func:`radproc.core.load_months_from_hdf5`
    
        Every row of the output DataFrames equals a precipitation raster of the investigation area at the specific date.
        Every column equals a time series of the precipitation at a specific raster cell.
        
        Data can be accessed and sliced with the following Syntax:
            
        **df.loc[row_index, column_name]**
        
        with row index as string in date format 'YYYY-MM-dd hh:mm' and column names as integer values
            
        **Examples::**
            
        >>> dataHDF5 = r'C:\Data\HDF5\RW.h5'
        >>> df = radproc.load_month(HDFFile=dataHDF5, year=2008, month=5)
        >>> df.loc['2008-05-01 00:50',414773] #--> returns single float value of specified date and cell
        >>> df.loc['2008-05-01 00:50', :] #--> returns entire row (= raster) of specified date as one-dimensional DataFrame
        >>> df.loc['2008-05-01', :] #--> returns DataFrame with all rows of specified day (because time of day is omitted)
        >>> df.loc[, 414773] #--> returns time series of the specified cell as Series
    
    """    
    # Ignore NaturalNameWarnings --> Group/Dataset names begin with number,
    # doesn't affect generation and access
    warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)
   
    # For every year folder...
    yearFolders = [os.path.join(inFolder, yearDir) for yearDir in os.listdir(inFolder)]
    yearFolders = [yearDir for yearDir in yearFolders if os.path.isdir(yearDir)]
    for yearFolder in yearFolders:
        _process_year(yearFolder=yearFolder, HDFFile=HDFFile, idArr=idArr, complevel=complevel)