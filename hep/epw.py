#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 09:14:00 2021

Scripts to work with EPW files (EnergyPlus Weather files)

@author: melizgurgenci
"""

import numpy as np
import melib
from melib.xt import plotanno, openplot
import pandas as pd
# from  CoolProp.HumidAirProp import HAPropsSI  # For Humid Air properties import HAPropsSI  # For Humid Air properties
from  CoolProp.HumidAirProp import HAProps 

epwdata={}   # We will skip the header lines and read the rest into here
# The following are the long descriptions for the epw data line columns
# The units are default units in energyplus epw files
# My source for EPW file format : 
#    https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
def columnname(s):
    """
    Parameters
    ----------
    s : string
        epw dataframe column index (short name)
        

    Returns
    -------
    Description or the long name as a string if s!="all"
    All descriptions as an array of strings if s=="all"
    
    The units are default units in energyplus epw files
    My source for EPW file format : 
    https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm
    """
#
    
    column_descriptions={
    "Y":"Year", "M":"Month","D":"Day","H":"Hour","m":"Minute",
    "flags":"Data source and uncertainti flags",
    "tdb":"Dry bulb temperature,°C",
    "tdew":"Dew point temperature, °C",
    "rh":"Relative humidity, %",
    "pat":"Atmospheric pressure, Pa",
    "xhr":"Extraterrestrial horizontal readiation, Wh/m2",
    "xdni":"Extraterrestrial direct normal radiation, Wh/m2",
    "hiri":"Horizontal Infrared Radiation Intensity, Wh/m2",
    "ghi":"Global Horizontal Radiation",
    "dni":"Direct Normal Radiation, Wh/m2",
    "dhr":"Diffuse Horizontal Radiation, Wh/m2",
    "ghil":"Global Horizontal Illuminance, lux",
    "dnil":"Direct Normal Illuminance, lux",
    "dhil":"Diffuse Horizontal Illuminance, lux",
    "zl":"Zenith Luminance, Cd/m2",
    "widir":"Wind Direction, degrees (N = 0.0, East = 90.0, etc)",
    "wisp":"Wind Speed, m/s",
    "tsc":"Total Sky Cover, amount of sky dome in tenths covered by clouds or obscuring phenomena",
    "osc":"Opaque Sky Cover (used if to compute 'hiri', if 'hiri' is missing)",
    "vis":"Visibility,km.  Currently unused by eplus",
    "ch":"Ceiling Height, m.   Currently unused by eplus",
    "pwo":"Present Weather Observation, 0(weather from next field) or 9(missing weather)",
    "pwc":"Present Weather Codes (codes for rain, storm, etc)",
    "pw":"Precipitable Water,mm.  Unused.",
    "aod":"Aerosol Optical Depth, thousandths. Unused.",
    "sd":"Snow Depth, cm",
    "sls":"Days Since Last Snowfall.  Unused.",
    "alb":"Albedo, ratio  of reflected solar irradiance to GHI. Unused.",
    "lpd":"Liquid Precipitation Depth, mm.  If not missing, overrides the precipitation flag as rainfall.",
    "lpq":"Liquid Precipitation Quantity. Unused."
    }
    if s.upper()=="ALL":
        return list(column_descriptions.values())
    else:
        return column_descriptions[s]
    
def plotepw(filename, cols, months=[], days=[]):
    """
    _Parameters_
    filename : `string`
        Name of the EP Weather file, e.g. `longreach.epw`.
    cols : Array of `string`s, e.g. ['dni', 'ghi']
        EPW file columns to be plotted.
    months : `int` array, optional
        Plot only for these months. The default is [], which means all 12 months.
        e.g. `months=[3,4,5]` will plot for the months March, April and May.
    days : `int` array, optional
        Plot only for these days of the months. The default is [], which means all.

    _Returns_ : None
    
    Example:
        >>>plotepw('xxxx.epw', ['tdb', 'tdew'])

    """
    global epwdata
    readepwdata(filename)
    filt=[]
    if not months==[]:
        filt=epwdata['M'].isin(months)
    if not days==[]:
        filt=filt&epwdata['D'].isin(days)
    if filt==[]:
        df=epwdata
    else:
        df=epwdata[filt]
    (f1,ax)=openplot(1,0.5)
    for col in cols:
        y=list(df[col])
        ax.plot(np.arange(0,len(y)), y, label=col)
    plotanno(ax, legendloc="upper right", grid="on")
    
def newepwfile(oldfile, newfile, newdf):
    """
    _Parameters_
    oldfile : `string`
        Name of the original EP Weather file, e.g. longreach.epw
    newfile : `string`
        Name of the new EP Weather file, e.g. longreach.epw
    newdf : Data Frame (in `readepwdata` format)
        New data frame.  Usually we read the data frame from the original file
        and modify data as required.

    _Returns_ : None
    """
    fdx1=open(oldfile)
    fdx2=open(newfile, "w")
    for n in range(0, 8): # Skip first 8 lines
        s=fdx1.readline()
        fdx2.write(s)
    newdf.to_csv(fdx2, header=False, index=False)
    fdx2.close()
    fdx1.close()

# def zeroepwcolumn(oldfile, newfile, cols):
#     readepwdata(oldfile)
#     for col in cols:
#         epwdata[col]=np.zeros(len(epwdata))
#     newepwfile(oldfile, newfile, epwdata)
    
def newepwcolumn(oldfile, newfile, cols, values):
    """
    _Parameters_
    oldfile : `string`
        Name of the original EP Weather file, e.g. longreach.epw
    newfile : `string`
        Name of the new EP Weather file, e.g. xxxx.epw
    cols : Array of `string`s
        EPW file columns to be set to a fixed value, e.g. ['dni', 'tdb']
    values : Array of `float`s, e.g.[0.0, 100.0]
        Fixed value for each column in the argument 'cols'.

    _Returns_ : None
    """
    readepwdata(oldfile)
    for col, v in zip(cols, values):
        epwdata[col]=np.ones(len(epwdata))*v
    newepwfile(oldfile, newfile, epwdata)

def readepwdata(filename):
    """
    _Parameters_
    filename : `string`
        EP Weather data file name, e.g. `lopngreach.epw`.

    _Returns_ : The data frame (which is also stored in the global `epwdata`)
    """
    global epwdata
    epwdata=pd.read_csv(filename, skiprows=8, header=None)
    epwdata.columns=\
    ["Y","M","D","H","m","flags","tdb","tdew","rh","pat","xhr",  # 0-10
     "xdni","hiri","ghi","dni","dhr","ghil","dnil","dhil","zl","widir", # 11-20
     "wisp","tsc","osc","vis","ch","pwo","pwc","pw","aod","sd",  # 21-30
     "sls","alb","lpd","lpq"     
    ]
    return epwdata

# def makenewboxfile(origfile, n):
#     colrevise=[[],['dni', 'ghi']]
#     if n>1:
#         cols=colrevise[n-1]
#         newfile="%s%03d.epw"%(origfile,n)
#         cols=['dni', 'ghi']
#         zeroepwcolumn(origfile, newfile, cols)
        
# def idfparvalues(origfile, newfile, parnames, parvalues):

#     with open(origfile, 'r') as infile, open(newfile, 'w') as outfile:
#         for line in infile:
#             print(line[0:-1], end="")
#             for p,v in zip(parnames, parvalues):
#                 print("(%s,%s)"%(p,v), end="")
#                 value=v
#                 line=line.replace(p,value)
#             outfile.write(str(line))

        

    
    