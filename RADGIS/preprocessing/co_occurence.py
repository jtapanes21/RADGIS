from ..core.trajectorydataframe import *
from RADGIS.preprocessing import clustering
from ..utils import constants
import pandas as pd
import numpy as np
from collections import namedtuple
from datetime import datetime

def co_occurence(tdf, group_column, epsilon_size=.1, time_column=constants.DATETIME, lat_column=constants.LATITUDE, lon_column=constants.LONGITUDE, min_column=None, max_column=None, simple=False):
    tdf = tdf.copy()

    if min_column != None:
        tdf = _stop_co_occurence(tdf=tdf, group_column=group_column, epsilon_size=epsilon_size, time_column=time_column, lat_column=lat_column, lon_column=lon_column, min_column=min_column, max_column=max_column, simple=simple)
    else:
        tdf = _co_occurence(tdf=tdf, group_column=group_column, epsilon_size=epsilon_size, time_column=time_column, lat_column=lat_column, lon_column=lon_column, simple=simple)


    #Clean the column names

    #tdf.drop(["co_stops", "co_test", "co_counter"], inplace=True, axis=1)

    # Test the return from the above functions to make sure they returned a dataframe.

    if type(tdf) != str:

        tdf = TrajDataFrame(tdf, latitude=constants.LATITUDE, longitude=constants.LONGITUDE, datetime=constants.DATETIME, user_id=constants.UID)
    else:
        pass
    


    return tdf



# This function is used on the result of the travel_analysis script. 

def _stop_co_occurence(tdf, group_column, epsilon_size, time_column, lat_column, lon_column, min_column, max_column, simple):



    # Have to convert from a TrajDataFrame back to a pandas DataFrame for the merge on multi-index to work.


    '''
    Don't need this because the input is from the travel_analysis script and not the numpy stop detection.
    '''
    #tdf = pd.DataFrame(tdf)

    # Filter the dataframe by removing all non-stops determined by the stop detection module. The global
    # variable constants.STOP_TIME is used, which is set in the detection module.

    '''
    Don't need this because the input is from the travel_analysis script and not the numpy stop detection.
    '''
    #tdf = tdf[tdf[constants.STOP_TOTAL_SECONDS]>=constants.STOP_TIME]

    # Make a copy to later join the co-occurence results to.
    tdf_copy = tdf.copy()
    
    '''
    Don't need this because the input is from the travel_analysis script and not the numpy stop detection.
    '''

    #tdf = tdf.drop_duplicates([group_column, lat_column, lon_column, min_column, max_column])

    #tdf.reset_index(drop=True, inplace=True)





    tdf = clustering.dbscan_clustering(tdf, "Co_Occurence", epsilon_size, min_sample=2, lat_column=lat_column, lon_column=lon_column)



    # Remove non-clusters:
    tdf = tdf[tdf["Co_Occurence"]!= -1]

    tdf.sort_values(by=["Co_Occurence"], inplace=True)
    tdf.reset_index(drop=True,inplace=True)

    # Identify if multiple user ids are within the same space.
    tdf["testing"] = tdf.groupby(["Co_Occurence"], sort=False)[group_column].transform(lambda x: x.diff().ne(0))
    # Top of each group automatically labeled as True. Change it to False
    tdf.loc[tdf.groupby("Co_Occurence", sort=False)["testing"].head(1).index, "testing"] = False

    # Build out the index for where there is co-occurence within space.
    idx1 = tdf.index[tdf["testing"]==True]
    # Only one of the identified multi user ids was labeled so add the index above to include the complete index.
    idx2 = idx1 - 1
    # Merge the indexes and drop duplicates.
    idx3 = idx2.append(idx1)
    idx3 = idx3.drop_duplicates()

    # Filter the dataframe to only include co-occurence candidates.
    tdf = tdf.loc[idx3]
    
    # Save a new dataframe with duplicates dropped, which speeds up processing time.
    #tdf_2 = tdf.drop_duplicates(["Co_Occurence", group_column, min_column, max_column])

    # Make a dictionary that has each group ident, Co_Occurence group, and the min-max range.
    
    d = {}

    Range = namedtuple('Range', ['start', 'end'])

    for i in tdf["Co_Occurence"].unique():
        d[i] = [{tdf[group_column][j] : Range(start=tdf[min_column][j], end=tdf[max_column][j])} for j in tdf[tdf["Co_Occurence"]==i].index]

    




    def _finder(row0, row1, row2, row3, dict_):
        f = []
        Range = namedtuple('Range', ['start', 'end'])
        for key, value in dict_.items():
            if key == row0:
                for k in value:
                    for key2, value2 in k.items():
                        
                        if key2 != row1:
                            
                            if simple == True:
                                f.append(key2)

                            else:
                            
                                r1 = value2
                                r2 = Range(start=row2, end = row3)
                                
                                latest_start = max(r1.start, r2.start)
                                earliest_end = min(r1.end, r2.end)

                                if latest_start <= earliest_end:
                                
                                    delta = (earliest_end - latest_start).seconds
                                
                                    p = {key2:delta}
                                    f.append(p)
                            
                  


        if len(f)>0:
            return f
        else:
            return "No"

    tdf["co_occurence"] = [_finder(row[0], row[1], row[2], row[3], d) for row in tdf[["Co_Occurence", group_column, min_column, max_column,]].values]


    tdf = tdf.set_index([group_column, min_column, max_column, "group_ident"])

    tdf = tdf[["co_occurence", "Co_Occurence"]]

    tdf_copy = tdf_copy.set_index([group_column, min_column, max_column, "group_ident"])

    new_tdf = tdf_copy.merge(tdf, right_index=True, left_index=True)

    #new_tdf = new_tdf["co_occurence"].dropna()
    

    new_tdf = new_tdf[new_tdf["co_occurence"]!="No"]

    new_tdf.reset_index(inplace=True)

    if len(tdf) != 0:
        return tdf
    else:
        return "No co-occurence detected."




    




    

    

