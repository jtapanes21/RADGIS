from ..utils import gislib, constants, detection
from ..preprocessing import clustering
import numpy as np
import pandas as pd
import geopandas
from time import gmtime, strftime
from shapely.geometry import MultiPoint, Point, LineString
import os
import glob





def travel_analysis(tdf, save_location, stop_radius_meters=20, minutes_for_a_stop=10, 
                   time_column = constants.DATETIME, unique_identifier = constants.UID, 
                    all_stops=False, convex_stops=False, all_points=False):
    
    print("Start")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    # Set the lat and lon variable:
    
    lat_column = "mean_lat"
    lon_column = "mean_lon"
    
    df = tdf.copy()
    
    df.reset_index(drop=True, inplace=True)
    
    # Run the numpy stop detection code.
    
    print("Starting numpy stop detection.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    df = detection.stops(df, stop_radius_meters=stop_radius_meters, minutes_for_a_stop=minutes_for_a_stop)
    
    print("Finished numpy stop detection.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    
    
    
    os.chdir(save_location)


    
  
    
    
    #------------------------------------------------------------------------
    # Start of stop analysis
    
    print("Starting pandas stop cleanup and configuration for final output.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    
    df1 = df.copy()
    
    df_temp = df1.copy()
    
    # Filter the temp dataframe to only include stops
    df_temp = df_temp[df_temp["group_ident"] != -1]
    
    # Filter the temp dataframe to only include one point from each group. This will greatly lessen the time it takes
    # for clustering.
    
    df_temp = df_temp.drop_duplicates([unique_identifier, "group_ident"])
    
    
    ## This is the density-based clustering where stops are identified.
    ## A stop can be comprised of just two points.
    
    
    ## Function input is a dataframe
    ## epsilon size is in kilometers. 1 would be 1 kilometer. 0.1 would be 100 meters.
    ## for spherical coordinates only because it uses great circle for distance calculation aka haversine
    ## convert the coordinates to radians. haversine metric expects radians

    
    print("Starting DBSCAN within pandas stop section.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    # The default epsilon size is 20 meters, which is .02 because the dimension is in kilometers.
    df_temp = clustering.dbscan_clustering(df_temp, "Stops", epsilon_size=.02, min_sample=1, 
                                           lat_column = "mean_lat", lon_column = "mean_lon", group_column=unique_identifier)
    
    print("Finished DBSCAN clustering.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    
    # Now insert the rows from the temp dataframe back into the main dataframe using their index.
    # Add "Stops" to the main dataframe so that the shape of each dataframe matches
    df1["Stops"] = -1
    
    df1.update(df_temp)
    
    # Adding the df_temp to the main dataframe only added one record per stop group. Now we apply the dbscan Stop group label
    # to all of the cells in the Stop column.
    
    df1["Stops"] = df1.groupby([unique_identifier, "group_ident"], sort=False)["Stops"].transform(lambda x: x.loc[x.first_valid_index()])
    
    #return df1

    
    

    
    
    
    # Create a new column - "stops" - to remain consistent with the first iteration of this code. This column 
    # is comprised of the sequential stops that were renamed in dbscan. Uses the group_ident column from the detection module.
    # This might seem like it is not needed bc the detection module provides sequential stops, but it does not start from stop
    # 1 after the first group ends. So negating this code below would work if there was only one unique user in the data,
    # but if there are more than one users then this is needed.
    
    #df1.sort_values(by=["timestamp"], inplace=True)
    #df1.reset_index(drop=True,inplace=True)
    
    #df1["test"] = df1.groupby([group_column], sort=False)["Stops"].transform(lambda x: x.diff().ne(0).cumsum())
    onlyCluster = df1[df1.Stops != -1]
    df1["stops"] = onlyCluster.groupby([unique_identifier], sort=False)["group_ident"].transform(lambda x: x.diff().ne(0).cumsum())
    
    
    
    

    
    
    
    # Original algorithm used dbscan clustering a second time with broader parameters to cover a larger area to find sig locations.
    # Sig locations are revisited locations like home or work. With the new algorithm, dbscan is not run a second time.
    # To remain consistent with code further down we add the Sig_Location column name.
    
    df1["Sig_Location"] = df1["Stops"]


            
    ## Add a day count column to the dataframe.
    ## This will be used to filter significant locations.
    
    onlyCluster = df1[df1.Sig_Location != -1]
    df1["SigLocDayCt"] = onlyCluster.groupby([unique_identifier, "Sig_Location"], sort=False)[time_column].transform(lambda x: len(x.dt.date.unique()))
    
    ## Evaluate the day count column.
    # Current default is to remove significant location if it does not represent
    ## two days.
    
    
    def sig_cluster(row0, row1):
        if row0 < 2:
            return -1
        else:
            return row1
    
    df1["Sig_Location"] = [sig_cluster(row[0], row[1]) for row in df1[["SigLocDayCt", "Sig_Location"]].values]
    
    

    
    ## Official start of stop analysis.
    

    
    
    '''
    
    Don't think that I need this bit anymore:
    
    
    # Next address when non-sequential stops occur. They look like this:
    
    # 1
    # 2
    # 3
    # 4
    
    ## These are not stops. They are trips.
    ## Below three lines of code will rectifiy this and make them into trips.
    
    
    df1 = df1.join(df1.groupby([group_column, "stops"], sort=False)["stops"].size().rename("counter"), on=[group_column,"stops"], how="outer")

    def stop_fixer(row0, row1):
        if row1 > 1:
            return row0
        else:
            return np.NaN
    
    df1["stops"] = [stop_fixer(row[0], row[1]) for row in df1[["stops", "counter"]].values]


    '''
    
    '''
    
    Probably don't need this since we aren't doing the above code.
    
    # Run the cumsum function again to ensure that the stops have an ascending
    ## order (1,2,3,4) and not how they would be (1,3,6,12).
    
    onlyCluster = df1[df1.stops.notnull()]
    df1["stops"] = onlyCluster.groupby([group_column], sort=False)["stops"].transform(lambda x: x.diff().ne(0).cumsum())
    
    '''
    
    '''
    
    Don't think that I need this bit anymore bc the "Stops" should be in order. In the old code the Stops might go
    from 1,2,4,6,7 because we removed rows that were stops. Since we no longer do this - stops all all
    identified in the detection module - the dbscan run should order them correctly - 1,2,3,4,5,6,7.
    
    
    # Do the same thing to ensure ascending order names for the "Stops".
    
    df1.sort_values("Stops",inplace=True)
    onlyCluster = df1.loc[df1.stops.notnull()]
    df1["Stops"] = onlyCluster.groupby([group_column],sort=False)["Stops"].transform(lambda x: x.diff().ne(0).cumsum())
    '''
 

    
    
    
    ## Added a safeguard for the value names in the sig location column.
    # The points that comprise a stop could be partially enveloped by a 
    ## sig location. 
    ## It is likely that either all stop points will be in a sig location or none will.
    # However, in the off-chance that some are and some are not, this code
    ## will address that to ensure that the sig location name is transfered.
    
    df1.sort_values("Sig_Location",inplace=True)
    
    
    # The goal of this code is to cleanup the "Sig_Location" labels
    # by giving them ascending order names like we did above
    ## for "stops" and "Stops".

    # We only care about the "Sig_Location" values that correspond to a row
    ## that contains a temporal stop.
    onlyCluster = df1.loc[df1.stops.notnull()]
    onlyCluster = onlyCluster[onlyCluster.Sig_Location != -1]
    df1["Sig_Location"] = onlyCluster.groupby([unique_identifier], sort=False)["Sig_Location"].transform(lambda x: x.diff().ne(0).cumsum())
    
    
    # The point of this block is to apply the "Sig_Location" label to the 
    ## "Stops" column if the row has a "Sig_Location".
    df1.Sig_Location.fillna(-1, inplace=True) 
    
    
    def sig_loc_fixer1(row0):
        if row0 != -1:
            return "Sig_" + str(row0)
        else:
            return row0
    
    df1["Sig_Location"] = [sig_loc_fixer1(row[0]) for row in df1[["Sig_Location"]].values]



    def sig_loc_fixer2(row0, row1):
        if row0 != -1:
            return row0
        else:
            return row1

    df1["Stops"] = [sig_loc_fixer2(row[0], row[1]) for row in df1[["Sig_Location", "Stops"]].values]
    
    
    

    
    
   

    

    StopsDF = df1.copy()
    StopsDF = StopsDF[StopsDF.stops.notnull()]


    
    
   

    crs = {"init": "epsg:4326"}
    
    print("Exporting mean center stops shapefile.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
  
    # Export the mean center coordinates for each stop.
    StopsDF_mean = StopsDF.copy()
    
    StopsDF_mean.drop_duplicates(subset=[unique_identifier, "stops"], inplace=True)
    StopsDF_mean.reset_index(drop=True, inplace=True)
    
    # Save a copy to return at the end that the user can further process in Python - like
    # inputing the stops in a markvo chain or creating an edge list to show relation on a graph.
    final_return = StopsDF.copy()
    
    StopsDF_mean[time_column] = StopsDF_mean[time_column].astype(str)
    StopsDF_mean["min"] = StopsDF_mean["min"].astype(str)
    StopsDF_mean["max"] = StopsDF_mean["max"].astype(str)
    


    geometry = [Point(xy) for xy in zip(StopsDF_mean["mean_lon"], StopsDF_mean["mean_lat"])]
    dfStops = geopandas.GeoDataFrame(StopsDF_mean,crs=crs, geometry=geometry)

    if len(glob.glob("stops_mc*")) < 1:
        dfStops.to_file("stops_mc_1.shp")

        print("Mean center stops shapefile exported.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    else:
        counter = 0
        files = glob.glob("stops_mc*")
        for file in files:
            if file.endswith(".shp"):
                counter += 1
            else:
                pass

        counter += 1

        dfStops.to_file("stops_mc_" + str(counter) + ".shp")
   
        print("Mean center stops shapefile exported.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    
    
    
    
    # Dirty condition to make the geopandas dataframe so we only make it once.
    if all_stops or convex_stops == True:
        
        print("Creating the geopandas dataframe of all of the stops")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        
        stops_copy = StopsDF.copy()
        geometry_copystops = [Point(xy) for xy in zip(stops_copy["longitude"], stops_copy["latitude"])]
        gdf_stopscopy = geopandas.GeoDataFrame(stops_copy,crs=crs, geometry=geometry_copystops)
        
        print("Geopandas dataframe created.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    else: 
        pass
        
        
   
    # Arguement condition that, if True, will return all of the points for each stop.
    if all_stops == True:
        
        print("Started exporting the all stops shapefile.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        
        df_all_stops = gdf_stopscopy.copy()
        
        df_all_stops[time_column] = df_all_stops[time_column].astype(str)
        df_all_stops["min"] = df_all_stops["min"].astype(str)
        df_all_stops["max"] = df_all_stops["max"].astype(str)
        
 
        if len(glob.glob("stops_all*")) < 1:
            df_all_stops.to_file("stops_all_1.shp")
        
            print("Finished exporting the all stops shapefile.")
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        else:
            counter = 0
            files = glob.glob("stops_all*")
            for file in files:
                if file.endswith(".shp"):
                    counter += 1
                else:
                    pass
            
            counter += 1
        
            df_all_stops.to_file("stops_all_" + str(counter) + ".shp")
            
            print("Finished exporting the all stops shapefile.")
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    else: 
        pass
    
    if convex_stops == True:
        
        print("Started exporting the convex hull stops shapefile.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        
        gdf_forconvex = gdf_stopscopy.copy()
        
        gdf_forconvex[time_column] = gdf_forconvex[time_column].astype(str)
        gdf_forconvex["min"] = gdf_forconvex["min"].astype(str)
        gdf_forconvex["max"] = gdf_forconvex["max"].astype(str)

        
        # Function that builds the convex hulls around the stops.
        def convex_hull(gdf, unique_ident_list):
            original_gdf = gdf.copy()
            groupHull = gdf.groupby(unique_ident_list, sort=False)
            points = groupHull.geometry
            polygon = points.apply(lambda x: MultiPoint(x.tolist()))
            Hull = polygon.apply(lambda x: x.convex_hull)
            polygonGdf = pd.DataFrame(Hull)

            # Remove duplicated to make the merge faster:
            original_gdf.drop_duplicates(subset=unique_ident_list, inplace=True)
            # Merge the convex hull geometry with the original df.

            gdf_convex_hull = polygonGdf.merge(original_gdf, on=unique_ident_list)
            gdf_convex_hull.reset_index(drop=True, inplace=True)

            gdf2 = geopandas.GeoDataFrame(gdf_convex_hull, crs={"init": "epsg:4326"}, geometry="geometry_x")

            # Remove all geometries other than polygon
            gdf2.drop((gdf2[(gdf2.geom_type == "LineString")].index), inplace=True)
            gdf2.drop((gdf2[(gdf2.geom_type == "Point")].index), inplace=True)
            gdf2.drop("geometry_y", inplace=True, axis=1)

            return gdf2
        
        
        gdf_convex = convex_hull(gdf_forconvex, [unique_identifier, "stops"])
        
        
        if len(glob.glob("stops_convex*")) < 1:
            gdf_convex.to_file("stops_convex_1.shp")
            
            print("Finished exporting the convex hull stops shapefile.")
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            
        else:
            counter = 0
            files = glob.glob("stops_convex*")
            for file in files:
                if file.endswith(".shp"):
                    counter += 1
                else:
                    pass
            
            counter += 1
        
            gdf_convex.to_file("stops_convex_" + str(counter) + ".shp")
            
            print("Finished exporting the convex hull stops shapefile.")
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    
    else:
        pass
        
    
    
    
    
    
    
    
   
        
    ## Remove groups that have zero stops.
    

    
    def check_stops(row0):
        if row0 == 1:
            return "Yes"
    
    df1["Stop_Checker"] = [check_stops(row[0]) for row in df1[["stops"]].values]
    df1.sort_values(["Stop_Checker"], inplace=True)
    df1["Stop_Checker"] = df1.groupby([unique_identifier], sort=False).Stop_Checker.ffill()
    df1 = df1.loc[df1.Stop_Checker.notnull()]
    
    
    # Return all points.
    if all_points == True:
                
        print("Exporting all points to a shapefile. Note that points that belong to a unique ident that don't "
             "have stops will not be exported.")
        
        df_allpoints = df1.copy()
        
        # Clean the dataframe for export.
        df_allpoints.drop(["group_ident", "Stop_Checker"], inplace=True, axis=1)
        df_allpoints["min"] = df_allpoints["min"].astype(str)
        df_allpoints["max"] = df_allpoints["max"].astype(str)
        df_allpoints[time_column] = df_allpoints[time_column].astype(str)
        
        # Create the geopandas dataframe.
        
        print("Creating the geopandas dataframe of all of the points.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        

        geometry_allpoints = [Point(xy) for xy in zip(df_allpoints["longitude"], df_allpoints["latitude"])]
        gdf_allpoints = geopandas.GeoDataFrame(df_allpoints,crs=crs, geometry=geometry_allpoints)
        
        print("Finished creating the geopandas dataframe of all of the points.")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        
        
        if len(glob.glob("all_points*")) < 1:
            gdf_allpoints.to_file("all_points_1.shp")
        
            print("Finished exporting the 'all points' shapefile.")
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        else:
            counter = 0
            files = glob.glob("all_points*")
            for file in files:
                if file.endswith(".shp"):
                    counter += 1
                else:
                    pass
            
            counter += 1
        
            gdf_allpoints.to_file("all_points_" + str(counter) + ".shp")
            
            print("Finished exporting the 'all points' shapefile.")
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        #return df_allpoints
    else:
        pass
    
    

    ## End of stop analysis.
    
    #-----------------------------------------------------------------------------------
    
    print("Stop analysis completed. Trip analysis started.")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime())) 
    
    
    ## Start of trip analysis
    
    df1.sort_values(time_column, inplace=True)
    
    ## changed slightly to jive with names from new numpy stop integration.
    
    df1.drop(["min", "max", "total_seconds", "Sig_Location", "SigLocDayCt", "Stop_Checker"], inplace=True,axis=1)
    #df1.drop(["min", "max", "stop_duration", "Sig_Location", "SigLocDayCt", "Stop_Checker"], inplace=True,axis=1)
    
    # Provide lat/lon coordinates for the non-stops under the mean_lat/mean_lon columns
    def mean_lat_lon_shift(row0, row1):
        if row0 == 0.0:
            return row1
        else:
            return row0
    
    df1["mean_lat"] = [mean_lat_lon_shift(row[0], row[1]) for row in df1[["mean_lat", "latitude"]].values]
    df1["mean_lon"] = [mean_lat_lon_shift(row[0], row[1]) for row in df1[["mean_lon", "longitude"]].values]
    
    
    df2 = df1.copy()
    
    
    # DF2 is used to identify trips between two stops. This illustrates the purpose of df4:
    
    # stop 1
    # stop 1
    # stop 2
    # stop 2
    
    # Currently there are no trips that seperate two legitimate stops. This occurs for many reasons
    # one of which could be sparse data. We will address this issue and create a trip between
    ## these two stops.
    
    ## Steps:
    # Use the shift function to retrieve the above/below cell value for the coordinates.
    # This provides the spatial edge for the start and end of the trip.
    # The coordinate shift is also used to calculate the distance for the trip.
    
    
    df2["end_X"] = df2.groupby([unique_identifier],sort=False)[lon_column].shift(-1)
    df2["end_Y"] = df2.groupby([unique_identifier],sort=False)[lat_column].shift(-1)


    df2["start_X"] = df2[lon_column]
    df2["start_Y"] = df2[lat_column]
    
    ## The shift function is also used for the timestamp.
    
    df2["start_time"] = df2[time_column]
    df2["end_time"] = df2.groupby([unique_identifier],sort=False)[time_column].shift(-1)
    
    
    ## The checker is used with this logic:
    # Place the "stop" value in the checker column from the previous cell hence the shift.
    # Return a dataframe that only contains stops.
    # In this new dataframe, if a cell in the checker column has a NaN value or if the cell's
    # checker equals the cell's "stop" value, then we know that we did not identify the butressing
    # two stops. But if the cell's checker value does not equal it's "stop" value or NaN, then
    # we know that we identified the top portion of the buttressing stop.
    
    df2["checker"] = df2.groupby([unique_identifier],sort=False)["stops"].shift(-1)
    
    df2 = df2.loc[df2.stops.notnull()]
    
    ## Return the NaN values back to their stop values. 
    ## The NaN values do not identify the butressing stops. 
    # To do this assign the NaN values a meaningless string value that can be used to write
    ## a conditional statement on.
    
    df2["checker"].fillna("Used", inplace = True)
    
    ## The conditional lambda function will return the NaN values ("Used") back to their stop values.
    
    def restore_nans(row0, row1):
        if row1 == "Used":
            return row0
        else:
            return row1
    
    
    df2["checker"] = [restore_nans(row[0], row[1]) for row in df2[["stops", "checker"]].values]


    
    ## This function will idenntify the butressing stop with an integer value of 1.
    
    ## 1 = Trip
    
    def trip(row0, row1):
        if row0 == row1:
            return 0
        else:
            return 1
    
    
    df2["is_a_trip"] = [trip(row[0], row[1]) for row in df2[["checker", "stops"]].values]
    
    
 

    ## Only continue to process df2 trips if there exist butressing trips.
    
    if len(df2[df2["is_a_trip"]==1]) >= 1:
        
        ## Assign a unique identifier to the first cell in the butressing trip.
        
        df2["test4"] = df2.groupby([unique_identifier], sort=False)["is_a_trip"].transform(lambda x: x.diff().ne(0).cumsum())
        onlyiTrip = df2[df2.is_a_trip == 1]
        df2["iTrips"] = onlyiTrip.groupby([unique_identifier], sort=False)["test4"].transform(lambda x: x.diff().ne(0).cumsum())
        
        # Provide the start and end stop names for the trips aka where did the trip start and end.
        
        df2["from_loc"] = df2["Stops"]
        df2["to_loc"] = df2.groupby([unique_identifier], sort=False)["Stops"].shift(-1)
        
        ## Filter the dataframe to only include the butressing trip record.
        ## Calculate the time duration of the trip.
        
        ## Result is a dataframe with the inner trips.
        # The coordinate of the actual record is the start. The end and start coordinates
        ## are the end and start for the waypoint. 
        
        df2 = df2[df2.iTrips.notnull()]
        df2 = df2.join(df2.groupby([unique_identifier,"iTrips"], sort=False)["start_time"].min().rename("min"), on=[unique_identifier, "iTrips"], how="outer")
        df2 = df2.join(df2.groupby([unique_identifier,"iTrips"], sort=False)["end_time"].max().rename("max"), on=[unique_identifier, "iTrips"], how="outer")
        df2["trip_duration"] = (df2["max"] - df2["min"]).dt.total_seconds()
        
        
        
        ## Calculate the trip distance
        
   

        
        ## Cacluate the distance.
        
        ## Changed with new integration of numpy code to use the gislib module:
        

        df2["trip_dist"] = [gislib.haversine_np(row[0], row[1], row[2], row[3]) for row in df2[[lat_column, lon_column, "end_Y", "end_X"]].values]
     
        # The gislib haversine function produces a list where the distance, in meters, is first. So
        # we use a slow pandas apply/lambda to grab it from the list.
        df2["trip_dist"] = df2["trip_dist"].apply(lambda x: x[0])
        
        #df2["trip_dist"] = [haversine(row[0], row[1], row[2], row[3]) for row in df2[[lat_column, lon_column, "end_Y", "end_X"]].values]
        
        
  
        
        df2 = df2.filter(['end_X', 'end_Y', 'start_X', 'start_Y', 'from_loc', 'to_loc', 'min', 'max',
       'trip_duration', 'trip_dist', unique_identifier, "trips"])
        
 

        
    else:
        del df2
 
        
        
    # There are three different trip types that we have to deal with. We just dealt with the first trip type.
    # We will collect the finished trips in a list of dataframes that we will merge at the end.
    
    for name, value in locals().items():
        if name.startswith("df2"):
            mergedTrips = df2
            
        else:
            pass
        


    
    
   
    ## The hard trips have been identified. Now identify the trips with a -1 cluster labal.
    
    df3 = df1.copy()
    

    
    ## Manipulate the NaN values in the stops column and change their value to a -1 aka a trip.
    
    df3["stops"].fillna(-1,inplace=True)
    
    ## Like we previously did for df2 trips, we will add a unique identifier to each trip sequence.
    
    df3["test2"] = df3.groupby([unique_identifier], sort=False)["stops"].transform(lambda x: x.diff().ne(0).cumsum())
    onlyTrip = df3[df3.stops == -1]
    df3["trips"] = onlyTrip.groupby([unique_identifier], sort=False)["test2"].transform(lambda x: x.diff().ne(0).cumsum())
    
    ## Add the Timestamp from above and below cells.
    
    df3["time_above"] = df3.groupby([unique_identifier], sort=False)[time_column].shift(1)
    df3["time_below"] = df3.groupby([unique_identifier], sort=False)[time_column].shift(-1)
    
    onlyTrip = df3[df3.trips.notnull()]
    df3 = df3.join(onlyTrip.groupby([unique_identifier, "trips"], sort=False)["time_above"].min().rename("min"), on=[unique_identifier, "trips"], how="outer").sort_values(time_column)
    df3 = df3.join(onlyTrip.groupby([unique_identifier, "trips"], sort=False)["time_below"].max().rename("max"), on=[unique_identifier, "trips"], how="outer").sort_values(time_column)
    
    
    
    ## If the top record is a trip then it would not have a min time. 
    ## This line of code rectifies that.
    
    df3.loc[df3.groupby([unique_identifier],sort=False)['min'].head(1).index, 'min'] = df3.loc[df3.groupby([unique_identifier],sort=False)[time_column].head(1).index, time_column]
    
    ## Calculate the trip time duration.
    
    df3["trip_duration"] = (df3["max"] - df3["min"]).dt.total_seconds()
    
    ## Get the coordinates for the cell above and below.
    
    df3["X_above"] = df3.groupby([unique_identifier], sort=False)[lon_column].shift(1)
    df3["Y_above"] = df3.groupby([unique_identifier], sort=False)[lat_column].shift(1)

    df3["X_below"] = df3.groupby([unique_identifier], sort=False)[lon_column].shift(-1)
    df3["Y_below"] = df3.groupby([unique_identifier], sort=False)[lat_column].shift(-1)
    
    ## The top row will not have a value above it for the shift to work. This addresses that.
    
    df3.loc[df3.groupby([unique_identifier],sort=False)['X_above'].head(1).index, 'X_above'] = df3.loc[df3.groupby([unique_identifier],sort=False)[lon_column].head(1).index, lon_column]
    df3.loc[df3.groupby([unique_identifier],sort=False)['Y_above'].head(1).index, 'Y_above'] = df3.loc[df3.groupby([unique_identifier],sort=False)[lat_column].head(1).index, lat_column]
    
    ## Similarly, the bottom record does not have a row beneath it for the shift to work.
    
    df3.loc[df3.groupby([unique_identifier],sort=False)['X_below'].tail(1).index, 'X_below'] = df3.loc[df3.groupby([unique_identifier],sort=False)[lon_column].tail(1).index, lon_column]
    df3.loc[df3.groupby([unique_identifier],sort=False)['Y_below'].tail(1).index, 'Y_below'] = df3.loc[df3.groupby([unique_identifier],sort=False)[lat_column].tail(1).index, lat_column]
    
    ## Assign the start coordinate and the stop coordinate to the new columns.
    
    onlyTrip = df3[df3.trips.notnull()]
    
    df3["start_X"] = onlyTrip.groupby([unique_identifier, "trips"],sort=False).X_above.head(1)
    df3["start_Y"] = onlyTrip.groupby([unique_identifier, "trips"],sort=False).Y_above.head(1)

    df3["end_X"] = onlyTrip.groupby([unique_identifier, "trips"],sort=False).X_below.tail(1)
    df3["end_Y"] = onlyTrip.groupby([unique_identifier, "trips"],sort=False).Y_below.tail(1)
    
    ## Add the start and end node to the trips.
    
    df3["coming_from"] = df3.groupby([unique_identifier], sort=False)["Stops"].shift(1)
    df3["going_to"] = df3.groupby([unique_identifier], sort=False)["Stops"].shift(-1)
    
    onlyTrip = df3[df3.trips.notnull()]
    
    df3["from_loc"] = onlyTrip.groupby([unique_identifier, "trips"],sort=False).coming_from.head(1)
    df3["to_loc"] = onlyTrip.groupby([unique_identifier, "trips"],sort=False).going_to.tail(1)
    
    
    ## Use a forward and backward fill to  add the start/end nodes and coordinates to each group.
    
    df3 = df3[df3["trips"].notnull()]

    df3["from_loc"] = df3.groupby([unique_identifier, "trips"], sort=False).from_loc.ffill()
    df3["to_loc"] = df3.groupby([unique_identifier, "trips"], sort=False).to_loc.bfill()
    
    df3["start_X"] = df3.groupby([unique_identifier, "trips"], sort=False).start_X.ffill()
    df3["start_Y"] = df3.groupby([unique_identifier, "trips"], sort=False).start_Y.ffill()

    df3["end_X"] = df3.groupby([unique_identifier, "trips"], sort=False).end_X.bfill()
    df3["end_Y"] = df3.groupby([unique_identifier, "trips"], sort=False).end_Y.bfill()
    
    ## Almost done with these trips.
    ## We will calculate their distance.
    ## Two considerations for this distance calculation:
    # First, a trip could be comprised of two or more waypoints.
    # Secondly, a trip could be comprised of just one waypoint.
    
    ## The code reflects that we have to calculate the distances for these two types of trips.
    
    ## The "trip_counter" column is a count of the waypoints that comprise the trip.
    ## This column will enable conditional statements to properly calculate the trip distance.
    
    df3 = df3.join(df3.groupby([unique_identifier, "trips"], sort=False)["trips"].count().rename("trip_counter"), on=[unique_identifier, "trips"], how="outer").sort_values(time_column)

    
    
    ## If "trip_counter" < 2, then calculate the trip distance from rows above-to-current-to-below.
    # Elif "trip_counter" > 1, calculate the head of the group using the above-to-current, then next
    # row would be above-to-current, then last row aka tail would be from above-to-current and from
    ## current-to-below. Then sum those up for the tail. Then add all of the distances.
    
    
   
    
    
    
    
    ## Calculate the distance for the trips that have one waypoint. 
    
    df_dist1 = df3.copy()
    

    

    
    if len(df_dist1[df_dist1["trip_counter"]==1]) > 1:
    
        
    
        # The distance function is applied twice because the start-to-waypoint is
        ## calculated and then the waypoint-to-end is calculated.
        
        # Also, the gislib haversine function produces a list where the distance, in meters, is first. So
        # we use a slow pandas apply/lambda to grab it from the list.
        
    
        df_dist1 = df_dist1[df_dist1["trip_counter"]==1]
        df_dist1["counter1_dist_a"] = [gislib.haversine_np(row[0], row[1], row[2], row[3]) for row in df_dist1[["Y_above", "X_above", lat_column, lon_column]].values]
        df_dist1["counter1_dist_a"] = df_dist1["counter1_dist_a"].apply(lambda x: x[0])
        df_dist1["counter1_dist_b"] = [gislib.haversine_np(row[0], row[1], row[2], row[3]) for row in df_dist1[[lat_column, lon_column, "Y_below", "X_below"]].values]
        df_dist1["counter1_dist_b"] = df_dist1["counter1_dist_b"].apply(lambda x: x[0])
        df_dist1["trip_dist"] = df_dist1["counter1_dist_a"] + df_dist1["counter1_dist_b"]

        
    
    
        ## cleanup the dataframe.
    
        df_dist1 = df_dist1.filter(["end_X", "end_Y", "start_X", "start_Y", 
                                    "from_loc", "to_loc", "min", "max", "trip_duration", "trip_dist", unique_identifier, "trips"])
        
 
    else:
        del df_dist1
        
    
    
   
    
    
    local_list1 = []
        
    for name, value in locals().items():
        local_list1.append(name)
    
    if "df_dist1" in local_list1:
        if "mergedTrips" in local_list1:
            mergedTrips = pd.concat([mergedTrips, df_dist1])
        else:
            mergedTrips = df_dist1
            
    else:
        pass
        
    
    
    
    ## Calculate the distance for the trips that have more than one waypoint.
    
    df_dist2 = df3.copy()
    

    
    if len(df_dist2[df_dist2["trip_counter"]>1]) > 1:
        
    
        
    
        df_dist2 = df_dist2[df_dist2["trip_counter"]>1]
    
        ## Calculate the distance.
        # Creates two columns for the two distance calculations - above-to-current and
        ## the group tail that is current-to-below.
        

        
        df_dist2["dist1"] = [gislib.haversine_np(row[0], row[1], row[2], row[3]) for row in df_dist2[["Y_above", "X_above", lat_column, lon_column]].values]
        
        # Also, the gislib haversine function produces a list where the distance, in meters, is first. So
        # we use a slow pandas apply/lambda to grab it from the list.
        df_dist2["dist1"] = df_dist2["dist1"].apply(lambda x: x[0])
        
        df_dist2["tail_check"] = df_dist2.sort_values([unique_identifier, time_column])["trip_counter"].diff().ne(0).shift(-1)

        def theTail(row0, row1, row2, row3, row4):
            if row0 == True:
                return gislib.haversine_np(row1, row2, row3, row4)

        df_dist2["dist2"] = [theTail(row[0], row[1], row[2], row[3], row[4]) for row in df_dist2[["tail_check", lat_column, lon_column, "Y_below", "X_below"]].values]
        
        # The gislib haversine function produces a list where the distance, in meters, is first. So
        # we use a function to grab it from the list.
        def haversine_cleanup(row0, row1):
            if row0 == True:
                return row1[0]
            
        df_dist2["dist2"] = [haversine_cleanup(row[0], row[1]) for row in df_dist2[["tail_check", "dist2"]].values]
        

        
    
        ## Fillna is done so that the two columns can be summed.
        ## A new column is created with the column-to-column across sum.
        ## The only sum really being done is the tail in the group.

        df_dist2["dist2"].fillna(0,inplace=True)
        df_dist2["to_add"] = df_dist2["dist1"] + df_dist2["dist2"]

        ## Complete the total distance sum for the trip and assign it to the entire group.

        df_dist2 = df_dist2.join(df_dist2.groupby([unique_identifier, "trips"], sort=False)["to_add"].sum().rename("trip_dist"), on=[unique_identifier, "trips"], how="outer").sort_values(time_column)



        ## Add the to and from nodes to all rows in each group.

        df_dist2["to_loc"].replace(-1, np.nan, inplace=True)
        df_dist2["from_loc"].replace(-1, np.nan, inplace=True)

        df_dist2["from_loc"] = df_dist2.groupby([unique_identifier, "trips"],sort=False).from_loc.ffill()
        df_dist2["to_loc"] = df_dist2.groupby([unique_identifier, "trips"],sort=False).to_loc.bfill()

        ## Cleanup the dataframe

        df_dist2 = df_dist2.filter(["end_X", "end_Y", "start_X", "start_Y", 
                               "from_loc", "to_loc", "min", "max", "trip_duration", "trip_dist", "trips", unique_identifier])
        
        #return df_dist2
        
        df_dist2 = df_dist2.drop_duplicates([unique_identifier, "trips"])
        
        #if entire_trip == True:
            
        

    
    else:
        del df_dist2

    
    
    
    local_list1 = []
        
    for name, value in locals().items():
        local_list1.append(name)
    
    if "df_dist2" in local_list1:
        if "mergedTrips" in local_list1:
            mergedTrips = pd.concat([mergedTrips, df_dist2])
        else:
            mergedTrips = df_dist2
    else:
        pass
    

            
            
   
       
    
    local_list1 = []
        
    for name, value in locals().items():
        local_list1.append(name)
        
    
    if "mergedTrips" in local_list1:
    
            
  
    
        mergedTrips.reset_index(drop=True, inplace=True)

     ## Recalculte the trips so that they are 1-n in ascending order.

        mergedTrips.sort_values("min", inplace=True)
        mergedTrips["trips"] = mergedTrips.groupby([unique_identifier],sort=False)["trips"].transform(lambda x: x.diff().ne(0).cumsum())

    ## If the last point for each group is a trip then label it as the end.

        mergedTrips["to_loc"].replace(np.nan, "end", inplace=True)

    # Export the trips to a shapefile.

        geometry = mergedTrips.apply(lambda x: LineString([(x['start_X'], x['start_Y']) , (x['end_X'], x['end_Y'])]), axis = 1)
        crs = {"init": "epsg:4326"}
        df222 = geopandas.GeoDataFrame(mergedTrips,crs=crs, geometry=geometry)

        df222["max"] = df222["max"].astype(str)
        df222["min"] = df222["min"].astype(str)
        
        
        
        

        if len(glob.glob("trips*")) < 1:
            df222.to_file("trips_1.shp")
        else:
            
            files = glob.glob("trips*")
            counter = 0
            for file in files:
                if file.endswith(".shp"):
                    counter += 1
                else:
                    pass
            
            counter += 1
            df222.to_file("trips_" + str(counter) + ".shp")
    else:
        pass
    
    print("Finished!")
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    
    
    if all_points == True:
        return df_allpoints
    else:
        return final_return







