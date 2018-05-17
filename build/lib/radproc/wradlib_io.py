# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2016, wradlib developers.
# Distributed under the MIT License. See LICENSE.txt for more info.

"""
============================
 RADOLAN Binary File Import
============================

Copy of all functions necessary for reading in RADOLAN composite files, taken from module wradlib.io (version=0.9.0)

(Heistermann, M., Jacobi, S., and Pfaff, T. 2013:
Technical Note: An open source library for processing weather radar data (wradlib),
Hydrol. Earth Syst. Sci., 17, 863-871)

Copying these functions was necessary in order to reduce number of dependencies
and avoid conflicts arising between different GDAL installations required for other wradlib modules and ArcGIS.

.. autosummary::
   :nosignatures:
   :toctree: generated/

   read_RADOLAN_composite

   
.. module:: radproc.wradlib_io
    :platform: Windows
    :synopsis: Python package radproc (Radar data processing), Module wradlib_io
.. moduleauthor:: Jennifer Kreklow

"""

# standard libraries
from __future__ import absolute_import
import datetime as dt

try:
    import io
except ImportError:
    import io

import warnings

# site packages
import numpy as np
import gzip


def get_radolan_filehandle(fname):
    """Opens radolan file and returns file handle

    Parameters
    ----------
    fname : string
        filename

    Returns
    -------
    f : object
        filehandle
    """

    #gzip = util.import_optional('gzip') --> um Funktion zu "sparen" direkter Import von gzip oben

    # open file handle
    try:
        f = gzip.open(fname, 'rb')
        f.read(1)
    except IOError:
        f = open(fname, 'rb')
        f.read(1)

    # rewind file
    f.seek(0, 0)

    return f


def read_radolan_header(fid):
    """Reads radolan ASCII header and returns it as string

    Parameters
    ----------
    fid : object
        file handle

    Returns
    -------
    header : string
    """
    # rewind, just in case...
    fid.seek(0, 0)

    header = ''
    while True:
        mychar = fid.read(1)
        if mychar == b'\x03':
            break
        header += str(mychar.decode())
    return header


def get_radolan_header_token():
    """Return array with known header token of radolan composites

    Returns
    -------
    head : dict
        with known header token, value set to None
    *JP: 'VR': None added for new data format *
    """
    head = {'BY': None, 'VS': None, 'SW': None, 'PR': None,
            'INT': None, 'GP': None, 'MS': None, 'LV': None,
            'CS': None, 'MX': None, 'BG': None, 'ST': None,
            'VV': None, 'MF': None, 'VR': None}
    return head


def get_radolan_header_token_pos(header):
    """Get Token and positions from DWD radolan header

    Parameters
    ----------
    header : string
        (ASCII header)

    Returns
    -------
    head : dictionary
        with found header tokens and positions
    """

    head_dict = get_radolan_header_token()

    for token in head_dict.keys():
        d = header.rfind(token)
        if d > -1:
            head_dict[token] = d
    head = {}

    result_dict = {}
    result_dict.update((k, v) for k, v in head_dict.items() if v is not None)
    for k, v in head_dict.items():
        if v is not None:
            start = v + len(k)
            filt = [x for x in result_dict.values() if x > v]
            if filt:
                stop = min(filt)
            else:
                stop = len(header)
            head[k] = (start, stop)
        else:
            head[k] = v

    return head




