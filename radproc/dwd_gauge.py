# -*- coding: utf-8 -*-
"""
DWD MR90 gauge data processing
==============================

Collection of functions for processing DWD gauge data in MR90 format.

Convert gauge data to pandas DataFrames with same format as RADOLAN data and saves them as HDF5 datasets.

.. autosummary::
   :nosignatures:
   :toctree: generated/

    stationfile_to_df
    summarize_metadata_files
    dwd_gauges_to_hdf5


.. module:: radproc.dwd_gauge
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module arcgis
.. moduleauthor:: Jennifer Kreklow
"""

import numpy as np
import pandas as pd
import os, sys, gc
from datetime import datetime
from multiprocessing import Pool
import warnings, tables


def _read_line(line):
    """
    Read in one line (= 1 hour) of gauge data  according to MR90 format description.

    10-minute-blocks are merged to 60-minute-blocks and time index is shifted to make data hours begin at hh:50 and convert time zone from MEZ to UTC.


    :Parameters:
    ------------
    
        line : string
            data line containing station number, date and minute measurement data of weighing (Tropfer) and seesaw (Wippe) method in 10-minute-blocks.

        
    :Returns:
    ---------
    
        data : dictionary
            with data collected from line.
            keys: statnr, startdatum_dt (datetime-object), startdatum (string), dateIndex_UTC, wippe, tropfer, N_gefallen und qualitaetsbyte
    """   
    data = dict(wippe = "", tropfer = "")
    
    #data['kennung'] = line[0:2]
    data['statnr'] = line[2:7].strip()
    year = int(line[7:11])
    month = int(line[11:13])
    day = int(line[13:15])
    hour = int(line[15:17])
    data['startdatum_dt'] = datetime(year, month, day, hour)
    data['startdatum'] = data['startdatum_dt'].strftime("%Y-%m-%d %H:%M")
    # Erstellen einer einstündigen pandas TimeSeries mit fester minütlicher Frequenz
    # shift -70, da Beginn um xx:50 der Vorstunde und MEZ-1h = UTC       
    data['dateIndex_UTC'] = pd.date_range(start = data['startdatum'], periods = 60, freq = '1min').shift(-70).tolist()    
    #leerfeld = line[17:19]
    # Zusammenfügen der Messwerte aus den 10-Min-Blöcken zu einem 60-Min-String
    # Positionen der Liste (kennzeichnen jew. den Beginn eines Blocks) gem. Formatbeschreibung des DWD
    for wippe_start in [19, 100, 181, 262, 343, 424]:
            tropfer_start = wippe_start + 30  #Datensatz Wippe: 30 Zeichen
            N_gefallen_start = wippe_start + 70      # Datensatz Tropfer: 40 Zeichen
            #qualitaetsbyte = wippe_start + 80    #Datensatz Indikator: 10 Zeichen, Qualitätsbyte = 1 Zeichen --> gesamt: 81 Zeichen
                        
            data['wippe'] = data['wippe'] + line[wippe_start:tropfer_start]
            data['tropfer'] = data['tropfer'] + line[tropfer_start:N_gefallen_start]
            #daten['N_gefallen'] = daten['N_gefallen'] + line[N_gefallen_start:qualitaetsbyte]
            #daten['qualitaetsbyte'] = daten['qualitaetsbyte'] + line[qualitaetsbyte]            
            
    return data


