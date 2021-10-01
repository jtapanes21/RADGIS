from ..utils import gislib, utils, constants
from ..core.trajectorydataframe import *
import numpy as np
import pandas as pd



def stops(tdf, stop_radius_meters=20, minutes_for_a_stop=10):
    
    """ Stops detection
    
    Detect the stops for each individual in a TrajDataFrame. A stop is 
    detected when the individual spends at least 'minutes_for_a_stop' minutes
    within a distance 'stop_radius_meters' from a given trajectory point.
    The stop's coordinates are the median latitude and longitude values
    of the points found within the specified distance.
    
    Parameters
    ----------
    tdf : TrajDataFrame
        the input trajectories of the individuals.
    
    stop_radius_meters : integer, optional
        the minimum distance between two consecutive points to be considered
        a stop. The default is 20 meters.
    
    minutes_for_a_stop : integer, optional
        the minimum stop duration, in minutes. The default is '10' minutes.
    
    no_data_for_days : integer, optional
        if the number of minutes between two consecutive points is larger
        than 'no_data_for_days', then this is interpreted as missing data
        and dows not count as a stop or a trip.
        
    Returns
    -------
    
    TrajDataFrame
        a TrajDataFrame with the coordinates (latitude, longitude) of
        the stop locations.
    
    """
    
    
    
    # convert the minutes_for_a_stop variable to seconds.
    
    minutes_for_a_stop = minutes_for_a_stop * 60

    # Update the STOP_TIME global variable in the constants .py file. This is used for the co-occurence script.

    constants.STOP_TIME = minutes_for_a_stop
    
    # Sort
    
    tdf = tdf.sort_by_uid_and_datetime()
    
    # Reset the index.
    
    tdf.reset_index(drop=True, inplace=True)
    
    # Order the columns; important for numpy operations where column numbers are used.
    # Add a "uid" column name if not multi_user.
    if utils.is_multi_user(tdf) == False:
        tdf["uid"] = 1
    else:
        pass
    
    tdf = utils.column_order(tdf, "timestamp", "latitude", "longitude", "uid")
    

    
    
    stdf = _stops_array(tdf, stop_radius_meters, minutes_for_a_stop)
    
    return stdf
    
    
    
    
    
