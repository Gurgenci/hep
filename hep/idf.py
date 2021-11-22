#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 11:07:34 2021

@author: Hal Gurgenci

IDF File preparation and manipulation for Energy Plus simulations
"""
import platform
if platform.system()=='Darwin':
    EPLUS_DIR_PATH = '/Applications/EnergyPlus-9-5-0'
else:
    EPLUS_DIR_PATH = u"C:\EnergyPlusV9-5-0"
#
import numpy as np
import sys
import os
import pandas as pd
from  CoolProp.HumidAirProp import HAProps 
#
sys.path.insert(0, EPLUS_DIR_PATH)
from pyenergyplus.api import EnergyPlusAPI
api = EnergyPlusAPI()
#
from melib.xt import openplot, plotanno, saveplot

# Run data exchange
one_time = True
zone_temp_sensor = 0
power_level_actuator = 0

APILOG=0  # Log file pointer
def time_step_handler(state):
    global one_time, zone_temp_sensor, power_level_actuator 
    sys.stdout.flush()
    if one_time:
        if api.exchange.api_data_fully_ready(state):
            # val = api.exchange.list_available_api_data_csv()
            # with open('/tmp/data.csv', 'w') as f:
            #     f.write(val.decode(encoding='utf-8'))
            zone_temp_sensor = api.exchange.get_variable_handle(
                state, u"Zone Air Temperature", u"MAINZ"
            )
            # power_level_actuator = api.exchange.get_actuator_handle(
            #     state, "OtherEquipment", "Power Level", "TestOtherEquipment"
            # )
            if zone_temp_sensor == -1 or power_level_actuator == -1: 
                print(f'sensor or actuator not found temp = {zone_temp_sensor} and pow_level={power_level_actuator}')
                sys.exit(1)
            one_time = False
    zone_temp = api.exchange.get_variable_value(state, zone_temp_sensor)
    APILOG.write("%d, %.1f\n"%(state,zone_temp))
    # print("Reading outdoor temp via getVariable, value is: %s" % zone_temp)
    if zone_temp < 22:
        api.exchange.set_actuator_value(state, power_level_actuator, 0.0)
    else: 
        api.exchange.set_actuator_value(state, power_level_actuator, 1300.0)

    # sim_time = api.exchange.current_sim_time(state)
    # print("Current sim time is: %f" % sim_time)
    if api.exchange.zone_time_step_number(state) == 1:
        n = api.exchange.num_time_steps_in_hour(state)
        tomorrow_db = api.exchange.tomorrow_weather_outdoor_dry_bulb_at_time(state, 3, 2)
        # print(f"Num time steps in hour = {n}; Tomorrow's hour 3, timestep 2 temp is: {tomorrow_db}")


# IDF File Maker Functions
IDF=0

def newidf(filename, version="9.5", timestep=6):
    """
    

    Parameters
    ----------
    filename : string
        IDF file name to be created, for example `xxxx.idf`
    version : string, optional
        DESCRIPTION. The Energy Plus version.  The default is '9.5'
    timestep : int, optional
        DESCRIPTION. No of timesteps in an hour. The default is 6 (dt=10 mins). 

    Returns
    -------
    None.

    """
    global IDF
    IDF=open(filename, "w")
    IDF.write("! IDF file created by HG's idf.py script\n\n\
  Version,%s;\n\n\
  Timestep,%d;\n\n"%(version, timestep))


def idfclose():
    """
    Closes the IDF file created by an earlier `newidf` call.

    Returns
    -------
    None.

    """
    IDF.close()
  
  
def Building(name, north=0.0, terrain="Country", ltol=0.05, ttol=0.05, \
             solar="MinimalShadowing", maxwarmup=30, minwarmup=6):
    """
    

    Parameters
    ----------
    name : string
        Name of the building, e.g. 'mybuilding'.
    north : float, optional
        DESCRIPTION. The angle (degrees) from true North to building North.  The default is 0.0.
        The building North is Y-axis using default `GlobalGeometryRules`
    terrain : string, optional
        DESCRIPTION. The default is "Country".  This affects how the wind hits the building.
    ltol : float, optional
        DESCRIPTION. Warmup convergence for loads.  The default is 0.05.
        Do not change unless you have a good reason to.
    ttol : TYPE, Warmup convergence for temperatures.  The default is 0.05.
        Do not change unless you have a good reason to.
    solar : TYPE, optional
        DESCRIPTION. The default is "MinimalShadowing".  This means all beams
        entering the zone fal lon the floor; some gets absorbed by floor and the 
        rest becomes reflected diffuse radiation absorbed on all interior surfaces.
    maxwarmup : TYPE, optional
        DESCRIPTION. The default is 30.
    minwarmup : TYPE, optional
        DESCRIPTION. The default is 6.

    Returns
    -------
    None.

    """
    IDF.write("\
  Building,\n\
    %s,\n\
    %.1f,\n\
    %s,\n\
    %.2f,\n\
    %.2f,\n\
    %s,\n\
    %d,\n\
    %d;\n\n"%(name, north, terrain, ltol, ttol, solar, maxwarmup, minwarmup))
  
def Algorithms(heatbalance="ConductionTransferFunction", convin="TARP",\
               convout="DOE-2"):
    """
    

    Parameters
    ----------
    heatbalance : string, optional
        Heat and moisture transfer algorithm."ConductionTransferFunction" is default.
        This means a sensuibvle heat transfer only solution.
    convin : string, optional
        Models used for convection on surfaces. The default is "TARP".
        The TARP model is based on flat plate experiments.
    convout : string, optional
        Exterior surface convection model. The default is "DOE-2".
        DOE-2 uses correlations based on measurements from rough surfacers.
    Returns
    -------
    None.

    """
    IDF.write("\
  HeatBalanceAlgorithm,%s;\n\n\
  SurfaceConvectionAlgorithm:Inside,%s;\n\n\
  SurfaceConvectionAlgorithm:Outside,%s;\n\n"%(heatbalance, convin, convout))
  
def SimulationControl(zonesizing="No", systemsizing="No", plantsizing="No",
                      sizingsim="Yes", weathersim="Yes", hvacsizing="No", hvacruns=1):
    """
    

    Parameters
    ----------
    zonesizing : string, optional
        Do zone sizing calculation?. The default is "No".
    systemsizing : string, optional
        Combine individual zone sizing calcs into a system summary?. The default is "No".
    plantsizing : string, optional
        Does not use zone or system sizing arrays.  Therefore, can be 
        called on its own. The default is "No".
    sizingsim : string, optional
        Run simulate on ALL included SizingPeriod objects? The default is "Yes".
    weathersim : string, optional
        Run simulate on ALL included RunPeriod objects? The default is "Yes".
    hvacsizing : string, optional.  The default is "No"
    hvacruns : int, optional
        Used only if `hvacsizing` is 'Yes'.. The default is 1.

    Returns
    -------
    None.

    """
    IDF.write("\
  SimulationControl,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %d;\n\
\n"%(zonesizing, systemsizing, plantsizing, sizingsim, weathersim, hvacsizing, hvacruns))

def RunPeriod(name, month1=1, day1=1, year1="", month2=12, day2=31, year2="", \
              weekday="", holidays="No", daylightsaving="No", \
             weekends="No", rain="No", snow="No"):
    """
    

    Parameters
    ----------
    name : string
        Name to describe this run.
    month1 : int, optional
        Starting month. The default is 1 (i.e. January).
    day1 : int, optional
        Starting day of the month. The default is 1.
    year1 : string, optional
        If not specified, the yeear will be selected from other inpouts. The default is "".
    month2 : int, optional
        Ending month. The default is 12 (i.e. December).
    day2 : int, optional
        Ending day of the month. The default is 31.
    year2 : string, optional
        Specified only if year1 is specified. The default is "".
    weekday : string, optional
        If blank, the starting day type defaults to Sunday. The default is "".
    holidays : string, optional
        Consider holidays rules for holidays in the ewp file?. The default is "No".
    daylightsaving : string, optional
        Consider daylight saving?. The default is "No".
    weekends : string, optional
        Apply weekend holiday rule?. The default is "No".
    rain : string, optional
        Use the rain indicators in the ewp file?. The default is "No".
    snow : string, optional
        Use the snow indicators in the ewp file? The default is "No".

    Returns
    -------
    None.

    """
    IDF.write("  RunPeriod,\n\
    %s,\n\
    %d,\n\
    %d,\n\
    %s,\n\
    %d,\n\
    %d,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s,\n\
    %s;\n\
\n"%(name, month1, day1, year1, month2, day2, year2, weekday, holidays, daylightsaving,
weekends, rain, snow))
        
def Material(name, roughness="Smooth", t=0.003, k=5.0, rho=7850.0, cp=1000.0, ta=0.9,sa=0.7, va=0.7):
    """
    

    Parameters
    ----------
    name : string
        Name of the material.
    roughness : string, optional
        Surface roughness (for convection). The default is "Smooth".
    t : float, optional
        Thickness in meters (>0.003 m as per EPLUS IOREF). The default is 0.003.
    k : float, optional
        Thermal conductivity, W/m-K (E+ IOREF recommends <5). The default is 5.0.
    rho : float, , optional
        Density, kg/m3. The default is 7850.0.
    cp  : float, , optional
        Specific heat J/kg-K. The default is 1000.
    ta :  float, optional
        Thermal absorptance,. The default is 0.9.
    sa : float, optional
        Absorptance in the solar spectrum. The default is 0.7.
    va : float, optional
        Absorptance in the visible spectrum. The default is 0.7.
        
    Because of the limitations on k and t, this is probably not the right material
    for steel frames in greenhouses.  I can also try a NOMASS category for those
    frames.  They have thermal mass but they make up a small part of the structure.

    Returns
    -------
    None.

    """
    IDF.write("  Material,\n\
    %s,\n    %s,\n    %.3f,\n    %.1f,\n    %.0f,\n    %.0f,\n    %.2f,\n    %.2f,\n    %.2f;\n\n\
"%(name, roughness, t, k, rho, cp, ta, sa, va))

def MaterialNoMass(name, roughness="Smooth", Rth=0.001, ta=0.9,sa=0.7, va=0.7):
    """
     name : string
        Name of the material.
    roughness : string, optional
        Surface roughness (for convection). The default is "Smooth".
    Rth : float, , optional
        Thermal resistance, m2-K/W. The default is 0.001.
    ta :  float, optional
        Thermal absorptance,. The default is 0.9.
    sa : float, optional
        Absorptance in the solar spectrum. The default is 0.7.
    va : float, optional
        Absorptance in the visible spectrum. The default is 0.7.
        
    Returns
    -------
    None.

    """
    IDF.write("  Material:NoMass,\n\
    %s,\n    %s,\n    %.5f,\n    %.2f,\n    %.2f,\n    %.2f;\n\n\
"%(name, roughness, Rth, ta, sa, va))

def WindowMaterialGlazing(name="CLEAR 6MM", optics="SpectralAverage", dataset="",
     t=0.006, soltau=0.775, frontsolrho=0.071, backsolrho=0.071,
     vistau=0.881, frontvisrho=0.080, backvisrho=0.08,
     irtau=0.0, frontirhe=0.84, backirhe=0.84, k=0.9):
    """
    

    Parameters
    ----------
    name : string, optional
        Glazing material name. The default is "CLEAR 6MM".
    optics : string, optional
        Spectral optics data type. The default is "SpectralAverage".
    dataset : TYPE, optional
        Name of the spectral data set (if not SpectralAverage).
    t : float, optional
        Thickness, m. The default is 0.006.
    soltau : float, optional
        Solar transmittance at normal incidence (used only for SpectralAverage). The default is 0.775.
    frontsolrho : float, optional
        Front(outside) solar reflectance at normal incidence. The default is 0.071.
        Used only for SpectralAverage
    backsolrho : float, optional
        Back(inside) solar reflectance at normal incidence. The default is 0.071.
        Used only for SpectralAverage
    vistau : float, optional
        Transmittance weighted by human eye response. The default is 0.881.
        Used only for SpectralAverage
    frontvisrho : TYPE, optional
        Front-side Reflectance weighted by human eye response. The default is 0.080.
        Used only for SpectralAverage
    backvisrho : float, optional
        Back-side Reflectance weighted by human eye response. The default is 0.08.
        Used only for SpectralAverage
    irtau : float, optional
        DESCRIPTION. The default is 0.0.
    frontirhe : float, optional
        DESCRIPTION. The default is 0.84.
    backirhe : TYPE, optional
        DESCRIPTION. The default is 0.84.
    k : TYPE, optional
        DESCRIPTION. The default is 0.9.

    Returns
    -------
    None.

    """
    IDF.write("  WindowMaterial:Glazing,\n    %s,\n    %s,\n    %s,\n\
    %.3f,\n    %.3f,\n    %.3f,\n    %.3f,\n    %.3f,\n    %.3f,\n    %.3f,\n\
    %.3f,\n    %.3f,\n    %.3f,\n    %.3f;\n\n"%(name, optics, dataset,
    t, soltau, frontsolrho, backsolrho, vistau, frontvisrho, backvisrho,
    irtau, frontirhe, backirhe, k))

def Construction(name, *layers):
    """

    Parameters
    ----------
    name : string
        Name of this construction element, e.g. 'WALL', 'FLOOR', 'Roof'
    *layers : string
        Layers that make up this construction element.  The order is outside
        to inside.  For example, a concrete wall with steel cladding outside
        can be declared as `Construction('WALL', 'STEEL', 'CONCRETE').  The 
        strings 'STEEL' and 'CONCRETE' neds to eb defined as `Material`s.

    Returns
    -------
    None.

    """
    IDF.write("  Construction,\n    %s"%name)
    for s in layers:
        IDF.write(",\n    %s"%s)
    IDF.write(";\n\n")

def GroundTemperatureBuildingSurface(T):
    """

    Parameters
    ----------
    T : float array with 12 elements
        Monthly Ground temperatures in deg C.

    Returns
    -------
    None.

    """
    IDF.write("Site:GroundTemperature:BuildingSurface")
    for i in range(0, 12):
        IDF.write(",%.1f"%T[i])
    IDF.write(";\n\n")

def Zone(name, north=0.0, x=0.0, y=0.0, z=0.0, typ="", m=1.0, h="autocalculate",
         v="autocalculate",A="autocalculate",ica="", oca="", part="Yes"):
    """

    Parameters
    ----------
    name : string
        The name use to describe this zone. For a closed greenhouse, we will 
        start with a single zone, which may be named as GREENHOUSE
    north : float, optional
        Zone North Axis relative to the Building North. The default is 0.0.
    x : float, optional
        x coordinate of the zone origin wrt to the building origin. The default is 0.0.
    y : float, optional
        y coordinate of the zone origin wrt to the building origin. The default is 0.0.
    z : float, optional
        z coordinate of the zone origin wrt to the building origin. The default is 0.0.
    typ : string, optional
        Not used. The default is "".
    m : float, optional
        Multiplier for the load in HVAC sizing. The default is 1.0.
    h : float or string, optional
        The average height to the ceiling, m. The default is "autocalculate".
    v : float, optional
        Zone Volume, m3. The default is "autocalculate".
    A : float, optional
        Floor area, m2. The default is "autocalculate".
    ica : string, optional
        Inside convection algorithm. The default is "" (use what is specified in
        `SurfaceConvectionAlgorithm:Inside`)
    oca : string, optional
        Outside convection algorithm. The default is "" (use what is specified in
        `SurfaceConvectionAlgorithm:Outside`)
    part : string, optional
        Is this zone part of the total floor area? The default is "Yes".

    Returns
    -------
    None.

    """
    IDF.write("Zone,\n  %s,\n    %.1f,\n"%(name, north))
    IDF.write("    %.1f,\n    %.1f,\n    %.1f,\n"%(x,y,z))
    IDF.write("    %s,\n    %.1f,\n"%(typ,m))
    IDF.write("    %s,\n    %s,\n    %s,\n    %s,\n    %s,\n    %s;\n\n"%(h,v,A,ica,oca,part))
    
def GlobalGeometryRules(start="UpperLeftCorner", ved="CounterClockWise",
                        cs="World", drp="World", rsc="world"):
    """

    Parameters
    ----------
    start : string, optional
        Starting vertex position when defining surfaces. The default is "UpperLeftCorner".
    ved : string, optional
        Vertex entry direction. The default is "CounterClockWise".
    cs : string, optional
        Vertex coordinates. The default is "World".
    drp : string, optional
        Daylighting reference point coordinate system. The default is "World".
    rsc : string, optional
        Rectangular surface coordinate system. The default is "world".

    Returns
    -------
    None.

    """
    IDF.write("GlobalGeometryRules,\nUpperLeftCorner,\nCounterClockWise,\nWorld;\n\n")

def BuildingSurfaceDetailed(name, kind, coname, zoname, *v,\
    obc="Outdoors", obco="",\
    sun="SunExposed", wind="WindExposed", vfac=0,
    n=4):
    """
   
    Parameters
    ----------
    name : string
        The name we give to this surface.
    kind : string
        The type of this surface.  Acceptable types are Wall, Floor, Roof.
    coname : string
        Refers to the `Construction` object making up this surface.
    zoname : string
        This is the Zone class object this surface belongs.
    obc : string, optional
        Could be one of the following:
            Surface (for internal walls)
            Adiabatic (internal surface)
            Zone (the same as Surface but EP will automatically create the 
                  counterpart surface in the adjacent zone)
            Outdoors (for outside walls and roofs) -- Default
            Foundation (only used for a special foundation model)
            Ground (the temperature outside will be temperatures in the \
                    `GroundTemperatureBuildingSurface` object)
            OtherSideCOnditionsModel (Wal with attachments)
    obco : string, optional
        Outside Boundary Condition Object. The default is "".
        It is left blank if `obc` is set as 'Outside'
    sun : string
        'SunExposed' (default) or 'NoSun'
    wind : string
        'WindExposed' (default) or 'NoWind'
    vfac : float. Default=0
        View Factor to Ground
        Fraction of the ground visible by the surface:
            0.5 for the walls
            0.0 for the roof
            1.0 for horizontal down-facing surface
    n : No of vertices.  Default = 4
    *v : n triplets, one for each vertex.  See Figure 1.31 in IOReference for
        convention in terms of the vertex order and x,y,z measurements.
    Returns
    -------
    None.

    """    
    IDF.write("BuildingSurface:Detailed,\n  %s,\n  %s,\n"%(name, kind))
    IDF.write("  %s,\n  %s,\n  %s,\n  %s,\n"%(coname, zoname, obc, obco))
    IDF.write("  %s,\n  %s,\n"%(sun,wind))
    IDF.write("  %.2f,\n  %d,\n"%(vfac,n))
    # print("n : ", n, "  v : ",v)
    for i in range(0,n):
        IDF.write("  ")
        # print(i, " : ", v[i])
        IDF.write("%.3f, %.3f, %.3f"%(v[i][0], v[i][1], v[i][2]))
        if i==(n-1):
            IDF.write(";")
        else:
            IDF.write(",")
        IDF.write("  !- x%d,y%d,z%d {m}\n"%(i+1,i+1,i+1))
    IDF.write("\n")

def FloorAdiabatic(name,coname,zoname,L,W,x=0,y=0,z=0,azimuth=90,tilt=180):
    """
    

    Parameters
    ----------
    name : string
        The name we give to this surface.
    coname : string
        Refers to the `Construction` object making up this surface.
    zoname : string
        This is the Zone class object this surface belongs.
    L : float
        Length, m.
    W : float
        Width, m.
    x : float
        x for the lower left corner.
    y : float
        y for the lower left corner
    z : float
        z for the lower left cormer.
    azimuth : float
        Azimuth angle.  I do not what this means for a floor?  Examples use 90.
    tilt : float
        The tilt angle, the default is 180..

    Returns
    -------
    None.

    """
    IDF.write("Floor:Adiabatic,\
  %s,\n  %s,\n  %s,\n  %.0f,\n %.0f,\n  %.3f,\n  %.3f,\n  %.3f,\n  %.2f,\n\
  %.2f;\n\n"%(name, coname, zoname, azimuth, tilt, x, y, z, L, W))

def OutputControlFiles(**kwargs):
    """
    

    Parameters
    ----------
    **kwargs : string
        Keyword argumens to turn on output files, e.g. JSON="Yes"
        If you call with no arguments, only the following files will be output: 
            CSV, MTR, ESO, END

    Returns
    -------
    None.
    
    Example:
        OutputControlFiles(RDD="Yes")

    """
    oc={"CSV":"Yes", "MTR":"Yes", "ESO":"Yes", "EIO":"No","Tabular":"No", \
"SQLite":"No","JSON":"No","AUDIT":"No","Zone Sizing":"No","System Sizing":"No",
"DXF":"No","BND":"No","RDD":"No","MDD":"No","MTD":"No","END":"Yes","SHD":"No",
"DFS":"No","GLHE":"No","DelightIn":"No","DelightELdmp":"No","DelightDFdmp":"No",
"EDD":"No","DBG":"No","PerfLog":"No","SLN":"No","SCI":"No","WRL":"No",
"Screen":"No","ExtShd":"No","Tarcog":"No"}
    IDF.write("OutputControl:Files,\n")
    for key in kwargs:
        oc[key.upper()]=kwargs[key]
    n=len(oc.keys())
    for key in oc.keys():
        n-=1
        IDF.write(oc[key])
        if n>0:
            IDF.write(", ! %s\n"%( key))
        else:
            IDF.write("; ! %s\n"%(key))

def OutputVariable(interval, varnames):
    """
    

    Parameters
    ----------
    interval : string
        Frequency of reporting, e.g. "Hourly".
    varnames : string array
        Names of the variables to be reported

    Returns
    -------
    None.

    """
    for v in varnames:
        print(v)
        if type(v)==list:
            IDF.write("Output:Variable,%s,%s,%s;\n"%(v[0],v[1],interval))
        else:
            IDF.write("Output:Variable,*,%s,%s;\n"%(v,interval))

def idfrun(weatherfile, idfname, outputfolder="", log=False):
    """

    Parameters
    ----------
    weatherfile : string
        Weather file, e.g. 'longreach.epw'.
    idfname : string
        Name of the IDF file WITHOUT the extension, e.g. 'mybox'.
    outputfolder : string, optional
        Output folder name. Uses 'idfname' for "" (default)
    nb : Logical.  Default is False
        True if calling from a jupyter notebook

    Returns : None

    """
    if outputfolder=="":
        outputfolder=idfname
    idffile=idfname+".idf"
    api = EnergyPlusAPI()
    state = api.state_manager.new_state()
    if log:
        global APILOG
        APILOG=open(outputfolder+"/"+"apilog.csv","w")
        api.runtime.callback_end_zone_timestep_after_zone_reporting(state, time_step_handler)
        api.exchange.request_variable(state, u"Zone Air Temperature", u"ZONE ONE")

    print("initialization done")
    # if nb:
    #     shutil.copyfile('xxxx.idf', 'in.idf')  # copy the file to in.idf for ExpandObjects
    #     subprocess.check_call('/Applications/EnergyPlus-9-5-0/ExpandObjects')
    #     api.runtime.run_energyplus(state, ["-d", "output","-w",weatherfile, \
    #                                "xxxx_expanded.idf"])
    api.runtime.run_energyplus(state, ["-d", outputfolder,"-w",weatherfile, idffile])
    if log:
        APILOG.close()

def VariableDictionary():
    IDF.write("Output:VariableDictionary,IDF;\n\n")

def ridfout(outputfolder):
    """
    

    Parameters
    ----------
    outputfolder : string
        Name of the EP simulation output folder

    Returns
    -------
    The contents of the epout.csv file as a pandas data frame.

    """
    filename=os.path.join(outputfolder,"eplusout.csv")
    epout=pd.read_csv(filename)
    return epout
    # epout.columns=['date','tdbo','twbo',"wo","rho","ta","tai"]

if __name__ == "__main__":
    weatherfile="USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"
    weatherfile="longreach.epw"
    MAKEIDF=True
    RUNIDF=True
    
    if MAKEIDF:
        (H,W,L)=(10,50,100)
        zonename="MAINZ"
        wallcon="GHWALL" # Greenhouse wall. All walls have this construction
        steelroof="STEELROOF"
        concretefloor="CONCRETEFLOOR"
        idfname="xxxx.idf"
        newidf(idfname)
        Building("xxxx")
        Algorithms()
        SimulationControl(sizingsim="Yes")
        RunPeriod("Testing", month1=1, day1=1, year1=1979,\
                  month2=12, day2=31, year2=1979)
        MaterialNoMass("STEEL")
        Material("C5 - 4 in HW CONCRETE", "MediumRough", t=0.10, k=1.73, 
                 rho=224.2, cp=101., ta=0.9, sa=0.65, va=0.65)
        # cp=837, rho=2242
        WindowMaterialGlazing()
        Construction(wallcon, "C5 - 4 in HW CONCRETE", "STEEL")
        Construction(steelroof, "STEEL")
        Construction(concretefloor, "C5 - 4 in HW CONCRETE")
        GroundTemperatureBuildingSurface(np.ones(12)*20)
        Zone(zonename)
        GlobalGeometryRules()
        BuildingSurfaceDetailed("SouthWall", "Wall", wallcon, zonename,
        (0, 0, H), (0,0,0), (W, 0, 0), (W, 0, H))
        BuildingSurfaceDetailed("EastWall", "Wall", wallcon, zonename,
        (W, 0, H), (W,0,0), (W, L, 0), (W, L, H))
        BuildingSurfaceDetailed("NorthWall", "Wall", wallcon, zonename,
        (W, L, H), (W,L,0), (0, L, 0), (0, L, H))
        BuildingSurfaceDetailed("WestWall", "Wall", wallcon, zonename,
        (0, L, H), (0,L,0), (0, 0, 0), (0, 0, H))
        BuildingSurfaceDetailed("GHRoof", "Roof", steelroof, zonename,
        (0, 0, H), (W,0,H), (W, L, H), (0, L, H))
        # BuildingSurfaceDetailed("GHFloor", "Floor", concretefloor, zonename,
        # (W, 0, 0), (0,0,0), (0, L, 0), (W, L, 0))
        FloorAdiabatic("GHFloor", concretefloor, zonename, L=L, W=W)
        OutputControlFiles(RDD="Yes")
        outputvars=["Zone Mean Air Temperature",\
                    "Site Outdoor Air Drybulb Temperature",\
                        "Site Outdoor Air Wetbulb Temperature",\
                        "Site Outdoor Air Relative Humidity",\
                            ["GHFloor", "Surface Inside Face Temperature"],
                             ["GHRoof", "Surface Inside Face Temperature"],
                             ["SouthWall", "Surface Inside Face Temperature"],
                             ["EastWall", "Surface Inside Face Temperature"],
                             ["NorthWall", "Surface Inside Face Temperature"],
                             ["WestWall", "Surface Inside Face Temperature"],
                             "Site Sky Temperature"
                             ]
        OutputVariable("Hourly", outputvars)
        VariableDictionary()
    #    
        idfclose()
    if RUNIDF:
        from epw import newepwcolumn, readepwdata
        weatherfile="longreach.epw"
        idfname="xxxx"
        (tdb,rh, pat, vwind)=(20.0, 0.25, 100.0, 0)
        tdew=HAProps('D','T',tdb+273,'P', pat,'R',rh)-273
        newepwcolumn(weatherfile, "xxxx.epw", \
            ['dni', 'ghi', 'tdb', 'tdew', 'hiri', 'dhr', 'pat', 'rh', 'wisp'],\
                     [0.0, 0.0, tdb, tdew, 0.0, 0.0, pat*1000, rh*100, vwind])
        idfrun("xxxx.epw", "xxxx", log=False)
        dw=readepwdata("xxxx.epw")
        df=ridfout("xxxx")
        import matplotlib.pyplot as plt
        plothours=np.arange(0, 8000)
        labs={\
'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)':'Todb',
'Environment:Site Outdoor Air Wetbulb Temperature [C](Hourly)':'Towb',
'Environment:Site Outdoor Air Relative Humidity [%](Hourly)':'RHo',
'SOUTHWALL:Surface Inside Face Temperature [C](Hourly)':'TwS',
'EASTWALL:Surface Inside Face Temperature [C](Hourly)':"TwE",
'NORTHWALL:Surface Inside Face Temperature [C](Hourly)':"TwN",
'WESTWALL:Surface Inside Face Temperature [C](Hourly)':"TwW",
'GHFLOOR:Surface Inside Face Temperature [C](Hourly)':"Tflr",
'GHROOF:Surface Inside Face Temperature [C](Hourly)':"Troof",
'MAINZ:Zone Mean Air Temperature [C](Hourly)':"Ti",
'Environment:Site Sky Temperature [C](Hourly)':"Tsky"}
        (f1,ax)=openplot(1,0.5)
        for i in range(1, len(df.columns)):
            s=df.columns[i]
            ax.plot(plothours, df[s][plothours], label=labs[df.columns[i]])
            print("average(%s) = %.1f"%(s, np.average(df[s])))
        plotanno(ax, xlabel="Hours", ylim=[0, 30.0], legendloc="upper left")
        plt.show()
    
#
#   Run
    # api = EnergyPlusAPI()
    # state = api.state_manager.new_state()
    # print("initialization done")
    # api.runtime.run_energyplus(state, ["-d", "xxxx","-w",weatherfile, idfname])
    
# api = EnergyPlusAPI()
# state = api.state_manager.new_state()
# # api.runtime.callback_end_zone_timestep_after_zone_reporting(state, time_step_handler)
# # api.exchange.request_variable(state, u"Zone Air Temperature", u"ZONE ONE")
# print("initialization done")
# # trim off this python script name when calling the run_energyplus function so you end up with just
# # the E+ args, like: -d /output/dir -D /path/to/input.idf
# #api.runtime.run_energyplus(state, sys.argv[1:])
# idffile=".\Exercise1D-Solution_lib_mode.idf"
# idffile="xxxx.idf"
# if __name__ == "__main__":
#     api.runtime.run_energyplus(state, ["-d", "output", "-w","USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw", \
#     idffile])
        
    
    
    
    
    
    
    
    
    
    
    
    