def _interpret_line(data_dict):
    """
    Convert and decode data line of one hour from dictionary to pandas DataFrame.
    
    Decode data to precipitation values in mm,
    insert np.nan as NoData value where necessary and
    convert data to one-column DataFrame with time index
    
    :Parameters:
    ------------
    
        data_dict : dictionary
            with data collected from data line.
            necessary keys: statnr, dateIndex_UTC, wippe, tropfer
            dictionary can be read in with function _read_line()
    
        
    :Returns:
    ---------
    
        df : one-column pandas DataFrame
            with precipitation data of one hour in mm 
    
"""
    
    wippe = data_dict['wippe']
    tropfer = data_dict['tropfer']
    dateIndex = data_dict['dateIndex_UTC']
    arr = np.zeros(60, dtype = np.float32)
    arr.fill(np.nan)
    s = pd.Series(arr, index = dateIndex) 
    tropferNoData = 60 * "-999"
    #wippeNoData = 60 * "-99"
    # Interpretation der Daten:
    # Standardmäßig werden die Tropfermessungen ausgewertet und in pandas Series s eingefügt.
    # Ausnahme: alle 60 Zeitpunkte haben den Wert -999, also NoData. Nur dann wird auf die Wippenwerte zugegriffen.
    # Jeder Tropferwert besteht aus vier Zeichen. Diese werden nacheinander abgerufen und interpretiert.
    # -999 = Fehlkennung --> np.nan --> pass, da Series s bereits mit NaN initialisiert wurde
    # -001 = kein Niederschlag --> 0.0
    #   xx = xx * 0.01 mm Niederschlag
    # einige Zeitpunkte sind fehlerhaft und haben den Wert "0000". Diesen wird der Niederschalg 0.0 zugewiesen.
    if tropfer != tropferNoData:
        # Tropfermessung vorhanden
        k = 0
        
        for i in range(0, len(tropfer), 4):
            value = tropfer[i:i+4]
            if value == "-999":
                pass
            elif value == "-001" or value == "0000":
                s[dateIndex[k]] = 0.0
            else:
                try:
                    s[dateIndex[k]] = float(value)*0.01
                except:
                    s[dateIndex[k]] = np.nan
            k += 1
            
    else:
        # Wippenmessung vorhanden.
    # Jeder Wippenwert besteht aus drei Zeichen. Diese werden nacheinander abgerufen und interpretiert.
    # -99 = Fehlkennung --> np.nan
    # -01 = kein Niederschlag --> 0.0
    #  xx = xx * 0.1 mm Niederschlag
    # einige Zeitpunkte sind fehlerhaft und haben den Wert "000". Diesen wird der Niederschalg 0.0 zugewiesen.
        k = 0
        for i in range(0, len(wippe), 3):
            value = wippe[i:i+3]
            if value == "-99":
                pass
            elif value == "-01" or value == "000":
                s[dateIndex[k]] = 0.0
            else:
                try:
                    s[dateIndex[k]] = float(value)*0.1
                except:
                    s[dateIndex[k]] = np.nan
            k += 1
    # Umwandlung der Series in einen einspaltigen DataFrame.
    # Notwendig, um den Spaltennamen mit der Stationsnummer speichern zu können.
    df = pd.DataFrame(s.values, index = s.index, columns = [data_dict['statnr']])
    return df


def stationfile_to_df(stationfile):
    """
    Import a textfile with DWD rain gauge data in MR90 format into a one-column pandas DataFrame.

    Downsample frequency from 1 to 5-minute intervals to adjust temporal resolution to best-resolved RADOLAN data produt YW.
    Convert time zone to UTC.

    :Parameters:
    ------------
    
        stationfile : string
            Path and name of textfile containing rain gauge measurements.
    
        
    :Returns:
    ---------
    
        df : one-column pandas DataFrame
            with data imported from stationfile downsampled to 5-minute intervals.
            
"""
    #fails = []
    #for stationfile in stationfiles: --> unnötig, da map() beim parallel processing die Schleife ersetzt
    f = open(stationfile, "r")
    lines = f.readlines()
    f.close()
    df = pd.DataFrame()
    
    for line in lines:
        dataline = _read_line(line)        #erstelle Dictionary
        try:
            df_hour = _interpret_line(dataline)
            df_5min = df_hour.resample('5min', how = 'sum', closed = 'left', label = 'left')
            df = pd.concat([df,df_5min], axis = 0)
             
        except:
            # Hinweis: Ausgabe der Fehler funktioniert nicht bei Verwendung von Parallel Processing. Daher auskommentiert.
            #print "Problem bei Stunde beginnend um %s UTC in Station %s." % (str(daten['dateIndex_UTC'][0]), daten['statnr'])
            #fails.append((str(daten['dateIndex_UTC'][0]), daten['statnr']))
            continue
    del lines, df_hour, df_5min
    gc.collect()
    df = df.tz_localize('UTC')
    #print "Datei %s erfolgreich bearbeitet. Dauer: %.2f Minuten" % (stationfile, (time.time() - t0)/60)
    return df


