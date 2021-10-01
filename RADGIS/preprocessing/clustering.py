from sklearn.cluster import DBSCAN
from RADGIS.utils import constants
from ..core.trajectorydataframe import *



"""
Clustering of locations.

Examples
------------------------
tdf = clustering.dbscan_clustering(tdf, "cluster", .2, 2)

new_column_name = name of new column in dataframe
lat/lon are autoset, but can be overwritten
group_column is set to none, but can be set to multiple columns i.e., group_column = "group" or group_column = ["group1", "group2"]

Epsilon is in kilometers so .2 kilometers is 200 meters.


"""

def dbscan_clustering(tdf, new_column_name, epsilon_size, min_sample,lat_column=constants.LATITUDE, lon_column=constants.LONGITUDE, group_column=None):
    
    if group_column != None:
        ctdf = tdf.groupby(group_column, sort=False).apply(_cluster_trajectory, new_column_name=new_column_name, epsilon_size=epsilon_size, min_sample=min_sample, lat_column=lat_column, lon_column=lon_column)
    else:
        ctdf = _cluster_trajectory(tdf, new_column_name=new_column_name, epsilon_size=epsilon_size, min_sample=min_sample, lat_column=lat_column, lon_column=lon_column)

    return ctdf

def _cluster_trajectory(tdf, new_column_name, epsilon_size, min_sample, lat_column, lon_column):
    kms_per_radian = 6371.0088
    epsilon = epsilon_size / kms_per_radian
    coords = tdf[[lat_column, lon_column]].values
    result = DBSCAN(eps=epsilon,min_samples=min_sample, algorithm="ball_tree", metric="haversine").fit_predict(np.radians(coords))
    tdf[new_column_name] = result
    return tdf


