def _co_occurence(tdf, group_column, epsilon_size, time_column, lat_column, lon_column, simple):

    
    tdf = clustering.dbscan_clustering(tdf, "Co_Occurence", epsilon_size, min_sample=4, lat_column=lat_column, lon_column=lon_column)

    tdf.sort_values(by=[time_column], inplace=True)
    tdf.reset_index(drop=True,inplace=True)

    tdf["co_test"] = tdf.groupby([group_column], sort=False)["Co_Occurence"].transform(lambda x: x.diff().ne(0).cumsum())
    tdf = tdf[tdf.Co_Occurence != -1]
    tdf["co_stops"] = tdf.groupby([group_column],sort=False)["co_test"].transform(lambda x: x.diff().ne(0).cumsum())

    tdf = tdf.join(tdf.groupby([group_column, "co_stops"], sort=False).size().rename("co_counter"), on=[group_column, "co_stops"], how="outer").sort_values(time_column)

    # In this algorithm, co-occurence can only occur if there are two stops with different group idents. For a stop to be a stop, again according to this algorithm, there must be at least two points - a start and end point.
    # For this reason, the dataframe is filtered to only include potential stops with at least two points.
    def _co_occurence_checker(row0, row1):
        if row1 > 1:
            return row0
        else:
            return np.NaN

    tdf["co_stops"] = [_co_occurence_checker(row[0], row[1]) for row in tdf[["co_stops", "co_counter"]].values]
    tdf = tdf[tdf.co_stops.notnull()]

    # Stop the code and return a string if there are no stops detected.

    if len(tdf) == 0:
        return "No co-occurence detected."
    else:
        pass



    # Prepare for the below step by sorting and resetting the index.
    tdf.sort_values(by=["Co_Occurence"], inplace=True)
    tdf.reset_index(drop=True,inplace=True)

    # Identify if multiple user ids are within the same cluster:
    tdf["testing"] = tdf.groupby(["Co_Occurence"], sort=False)[group_column].transform(lambda x: x.diff().ne(0))
    
    # Top of each group automatically labeled as True. Change it to False
    tdf.loc[tdf.groupby("Co_Occurence", sort=False)["testing"].head(1).index, "testing"] = False

    # Only return cluster groups that have a True value aka there were at least two different user ids within the cluster. If this was not satisified at all then return a string and stop.


    tdf = tdf.groupby(["Co_Occurence"], sort=False).filter(lambda x: (x.testing == True).any())

    if len(tdf) == 0:
        return "No co-occurence detected."
    else:
        pass


    
    # Provide a min and max datetime for each stop group.
    tdf = tdf.join(tdf.groupby([group_column, "Co_Occurence", "co_stops"], sort=False)[time_column].min().rename("min"), on=[group_column, "Co_Occurence", "co_stops"], how="outer").sort_values(time_column)
    tdf = tdf.join(tdf.groupby([group_column, "Co_Occurence", "co_stops"], sort=False)[time_column].max().rename("max"), on=[group_column, "Co_Occurence", "co_stops"], how="outer").sort_values(time_column)

    #tdf["min"] = tdf.groupby([group_column,"co_stops"], sort=False)[time_column].min()
    #tdf["max"] = tdf.groupby([group_column,"co_stops"], sort=False)[time_column].max()

    
    # Make a copy of the dataframe that will be used later. Results will be joined back to this copy.

    tdf_copy = tdf.copy()

    # Remove the duplicates from the dataframe. This will speed up processing, but will also ensure that we do not get duplicate co-occurence values back.

    tdf = tdf.drop_duplicates([group_column, "Co_Occurence", "co_stops"])





     # Make a dictionary that has each group ident, Co_Occurence group, and the min-max range.
    

    d = {}

    Range = namedtuple('Range', ['start', 'end'])

    for i in tdf["Co_Occurence"].unique():
        d[i] = [{tdf[group_column][j] : Range(start=tdf["min"][j], end=tdf["max"][j])} for j in tdf[tdf["Co_Occurence"]==i].index]



    def _finder(row0, row1, row2, row3, dict_):
        f = []
        Range = namedtuple('Range', ['start', 'end'])
        for key, value in dict_.items():
            if key == row0:
                for k in value:
                    for key2, value2 in k.items():
                        
                        if key2 != row1:
                            
                            if simple == True:
                                f.append(key2)

                            else:
                            
                                r1 = value2
                                r2 = Range(start=row2, end = row3)
                                
                                latest_start = max(r1.start, r2.start)
                                earliest_end = min(r1.end, r2.end)

                                if latest_start <= earliest_end:
                                
                                    delta = (earliest_end - latest_start).seconds
                                
                                    p = {key2:delta}
                                    f.append(p)
                            
                  


        if len(f)>0:
            return f
        else:
            return "No"


    tdf["co_occurence"] = [_finder(row[0], row[1], row[2], row[3], d) for row in tdf[["Co_Occurence", group_column, "min", "max",]].values]


    # Merge the copied dataframe with the results. Have to rename two columns since they are made into the index.

    tdf["Co_Occurence_"] = tdf["Co_Occurence"]
    tdf["co_stops_"] = tdf["co_stops"]
    tdf[group_column + "_"] = tdf[group_column]
    
    tdf = tdf.set_index([group_column+"_", "Co_Occurence_", "co_stops_"])

    tdf = tdf[["co_occurence"]]

    tdf_copy["Co_Occurence_"] = tdf_copy["Co_Occurence"]
    tdf_copy["co_stops_"] = tdf_copy["co_stops"]
    tdf_copy[group_column + "_"] = tdf_copy[group_column]

    tdf_copy = tdf_copy.set_index([group_column + "_", "Co_Occurence_", "co_stops_"])

    new_tdf = tdf_copy.merge(tdf, right_index=True, left_index=True)


    


    # Only return the dataframe if there was co-occurence.

    new_tdf = new_tdf[new_tdf["co_occurence"]!="No"]

    new_tdf.reset_index(drop=True, inplace=True)

    new_tdf.drop(["co_test", "testing"], axis=1, inplace=True)

    if len(new_tdf) != 0:
        return new_tdf
    else:
        return "No co-occurence detected."


    








    

    """for i in tdf["Co_Occurence"].unique():
        d[i] = [{tdf[group_column][j] : tdf[time_column][j]} for j in tdf[tdf["Co_Occurence"]==i].index]

    def _finder(row0, row1, row2, row3, dict_):
        f = []
        for key, value in dict_.items():
            if key == row0:
                for k in value:
                    for key2, value2 in k.items():
                        if key2 != row1:
                            if (value2 >= row2):
                                if (value2 <= row3):
                                    p = {key2:value2}
                                    f.append(p)


        if len(f)>0:
            return f
        else:
            return "No"


    tdf["co_occurence"] = [_finder(row[0], row[1], row[2], row[3], d) for row in tdf[["Co_Occurence", group_column, "min", "max",]].values]

    tdf = tdf[tdf["co_occurence"] != "No"].reset_index(drop=True)
    tdf.drop(["co_stops", "co_test", "co_counter"], inplace=True, axis=1)
    return tdf
    """





    