def parse_DWD_quant_composite_header(header):
    """Parses the ASCII header of a DWD quantitative composite file

    Parameters
    ----------
    header : string
        (ASCII header)

    Returns
    -------
    output : dictionary
        of metadata retrieved from file header
        
    ------------------------------------------------------------    
    *JP: if k == 'VR': 
                out['reanalyseversion'] = str(header[v[0]:v[1]])
    added for new data format and if k == 'INT': block replaced
    """
    # empty container
    out = {}

    # RADOLAN product type def
    out["producttype"] = header[0:2]
    # file time stamp as Python datetime object
    out["datetime"] = dt.datetime.strptime(header[2:8] + header[13:17] + "00",
                                           "%d%H%M%m%y%S")
    # radar location ID (always 10000 for composites)
    out["radarid"] = header[8:13]

    # get dict of header token with positions
    head = get_radolan_header_token_pos(header)
    # iterate over token and fill output dict accordingly
    # for k, v in head.iteritems():
    for k, v in head.items():
        if v:
            if k == 'BY':
                out['datasize'] = int(header[v[0]:v[1]]) - len(header) - 1
            if k == 'VS':
                out["maxrange"] = {0: "100 km and 128 km (mixed)",
                                   1: "100 km",
                                   2: "128 km",
                                   3: "150 km"}.get(int(header[v[0]:v[1]]),
                                                    "100 km")
            if k == 'SW':
                out["radolanversion"] = header[v[0]:v[1]].strip()
            if k == 'PR':
                out["precision"] = float('1' + header[v[0]:v[1]].strip())
                
            #if k == 'INT':
                #out["intervalseconds"] = int(header[v[0]:v[1]]) * 60
                
            if k == 'INT':
                intervalfaktor = 60 #Stunden
                if header[v[0]:v[1]][-2] == "U":
                    if header[v[0]:v[1]][-1] == 1:
                        intervalfaktor = 60 * 24 #Tage 
                        out["intervalseconds"] = int(header[v[0]:v[1]-2]) * intervalfaktor
                else:
                    out["intervalseconds"] = int(header[v[0]:v[1]]) * intervalfaktor



            
            if k == 'GP':
                dimstrings = header[v[0]:v[1]].strip().split("x")
                out["nrow"] = int(dimstrings[0])
                out["ncol"] = int(dimstrings[1])
            if k == 'BG':
                dimstrings = header[v[0]:v[1]]
                dimstrings = (dimstrings[:int(len(dimstrings) / 2)],
                              dimstrings[int(len(dimstrings) / 2):])
                out["nrow"] = int(dimstrings[0])
                out["ncol"] = int(dimstrings[1])
            if k == 'LV':
                lv = header[v[0]:v[1]].split()
                out['nlevel'] = np.int(lv[0])
                out['level'] = np.array(lv[1:]).astype('float')
            if k == 'MS':
                locationstring = (header[v[0]:].strip().split("<")[1].
                                  split(">")[0])
                out["radarlocations"] = locationstring.split(",")
            if k == 'ST':
                locationstring = (header[v[0]:].strip().split("<")[1].
                                  split(">")[0])
                out["radardays"] = locationstring.split(",")
            if k == 'CS':
                out['indicator'] = {0: "near ground level",
                                    1: "maximum",
                                    2: "tops"}.get(int(header[v[0]:v[1]]))
            if k == 'MX':
                out['imagecount'] = int(header[v[0]:v[1]])
            if k == 'VV':
                out['predictiontime'] = int(header[v[0]:v[1]])
            if k == 'MF':
                out['moduleflag'] = int(header[v[0]:v[1]])
            if k == 'VR': 
                out['reanalyseversion'] = str(header[v[0]:v[1]])

    return out



def read_radolan_binary_array(fid, size):
    """Read binary data from file given by filehandle

    Parameters
    ----------
    fid : object
        file handle
    size : int
        number of bytes to read

    Returns
    -------
    binarr : string
        array of binary data
    """
    binarr = fid.read(size)
    fid.close()
    if len(binarr) != size:
        raise IOError('{0}: File corruption while reading {1}! \nCould not '
                      'read enough data!'.format(__name__, fid.name))
    return binarr


def decode_radolan_runlength_array(binarr, attrs):
    """Decodes the binary runlength coded section from DWD composite
    file and return decoded numpy array with correct shape

    Parameters
    ----------
    binarr : string
        Buffer
    attrs : dict
        Attribute dict of file header

    Returns
    -------
    arr : :func:`numpy:numpy.array`
        of decoded values
    """
    buf = io.BytesIO(binarr)

    # read and decode first line
    line = read_radolan_runlength_line(buf)
    arr = decode_radolan_runlength_line(line, attrs)

    # read following lines
    line = read_radolan_runlength_line(buf)

    while line is not None:
        dline = decode_radolan_runlength_line(line, attrs)
        arr = np.vstack((arr, dline))
        line = read_radolan_runlength_line(buf)
    # return upside down because first line read is top line
    return np.flipud(arr)




def read_radolan_runlength_line(fid):
    """Reads one line of runlength coded binary data of DWD
    composite file and returns it as numpy array

    Parameters
    ----------
    fid : object
        file/buffer id

    Returns
    -------
    line : :func:`numpy:numpy.array`
        of coded values
    """
    line = fid.readline()

    # check if eot
    if line == b'\x04':
        return None

    # convert input buffer to np.uint8 array
    line = np.frombuffer(line, np.uint8).astype(np.uint8)

    return line