def _stops_array(tdf, stop_radius_meters, minutes_for_a_stop):
    
    # Save the column names
    column_names = tdf.columns.to_list()
    
    # From dataframe convert to a numpy matrix.
    array = tdf.values
    
    # Save the uid edge index. This is used to overwrite the distance that spans from one
    # uid to the next uid. Three is the column that contains the uid.
    uid_edge_index = np.where(np.diff(array[:,3]))
    
    # Haversine distance calculation is added as a column to the array.
    array = np.hstack((((gislib.haversine_np(array[:,1],array[:,2], array[:,1][1:], array[:,2][1:]))[...,np.newaxis]), array))
    
    # Use the 'uid_edge_index' to assign very large distance to the edge of each uid.
    # This ensures that the uids remain separate.
    np.put(array[:,0], uid_edge_index[0], 99999999)
    
    # Identify stop candidates using distance. Retain the index of the rows that are less than
    # the 'stop_radius_meters' distance. Add a unique ident to the rows that meet this distance threshold.
    array = np.hstack((((np.where(array[:,0] > stop_radius_meters, array[:,0], (np.where(array[:,0] <= stop_radius_meters, -1111, np.nan))))[...,np.newaxis]), array))
    
    # Save the indicies that meet the distance threshold.
    old_stop_index = np.where(array[:,0] == -1111)
    
    # Add a unique ident for each candidate stop group. The stop group was previously
    # identified using distance and labeled -1111.
    np.put(array[:,0],np.where(array[:,0] == -1111), np.cumsum(np.not_equal((np.concatenate(([0], np.array(np.where(array[:,0] == -1111))[0])))[:-1], (np.concatenate(([0], np.array(np.where(array[:,0] == -1111))[0])))[1:]-1)))
    
    # The last row in the candidate stop group is not initially labeled with the stop group ident.
    put_index = old_stop_index[0]+1
    put_values = array[:,0][old_stop_index[0]]
    np.put(array[:,0], put_index, put_values)
    
    # Save the complete stop group index to a variable for later use.
    old_stop_index_complete = np.unique(np.concatenate((old_stop_index[0],put_index),0))
    
    # Filter the original array to only include the candidate stops.
    stop_cand = array[old_stop_index_complete]
    
    """ "Chaining" is a common problem that simple stop detection algorithms experience. Chaining
    is when false stops are identified that are most commonly the result of walking especially
    with highly sampled datasets. For example, a gps beacon set to ping every five seconds is
    considered highly sampled data. To a simple distance and time stop detection algorithm, walking 
    would look like a stop: little distance between each consecutive point until the person speeds up at
    which point the begining of the walk to the end would be considered the stop per the distance component 
    of the algorithm. It is likely that the time component of the algorithm would also be satified where the time
    difference from the begining to the end of the distance break are summed. Thus, long walks, with highly sampled
    data, can be falsly labeled as stops. These false stops have the appearence of linear chains hence the term "chaining".
    
    I use a primitive method to combat chaining. The method is not perfect, but the positives outweigh the negatives.
    The method is to select a large, relative to the original distance threshold, max distance and generate intra-group groups
    using the cumulative sum of each consecutive distance within each group. The mean latitude and longitude are then taken
    for each intra-group. If the mean coordinates are within a distance threshold of the next consecutive intra-group, then
    the intra-groups are merged. This distance threshold is larger than the original distance threshold selected by the user, 
    but smaller than the cumulative sum max distance. Esentially the original groups are broken into smaller intra-groups
    and then re-merged if the mean center of the intra-groups are less than the distance threshold.
    
    This method combats the chaining effects that occur with highly sampled datasets. If a highly sampled GPS stops, then there
    should be many pings within a close distance of eachother. Many detects will have large azimuth changes from GPS error or
    the user moving within a stop location. But in the end, breaking these pings up into intra-groups, their mean center will 
    be close to eachother. This is not the case with a walk.
    
    
    
    """
    
    # Edit the distance column before the groups are broken up into intra-groups.
    # Change all 0s to 1s and round up to whole numbers. This is done so that
    # the modulo operator will work to create the increasing pattern, which is
    # how the intra-groups are created. Yes, rounding up and changing 0s to 1s
    # is inaccurate, but we accept this small inaccuracy. 
    
    # Also, replace all nans with 1s
    stop_cand[:,1][np.isnan(stop_cand[:,1].astype(float))]=1
    stop_cand[:,1] = np.round(np.int64(np.float64(stop_cand[:,1])))
    stop_cand[:,1][stop_cand[:,1] == 0] = 1
    
    # Get the counts of each stop group size.
    
    users = np.float64(stop_cand[:,0])
    unames, idx, counts = np.unique(users, return_inverse=True, return_counts=True)
    
    """ What are we about to do and why?
    This block is a way to do a one-level groupby on our data and make 
    the cumsum on each groupby reset at a certain limit. The limit is 
    taken using the modulo. Overall this code was taken from a different 
    application where the modulo worked differently. But this still kind of 
    works for our purposes to create a pattern of increasing to decreasing on 
    the reset. It seems to work better with a larger limit aka like 100 or 200 
    meters. 
    
    Why do this? This might not need to be done with sparse data. But with 
    highly sampled GPS data where a new sample is taken ever 5-60 seconds this 
    is helpful to remove false positive stops. Specfically, where someone walks
    slowly. Without doing this, the walk might be determined to be a stop.
    
    """
    # Added the condition in the two below cumsum functions. Because if there
    # was only one stop candidate in the array we do not do the minus bc it would
    # be out of range.
    
    def _intervaled_cumsum(ar, sizes):
        # Make a copy to be used as output array
        out = ar.copy()

        # Get cumumlative values of array
        arc = ar.cumsum()

        # Get cumsumed indices to be used to place differentiated values into
        # input array's copy
        idx = sizes.cumsum()

        # Place differentiated values that when cumumlatively summed later on would
        # give us the desired intervaled cumsum
        
        # This condition is for when there is only one stop candidate. 
        # The minus of the index would be out of range.
        if len(idx) > 1:
            out[idx[0]] = ar[idx[0]] - arc[idx[0]-1]
            out[idx[1:-1]] = ar[idx[1:-1]] - np.diff(arc[idx[:-1]-1])
            limit = 50
            return out.cumsum() % limit
        else:
            limit = 50
            return ar.cumsum() % limit
    
    # Similar function as above but returns the pattern of each group.
    def _intervaled_cumsum2(ar, sizes):
        # Make a copy to be used as output array
        out = ar.copy()

        # Get cumumlative values of array
        arc = ar.cumsum()

        # Get cumsumed indices to be used to place differentiated values into
        # input array's copy
        idx = sizes.cumsum()

        # Place differentiated values that when cumumlatively summed later on would
        # give us the desired intervaled cumsum
        
        # This condition is for when there is only one stop candidate.
        # The minus of the index would be out of range.
        if len(idx) > 1:
            out[idx[0]] = ar[idx[0]] - arc[idx[0]-1]
            out[idx[1:-1]] = ar[idx[1:-1]] - np.diff(arc[idx[:-1]-1])
            return (np.where(np.diff(out) > 0)[0] + 1)
        else:
            return (np.where(np.diff(ar) > 0)[0] + 1)
    
    # Start to break each group into a sub-group by taking the cumsum of each group's
    # distance and reseting it once the distance threshold is met. The reset is done
    # by using the modulo operator. In reality it does not reset it, but the pattern changes
    # from an increasing number to then a smaller number, which is the reset.
    stop_cand = np.hstack((((_intervaled_cumsum(stop_cand[:,1], counts))[...,np.newaxis]), stop_cand))
    
    # Get the sub_group index and use it to assign a unique number, in our case -111111,
    # back to the filtered array.
    pattern = _intervaled_cumsum2(stop_cand[:,0], counts)
    np.put(stop_cand[:,0], pattern, -111111)
    
    # The subgroups are almost complete, but each sub-group contains one row that
    # was not assigned the unique ident. Assign this row the unique ident.
    old_cumsum_index = np.where(stop_cand[:,0] == -111111)
    old_cumsum_index_shifted = old_cumsum_index[0] - 1
    
    # Get the index that is not in one of these variables.
    back_fill_index = np.setdiff1d(old_cumsum_index_shifted, old_cumsum_index)
    
    # Create the complete index.
    combined_indexes =  np.unique(np.concatenate((old_cumsum_index[0],old_cumsum_index_shifted),0))
    
    # Save the index of the previous stops that were not given a unique ident.
    forgotten_guys = np.setdiff1d(np.arange(len(stop_cand)), combined_indexes)
    
    # Create the inque idents.
    np.put(stop_cand[:,0],np.where(stop_cand[:,0] == -111111), np.cumsum(np.not_equal((np.concatenate(([0], np.array(np.where(stop_cand[:,0] == -111111))[0])))[:-1], (np.concatenate(([0], np.array(np.where(stop_cand[:,0] == -111111))[0])))[1:]-1)))
    np.put(stop_cand[:,0], back_fill_index, (stop_cand[:,0])[back_fill_index + 1] )
    
    # insert a unique ident for the previous stops that were not 
    # given a unique ident. This is not 100 mandatory but is good 
    # practice to avoid having the not given stop ident having the same 
    #value as the preceding or following value, which would mess up the 
    #cumsum unique ident.
    np.put(stop_cand[:,0], forgotten_guys, -111111)
    
    # Add unique idents again. This fixes the problem of the previous not labeled stop groups.
    np.put(stop_cand[:,0], np.arange(len(stop_cand)), np.cumsum(np.not_equal((np.concatenate(([0], stop_cand[:,0])))[:-1], (np.concatenate(([0], stop_cand[:,0])))[1:])))
    
    # Latitude mean center.
    lat_column = np.float64(stop_cand[:,4])
    lat_users = np.float64(stop_cand[:,0])
    unames, idx, counts = np.unique(lat_users, return_inverse=True, return_counts=True)
    sum_pred = np.bincount(idx, weights=lat_column)
    mean_pred_lat = sum_pred / counts
    # Add it to the array.
    mean_pred_lat = mean_pred_lat[..., np.newaxis]
    stop_cand = np.hstack((mean_pred_lat[idx],stop_cand))
    
    # Longitude mean center.
    lon_column = np.float64(stop_cand[:,6])
    lon_users = np.float64(stop_cand[:,1])
    unames, idx, counts = np.unique(lon_users, return_inverse=True, return_counts=True)
    sum_pred = np.bincount(idx, weights=lon_column)
    mean_pred_lon = sum_pred / counts
    # Add it to the array.
    mean_pred_lon = mean_pred_lon[..., np.newaxis]
    stop_cand = np.hstack((mean_pred_lon[idx],stop_cand))
    
    # Run the distance meansurment again, but this time on the mean center of the intra-groups.
    distance_2 = gislib.haversine_np(stop_cand[:,1],stop_cand[:,0], stop_cand[:,1][1:], stop_cand[:,0][1:])
    distance_2 = distance_2[...,np.newaxis]
    stop_cand = np.hstack((distance_2,stop_cand))
    
    # Insert impossible distances between stop group edges.
    unames, idx, counts = np.unique(stop_cand[:,4], return_inverse=True, return_counts=True)
    group_breaks = np.cumsum(counts) - 1
    np.put(stop_cand[:,0], group_breaks, 9999999)
    
  
    
    # Make the groups again using a slighly larger distance threshold than the user previously specified.
    # Use the original stop radius meters provided by the user, but increase it by 40%.
    increased_radius = (stop_radius_meters * .40) + stop_radius_meters
    temp_dist_2 = np.where(stop_cand[:,0] > increased_radius, stop_cand[:,0], (np.where(stop_cand[:,0] <= increased_radius, -1111, np.nan)))
    temp_dist_2 = temp_dist_2[..., np.newaxis]
    stop_cand = np.hstack((temp_dist_2,stop_cand))
    old_stop_index_2 = np.where(stop_cand[:,0] == -1111)
    np.put(stop_cand[:,0],np.where(stop_cand[:,0] == -1111), np.cumsum(np.not_equal((np.concatenate(([0], np.array(np.where(stop_cand[:,0] == -1111))[0])))[:-1], (np.concatenate(([0], np.array(np.where(stop_cand[:,0] == -1111))[0])))[1:]-1)))
    put_index_2 = old_stop_index_2[0]+1
    put_values_2 = stop_cand[:,0][old_stop_index_2[0]]
    np.put(stop_cand[:,0], put_index_2, put_values_2)
    
    #Sometimes only one record is leftover after the cumsum. This fixes that by
    # identifying those records and assigning them to the above group.
    unames, idx, counts = np.unique(stop_cand[:,4], return_inverse=True, return_counts=True)
    group_breaks2 = np.cumsum(counts) - 1
    np.put(stop_cand[:,0], group_breaks2, stop_cand[:,0][group_breaks2-1])
    
    # Test these new groups for time.
    filtered_array_time = stop_cand
    
    
    filtered_array_time_diff = filtered_array_time[:,7][1:] - filtered_array_time[:,7][:-1]
    filtered_array_time_diff = np.append(filtered_array_time_diff, np.timedelta64(0,"s"))
    filtered_array_time_diff = filtered_array_time_diff.astype("timedelta64[ms]").astype(int)/1000
    filtered_array_time_diff = filtered_array_time_diff[...,np.newaxis]
    stop_cand = np.hstack((filtered_array_time_diff,stop_cand))
     # make a copy of the time difference column that will be used later.
    copied = stop_cand[:,0][...,np.newaxis]
    stop_cand = np.hstack((copied, stop_cand))
    # The edge of the new groups.
    tester = np.where(np.diff(filtered_array_time[:,0])!=0)
    np.put(stop_cand[:,1], tester[0], 0)
    filtered_array_time_diff2 = stop_cand
    time_column = np.float64(filtered_array_time_diff2[:,1])
    users_3 = np.float64(filtered_array_time_diff2[:,2])
    # assign integer indices to each unique user name, and get the total
    # number of occurrences for each name
    unames, idx, counts = np.unique(users_3, return_inverse=True, return_counts=True)
    # now sum the values of pred corresponding to each index value
    sum_pred = np.bincount(idx, weights=time_column)
    add_time = sum_pred[idx]
    add_time = add_time[...,np.newaxis]
    filtered_array_time_diff2 = np.hstack((add_time, filtered_array_time_diff2))


    # Identify stops that occur with just two points that might not be detected
    # using the cumsum.
    
    tester3 = np.where(np.diff(filtered_array_time_diff2[:,8])==1)[0]
    np.put(filtered_array_time_diff2[:,1], tester3, 0)
    
    # Add a new placeholder column made up of 1s.
    filtered_array_time_diff2 = np.c_[np.ones(len(filtered_array_time_diff2)) ,filtered_array_time_diff2]
    
    # Assign an ident to each row that meets this time threshold.
    np.put(filtered_array_time_diff2[:,0],np.where(filtered_array_time_diff2[:,2] >= minutes_for_a_stop)[0],9999999)
    
    # will have to carry over the 99999999 to the row below. But first get rid
    #of any 9999999 that is assigned to the edge of a group.
    # Assign each group edge a value of 1.
    # Now these are the edges of the original groups made from the first distance measurment.
    np.put(filtered_array_time_diff2[:,0], np.where(np.diff(filtered_array_time_diff2[:,9]) == 1)[0], 1)
    np.put(filtered_array_time_diff2[:,0],np.where(filtered_array_time_diff2[:,0] == 9999999)[0] + 1, 9999999)

    # Assign ident back to array if two records are a stop and were not labeled as a stop.
    
    # Changed 20200928 - I changed the very last value from 999999 to 4444696944 just
    # bc I want these two row stops to be distinct.
    np.put(filtered_array_time_diff2[:,1], np.where(np.logical_and(filtered_array_time_diff2[:,0]==9999999, filtered_array_time_diff2[:,1]<= minutes_for_a_stop))[0], 4444696944)
    
    # Added 20200928 - Put in this one liner to assign the 4444696944 ident to the actual 
    # ident column to ensure that the cumsum gives the two row stops the same ident. before 
    # it was giving them a different ident like 1,2 instead of 1,1
    np.put(filtered_array_time_diff2[:,4], np.where(filtered_array_time_diff2[:,1] == 4444696944)[0], 4444696944)
    
    # Place the newest group idents and group times back into the original array.
    array = np.c_[np.ones(len(array)) ,array]
    np.put(array[:,0],old_stop_index_complete,filtered_array_time_diff2[:,4])
    array = np.c_[np.ones(len(array)) ,array]
    np.put(array[:,0],old_stop_index_complete,filtered_array_time_diff2[:,1])
    
    # filter the array to only include the groups that are over the stop limit time.
    # Create new group idents for them and then add them back to the array.
    real_stop = array[np.where(array[:,0] >= minutes_for_a_stop)]
    np.put(real_stop[:,1], np.arange(len(real_stop)), np.cumsum(np.not_equal((np.concatenate(([0], real_stop[:,1])))[:-1], (np.concatenate(([0], real_stop[:,1])))[1:])))
    
    # Need to recalculate the time bc if there were two row stops that we found
    # their cumsum time would be 9999999
    second_time_diff = real_stop[:,4][1:] - real_stop[:,4][:-1]
    second_time_diff = np.append(second_time_diff, np.timedelta64(0,"s"))
    second_time_diff = second_time_diff.astype("timedelta64[ms]").astype(int)/1000
    second_time_diff = second_time_diff[...,np.newaxis]
    real_stop = np.hstack((second_time_diff,real_stop))
    # The edge of the new groups.
    tester4 = np.where(np.diff(real_stop[:,2])!=0)
    np.put(real_stop[:,0], tester4[0], 0)
    time_column = np.float64(real_stop[:,0])
    users_3 = np.float64(real_stop[:,2])
    # assign integer indices to each unique user name, and get the total
    # number of occurrences for each name
    unames, idx, counts = np.unique(users_3, return_inverse=True, return_counts=True)
    # now sum the values of pred corresponding to each index value
    sum_pred = np.bincount(idx, weights=time_column)
    add_time = sum_pred[idx]
    add_time = add_time[...,np.newaxis]
    real_stop = np.hstack((add_time, real_stop))
    
    # Calculate the mean center for each final stop group.
    # Lat
    lat_column = np.float64(real_stop[:,7])
    lat_users = np.float64(real_stop[:,3])
    unames, idx, counts = np.unique(lat_users, return_inverse=True, return_counts=True)
    sum_pred = np.bincount(idx, weights=lat_column)
    mean_pred_lat = sum_pred / counts
    mean_pred_lat = mean_pred_lat[..., np.newaxis]
    
    # Lon
    lon_column = np.float64(real_stop[:,8])
    lon_users = np.float64(real_stop[:,3])
    unames, idx, counts = np.unique(lon_users, return_inverse=True, return_counts=True)
    sum_pred = np.bincount(idx, weights=lon_column)
    mean_pred_lon = sum_pred / counts
    mean_pred_lon = mean_pred_lon[..., np.newaxis]
    
    # Save the index of the final stop groups.
    final_stop_index = (np.where(array[:,0] >= minutes_for_a_stop))[0]
    
    # Place the sum time for each final stop group back into the array.
    np.put(array[:,0], final_stop_index, real_stop[:,0])
    
    # Do the same for their new idents. First have to add a column to the array
    # made up of 0s. Zeros work well bc the group starts at 1 so we can replace
    # the zeroes easily.
    add_zeros = np.zeros_like(array[:,0])
    add_zeros = add_zeros[...,np.newaxis]
    array = np.hstack((add_zeros, array))
    np.put(array[:,0], final_stop_index, real_stop[:,3])
    
    # Replace the 0s with -1, which is akin to dbscan.
    np.put(array[:,0], np.where(array[:,0] == 0), -1)
    
    # Put the mean center into the array.
    array = np.hstack((add_zeros, array))
    np.put(array[:,0], final_stop_index, mean_pred_lon[idx])
    
    array = np.hstack((add_zeros, array))
    np.put(array[:,0], final_stop_index, mean_pred_lat[idx])
    
    # Remove unnecessary columns.
    array = np.delete(array, [4,5,6], 1)


    # Add the min and max timestamp for each stop group.
    rstops = np.where(array[:,2] != -1)
    rarray = array[rstops]
    
    users = np.float64(rarray[:,2])
    unames, idx, counts = np.unique(users, return_inverse=True, return_counts=True)
    
    last_rows = (np.where(np.diff(rarray[:,2]) != 0))
    last_rows = np.insert(last_rows[0], len(last_rows[0]), len(rarray) -1)
    max_timestamp = rarray[:,4][last_rows]
    max_timestamp = max_timestamp[idx]
    max_timestamp = max_timestamp[...,np.newaxis]
    rarray = np.hstack((max_timestamp,rarray))
    
    
    first_rows = (np.where(np.diff(rarray[:,3]) != 0))[0]+1
    first_rows = np.insert(first_rows, 0, 0)
    min_timestamp = rarray[:,5][first_rows]
    min_timestamp = min_timestamp[idx]
    min_timestamp = min_timestamp[...,np.newaxis]
    rarray = np.hstack((min_timestamp,rarray))
    
    add_zeros = np.zeros_like(array[:,0])
    add_zeros = add_zeros[...,np.newaxis]
    array = np.hstack((add_zeros, array))
    np.put(array[:,0], rstops, rarray[:,1])
    
    add_zeros = np.zeros_like(array[:,0])
    add_zeros = add_zeros[...,np.newaxis]
    array = np.hstack((add_zeros, array))
    np.put(array[:,0], rstops, rarray[:,0])
    
    
    # Convert the array back into a traj dataframe and return to user.
    final_tdf = TrajDataFrame(array, 
                          latitude='latitude',
                          longitude="longitude",
                          datetime='timestamp',user_id="uid")

    
    # Name the dataframe's columns.
    new_column_names = ["min", "max", "mean_lat", "mean_lon", "group_ident", "total_seconds"]
    new_column_names.extend(column_names)
    final_tdf.columns = new_column_names

    # Convert the "mean_lat" and "mean_lon" columns from float to np.float64.
    final_tdf["mean_lat"] = np.float64(final_tdf["mean_lat"])
    final_tdf["mean_lon"] = np.float64(final_tdf["mean_lon"])
    
    
    return final_tdf
