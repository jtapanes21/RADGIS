from ..core.trajectorydataframe import *
from ..utils import constants, gislib, utils
import numpy as np
import pandas as pd


def azimuth(tdf, azimuth_diff=False):


    tdf = tdf.sort_by_uid_and_datetime().reset_index(drop=True)



    # Save the column names
    global column_names
    column_names = tdf.columns
    

    # Save the column indexes that will be used once the TrajDataFrame is converted to a multi-dimensional numpy array.

    #global time_index
    global lat_index
    global lon_index

    #time_index = tdf.columns.get_loc(constants.DATETIME) + 1
    lat_index = tdf.columns.get_loc(constants.LATITUDE)
    lon_index = tdf.columns.get_loc(constants.LONGITUDE)




    if utils.is_multi_user(tdf) == True:
        stdf = tdf.groupby(constants.UID, group_keys=False, as_index=False, sort=False).apply(_azimuth_work, azimuth_diff=azimuth_diff).reset_index(drop=True)
    else:
        stdf = _azimuth_work(tdf, azimuth_diff=azimuth_diff)


    #tdf = pd.DataFrame(stdf)
    


    
    # Name the dataframe's columns.
    #new_column_names = ["kph"]
    #new_column_names.extend(column_names)
    #tdf.columns = new_column_names

    stdf = TrajDataFrame(stdf, latitude=constants.LATITUDE, longitude=constants.LONGITUDE, datetime=constants.DATETIME, user_id=constants.UID)
    

    return stdf

def _azimuth_work(tdf, azimuth_diff=False):



    array = tdf.values



    lat1_ = (array[:,lat_index]).astype(float)
    lon1_ = (array[:,lon_index]).astype(float)

    lat2_ = (array[:,lat_index][1:]).astype(float)
    lat2_ = np.append(lat2_, np.nan)

    lon2_ = (array[:,lon_index][1:]).astype(float)
    lon2_ = np.append(lon2_, np.nan)


    lat1 = np.deg2rad(lat1_)
    lat2 = np.deg2rad(lat2_)

    diffLong = np.deg2rad(lon2_ - lon1_)

    x = np.sin(diffLong) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(diffLong))

    initial_bearing = np.arctan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180 to + 180 which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below

    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    np.put(compass_bearing, np.where(compass_bearing==0), compass_bearing[np.where(compass_bearing==0)[0] -1])
    compass_bearing = compass_bearing[...,np.newaxis]
    array = np.hstack((compass_bearing,array))

    if azimuth_diff == False:

        f = pd.DataFrame(array)


        new_column_names = ["azimuth"]
        new_column_names.extend(column_names)
        f.columns = new_column_names

        return f

    else:

        # Azimuth difference is the difference between each row's azimuth.
        # Not sure when I would use it, but could come in handy.

        comp = abs(abs((array[:,0][1:] - array[:,0][:-1])+180)% 360 - 180)
        comp = np.append(comp, np.nan)
        comp = comp[...,np.newaxis]
        array = np.hstack((comp,array))

        f = pd.DataFrame(array)


        new_column_names = ["azimuth_diff", "azimuth"]
        new_column_names.extend(column_names)
        f.columns = new_column_names

        return f

        
        