def decode_radolan_runlength_line(line, attrs):
    """Decodes one line of runlength coded binary data of DWD
    composite file and returns decoded array

    Parameters
    ----------
    line : :func:`numpy:numpy.array`
        of byte values
    attrs : dict
        dictionary of attributes derived from file header

    Returns
    -------
    arr : :func:`numpy:numpy.array`
        of decoded values
    """
    # byte '0' is line number, we don't need it
    # so we start with offset byte,
    lo = 1
    byte = line[lo]
    # line empty condition, lf directly behind line number
    if byte == 10:
        return np.ones(attrs['ncol'], dtype=np.uint8) * attrs['nodataflag']
    offset = byte - 16

    # check if offset byte is 255 and take next byte(s)
    # also for the offset
    while byte == 255:
        lo += 1
        byte = line[lo]
        offset += byte - 16

    # just take the rest
    dline = line[lo + 1:]

    # this could be optimized
    # iterate over line string, until lf (10) is reached
    for lo, byte in enumerate(dline):
        if byte == 10:
            break
        width = (byte & 0xF0) >> 4
        val = byte & 0x0F
        # the "offset pixel" are "not measured" values
        # so we set them to 'nodata'
        if lo == 0:
            arr = np.ones(offset, dtype=np.uint8) * attrs['nodataflag']
        arr = np.append(arr, np.ones(width, dtype=np.uint8) * val)

    trailing = attrs['ncol'] - len(arr)
    if trailing > 0:
        arr = np.append(arr, np.ones(trailing,
                                     dtype=np.uint8) * attrs['nodataflag'])
    elif trailing < 0:
        arr = dline[:trailing]

    return arr



def read_RADOLAN_composite(fname, missing=-9999, loaddata=True):
    """Read quantitative radar composite format of the German Weather Service

    The quantitative composite format of the DWD (German Weather Service) was
    established in the course of the
    RADOLAN project and includes several file
    types, e.g. RW, YW, RY, RX, RZ, and many, many more.
    (see format description on the RADOLAN project homepage).

    Originally, the national RADOLAN composite was a 900 x 900 grid with 1 km
    resolution and in polar-stereographic projection.
    But for the reanalysis within the radar climatology project finished in 2017 the national grid was extended to 1100 x 900 cells.
    There are other grid resolutions for other composites, too (e.g. PC, PG).

    Warning
    -------
    This function already evaluates and applies the so-called
    PR factor which is specified in the header section of the RADOLAN files.
    The raw values in an RY oder YW file are in the unit 0.01 mm/5min, while
    read_RADOLAN_composite returns values in mm/5min (i. e. factor 100 higher).
    The factor is also returned as part of attrs dictionary under
    keyword "precision".

    Parameters
    ----------
    fname : string
        path to the composite file
    missing : int
        value assigned to no-data cells
    loaddata : bool
        True | False, If False function returns (None, attrs)

    Returns
    -------
    output : tuple
        tuple of two items (data, attrs):

            - data : numpy array of shape (number of rows, number of columns)
            - attrs : dictionary of metadata information from the file header

    """

    NODATA = missing
    mask = 0xFFF  # max value integer

    f = get_radolan_filehandle(fname)

    header = read_radolan_header(f)

    attrs = parse_DWD_quant_composite_header(header)

    if not loaddata:
        f.close()
        return None, attrs

    attrs["nodataflag"] = NODATA

    if not attrs["radarid"] == "10000":
        warnings.warn("WARNING: You are using function e" +
                      "wradlib.io.read_RADOLAN_composit for a non " +
                      "composite file.\n " +
                      "This might work...but please check the validity " +
                      "of the results")

    # read the actual data
    indat = read_radolan_binary_array(f, attrs['datasize'])

    if attrs['producttype'] in ['RX', 'EX', 'WX']:
        # convert to 8bit integer
        arr = np.frombuffer(indat, np.uint8).astype(np.uint8)
        arr = np.where(arr == 250, NODATA, arr)
        attrs['cluttermask'] = np.where(arr == 249)[0]
    elif attrs['producttype'] in ['PG', 'PC']:
        arr = decode_radolan_runlength_array(indat, attrs)
    else:
        # convert to 16-bit integers
        arr = np.frombuffer(indat, np.uint16).astype(np.uint16)
        # evaluate bits 13, 14, 15 and 16
        attrs['secondary'] = np.where(arr & 0x1000)[0]
        nodata = np.where(arr & 0x2000)[0]
        negative = np.where(arr & 0x4000)[0]
        attrs['cluttermask'] = np.where(arr & 0x8000)[0]
        # mask out the last 4 bits
        arr &= mask
        # consider negative flag if product is RD (differences from adjustment)
        if attrs['producttype'] == 'RD':
            # NOT TESTED, YET
            arr[negative] = -arr[negative]
        # apply precision factor
        # this promotes arr to float if precision is float
        arr = arr * attrs['precision']
        # set nodata value
        arr[nodata] = NODATA

    # anyway, bring it into right shape
    arr = arr.reshape((attrs['nrow'], attrs['ncol']))

    return arr, attrs

