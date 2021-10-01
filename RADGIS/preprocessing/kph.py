from ..core.trajectorydataframe import *
from ..utils import constants, gislib, utils
import numpy as np
import pandas as pd


def kph(tdf):


    tdf = tdf.sort_by_uid_and_datetime().reset_index(drop=True)



    # Save the column names
    global column_names
    column_names = tdf.columns
    

    # Save the column indexes that will be used once the TrajDataFrame is converted to a multi-dimensional numpy array.

    global time_index
    global lat_index
    global lon_index

    time_index = tdf.columns.get_loc(constants.DATETIME) + 1
    lat_index = tdf.columns.get_loc(constants.LATITUDE)
    lon_index = tdf.columns.get_loc(constants.LONGITUDE)




    if utils.is_multi_user(tdf) == True:
        stdf = tdf.groupby(constants.UID, group_keys=False, as_index=False, sort=False).apply(_kph_work).reset_index(drop=True)
    else:
        stdf = _kph_work(tdf)


    #tdf = pd.DataFrame(stdf)
    


    
    # Name the dataframe's columns.
    #new_column_names = ["kph"]
    #new_column_names.extend(column_names)
    #tdf.columns = new_column_names

    stdf = TrajDataFrame(stdf, latitude=constants.LATITUDE, longitude=constants.LONGITUDE, datetime=constants.DATETIME, user_id=constants.UID)
    

    return stdf

def _kph_work(tdf):



    array = tdf.values

    


    
    array = np.hstack((((gislib.haversine_np(array[:,lat_index],array[:,lon_index], array[:,lat_index][1:], array[:,lon_index][1:]))[...,np.newaxis]), array))


    
    #return time_index
    
    
    transportation_mode = array[:,time_index][1:] - array[:,time_index][:-1]
    transportation_mode = np.append(transportation_mode, np.timedelta64(0, "s"))
    transportation_mode = transportation_mode.astype("timedelta64[ms]").astype(int)/1000
    
    transportation_mode = transportation_mode[..., np.newaxis]
    
    array = np.hstack((transportation_mode, array))
    
    c = (np.divide((array[:,1]/1000), (array[:,0]/3600), out=np.zeros_like(array[:,1]), where=array[:,0]!=0))
    
    c = c[...,np.newaxis]
    array = np.hstack((c,array))
    
    # delete the time difference column
    array = np.delete(array, 1, 1)
    
    # delete the distance column
    
    array = np.delete(array, 1, 1)

    f = pd.DataFrame(array)



    new_column_names = ["kph"]
    new_column_names.extend(column_names)
    f.columns = new_column_names



    
    return f
