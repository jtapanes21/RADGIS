from sklearn.neighbors import BallTree
import numpy as np

'''
Returns the KNN and distance in meters to the KNN.

Parameters
    ----------
    left_gdf : GeoDataFrame
        the target geodataframe; all columns are kept.
    
    right_gdf : GeoDataFrame
        the geodataframe that is the subject of the measurement.
    
    keep_columns : list of strings
        the columns in the right_gdf that are kept.
    
    return_dist : boolean, optional
        if True, the distance in meters is added.
    Returns
    -------
    
    GeoDataFrame
        a GeoDataFrame with all of the columns from the left_gdf and only
        the columns from the right_gdf specified in keep_columns parameter.


Taken from https://automating-gis-processes.github.io/site/notebooks/L3/nearest-neighbor-faster.html#Efficient-nearest-neighbor-search-with-Geopandas-and-scikit-learn


'''

def _get_nearest(src_points, candidates, k_neighbors=1):
    """Find nearest neighbors for all source points from a set of candidate points"""

    # Create tree from the candidate points
    tree = BallTree(candidates, leaf_size=15, metric='haversine')

    # Find closest points and distances
    distances, indices = tree.query(src_points, k=k_neighbors)

    # Transpose to get distances and indices into arrays
    distances = distances.transpose()
    indices = indices.transpose()

    # Get closest indices and distances (i.e. array at index 0)
    # note: for the second closest points, you would take index 1, etc.
    closest = indices[0]
    closest_dist = distances[0]

    # Return indices and distances
    return (closest, closest_dist)




def _complete_neighbor(left_gdf, right_gdf, return_dist):
    """
    For each point in left_gdf, find closest point in right GeoDataFrame and return them.

    NOTICE: Assumes that the input Points are in WGS84 projection (lat/lon).
    """

    left_geom_col = left_gdf.geometry.name
    right_geom_col = right_gdf.geometry.name

    # Ensure that index in right gdf is formed of sequential numbers
    right = right_gdf.copy().reset_index(drop=True)

    # Parse coordinates from points and insert them into a numpy array as RADIANS
    left_radians = np.array(left_gdf[left_geom_col].apply(lambda geom: (geom.x * np.pi / 180, geom.y * np.pi / 180)).to_list())
    right_radians = np.array(right[right_geom_col].apply(lambda geom: (geom.x * np.pi / 180, geom.y * np.pi / 180)).to_list())

    # Find the nearest points
    # -----------------------
    # closest ==> index in right_gdf that corresponds to the closest point
    # dist ==> distance between the nearest neighbors (in meters)

    closest, dist = _get_nearest(src_points=left_radians, candidates=right_radians)

    # Return points from right GeoDataFrame that are closest to points in left GeoDataFrame
    closest_points = right.loc[closest]

    # Ensure that the index corresponds the one in left_gdf
    closest_points = closest_points.reset_index(drop=True)

    # Add distance if requested
    if return_dist:
        # Convert to meters from radians
        earth_radius = 6371000  # meters
        closest_points['distance'] = dist * earth_radius

    return closest_points

def nearest_neighbor(left_gdf, right_gdf, keep_columns, return_dist=False):
    keep_columns.append("distance")
    knn = _complete_neighbor(left_gdf, right_gdf, return_dist=return_dist)
    knn = knn[keep_columns]
    knn_join = left_gdf.join(knn.add_suffix("_knn"))
    return knn_join
    
    
   
    