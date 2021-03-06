# Adapted from code & formulas by David Z. Creemer and others
# http://www.zachary.com/blog/2005/01/12/python_zipcode_geo-programming
# http://williams.best.vwh.net/avform.htm

from math import sin,cos,atan,acos,asin,atan2,sqrt,pi, modf
import csv
import numpy as np
from ..utils import constants
import pandas as pd




# At the equator / on another great circle???
nauticalMilePerLat = 60.00721
nauticalMilePerLongitude = 60.10793

rad = pi / 180.0

milesPerNauticalMile = 1.15078
kmsPerNauticalMile = 1.85200

degreeInMiles = milesPerNauticalMile * 60
degreeInKms = kmsPerNauticalMile * 60



# earth's mean radius = 6,371km
earthradius = 6371.0





def getDistance(loc1, loc2):
    "aliased default algorithm; args are (lat_decimal,lon_decimal) tuples"
    return getDistanceByHaversine(loc1, loc2)


def getDistanceByHaversine(loc1, loc2):
    "Haversine formula - give coordinates as (lat_decimal,lon_decimal) tuples"

    lat1, lon1 = loc1
    lat2, lon2 = loc2
    
    # convert to radians
    lon1 = lon1 * pi / 180.0
    lon2 = lon2 * pi / 180.0
    lat1 = lat1 * pi / 180.0
    lat2 = lat2 * pi / 180.0

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2.0))**2
    c = 2.0 * atan2(sqrt(a), sqrt(1.0-a))
    km = earthradius * c
    return km


    

def haversine_np(lat1, lon1, lat2, lon2, tdf=False):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    Returns an array aka a list with the distance in the first place:

    [100.0, nan]

    The distance is in meters. 

    """
    #lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    lat1 = np.deg2rad(np.float64(lat1))
    lon1 = np.deg2rad(np.float64(lon1))
    lat2 = np.deg2rad(np.float64(lat2))
    lon2 = np.deg2rad(np.float64(lon2))
    
    lat2 = np.append(lat2,np.nan)
    lon2 = np.append(lon2,np.nan)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km * 1000



def DecimalToDMS(decimalvalue):
    "convert a decimal value to degree,minute,second tuple"
    d = modf(decimalvalue)[0]
    m=0
    s=0
    return (d,m,s)


def DMSToDecimal(degrees,minutes,seconds):
    "Convert a value from decimal (float) to degree,minute,second tuple"
    d = abs(degrees) + (minutes/60.0) + (seconds/3600.0)
    if degrees < 0:
        return -d
    else:
        return d


def getCoordinatesForDistance(originlat, originlon, distance, units="km"):
    """return longitude & latitude values that, when added to & subtraced from
    origin longitude & latitude, form a cross / 'plus sign' whose ends are
    a given distance from the origin"""

    degreelength = 0

    if units == "km":
        degreelength = degreeInKms
    elif units == "miles":
        degreelength = degreeInMiles
    else:
        raise Exception("Units must be either 'km' or 'miles'!")

    lat = distance / degreelength
    lon = distance / (cos(originlat * rad) * degreelength)

    return (lat, lon)


def isWithinDistance(origin, loc, distance):
    "boolean for checking whether a location is within a distance"
    if getDistanceByHaversine(origin, loc) <= distance:
        return True
    else:
        return False

def load_spatial_tessellation(filename='location2info_trentino', delimiter=','):
    """
    Load into a dictionary the locations and corresponding information (latitude, longitude, relevance)
    Parameters
    ----------
    filename: str
        the filename where the location info is stored
    Returns
    -------
    dict
        the dictionary of locations
    """
    spatial_tessellation = {}
    f = csv.reader(open(filename), delimiter=delimiter)
    f.__next__()  # delete header
    i = 0
    for line in f:  # tqdm print a progress bar
        relevance = int(line[2])
        spatial_tessellation[i] = {constants.LATITUDE: float(line[0]),
                                       constants.LONGITUDE: float(line[1]),
                                       'relevance': relevance}
        i += 1
    return spatial_tessellation