def summarize_metadata_files(inFolder):
    """
    Import all metafiles and summarizes metadata in a single textfile.
    
    Metadata include information on station number and name, geographic coordinates and height above sea level.

    :Parameters:
    ------------
    
        inFolder : string
            Path of directory containing metadata files for DWD gauges.

        
    :Returns:
    ---------
    
        summaryFile : string
            Path and name of output summary file created.

    """
    
    metaFiles = [os.path.join(inFolder, mf) for mf in os.listdir(inFolder)]
    summaryFile = os.path.join(os.path.split(inFolder)[0], "metadata_summary.txt")
    outFile = open(summaryFile, "w")
    i = 0
    for f in metaFiles:
        infile = open(f, "r")
        
        while True:
            line = infile.readline().strip()
            if line.startswith("Station="):
                break
        #print line
        line = line.replace(":", " ")
        outFile.write(line[:-1] + "\n")
        infile.close()
        i += 1
    outFile.close()
    return summaryFile


def dwd_gauges_to_hdf5(inFolder, HDFFile):
    """
    Import all textfiles containing DWD rain gauge data in MR90 format from input folder into a DataFrame and save it as monthly HDF5 datasets.
    
    Frequency is downsampled from 1 to 5-minute intervals to adjust temporal resolution to RADOLAN product YW.
    Time zone is converted from MEZ to UTC.

    :Parameters:
    ------------
    
        inFolder : string
            Path of directory containing textfiles with DWD rain gauge data in MR90 format.
        HDFFile : string
            Path and name of the HDF5 file.
            If the specified HDF5 file already exists, the new dataset will be appended; if the HDF5 file doesn't exist, it will be created. 

        
    :Returns:
    ---------
    
        None
        Save monthly DataFrames to specified HDF5 file.
    """
    
    stationfiles = [os.path.join(inFolder, f) for f in os.listdir(inFolder)]
    #stationframes = []
    
    # Prozessierung der Stationsdateien mit Parallel Processing, um die Geschwindigkeit zu erhöhen.
    # Die Funktion Pool() aus dem Modul multiprocessing erzeugt mehrere Subprozesse auf unterschiedlichen Prozessorkernen,
    # welche die Multiprocessing-Sperre (GIL) umgehen, die normalerweise bei Python besteht.
    # map() nimmt eine Funktion und eine Liste als Eingabeargumente entgegen und gibt eine Liste
    # als Ausgabe zurück. Die Funktion wird auf unterschiedlichen Prozessorkernen für jedes Listenelement ausgeführt.
    # optional kann mit Pool(x) die Anzahl x der zu verwendenden Kerne übergeben werden.
    # Das Ergebnis stationframes ist eine Liste mit einspaltigen DataFrames der Ombrometerstationen.
    p = Pool()
    stationframes = p.map(stationfile_to_df, stationfiles)
    
    # Zusammenfügen der Dataframes zu einem  DF mit einer Spalte pro Station
    gaugeDF = pd.concat(stationframes, axis = 1, join = 'outer', copy=False)
    #ombroDF = ombroDF.asfreq('5min')
    gaugeDF.columns.name = 'DWD gauges'
    gaugeDF.index.name = 'Date (UTC)'

    #summaryFile = summarize_metadata_files(inFolder_metadata)
    warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)
    hdf = pd.HDFStore(HDFFile, mode = "a")

    for year in np.unique(gaugeDF.index.year):
        for month in xrange(1, 13):
            try:
                ind = "%i-%02i" %(year, month)
                HDFDataset = "%i/%i" %(year, month)
                hdf.put(HDFDataset, gaugeDF.loc[ind], data_columns = True, index = True)
            except:
                # in case of unavailable months
                continue
    
    hdf.close()
