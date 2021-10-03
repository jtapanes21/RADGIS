from ..utils import constants
from ..core.trajectorydataframe import *
from datetime import datetime, timedelta, time
import pandas as pd


"""
Periodicity of Sampling

------------------------
Periodicity of sampling is an important concept when working with trajectories. Many trajecory analyses
require an understanding of how densly sampled the dataset is.... i.e., sampled every 5 seconds or sampled every hour.
Understanding the periodicity of sampling helps inform later decisions such as clustering.

This function returns a dictionary when there are multiple users and an integer when there is one user.

Outliers are removed using Interquartile Range (IQR). The mean sampling rate in seconds is returned.



Example


from RADGIS.preprocessing import sampling_periodicity

sampling_periodicity.periodicity(tdf, "2000", "0800")

OR

sampling_periodicity.periodicity(tdf, "2000", "0800", "uid")



"""

def periodicity(tdf, start, end, group_column=None, time_column=constants.DATETIME):

    tdf=tdf.copy()
    tdf = pd.DataFrame(tdf)

    start = time(int(start[:2]), int(start[2:]), 0)
    end = time(int(end[:2]), int(end[2:]), 0)

    tdf.sort_values(time_column, inplace=True)
    tdf.reset_index(drop=True, inplace=True)

    tdf["time_index"] = pd.DatetimeIndex(tdf[time_column])
    tdf.set_index(keys="time_index", inplace=True)

    
    if group_column != None:
        ptdf = _grouped_periodicity(tdf=tdf, start=start, end=end, group_column=group_column, time_column=time_column)
    else:
        ptdf = _periodicity(tdf=tdf, start=start, end=end, time_column=time_column)
        
    return ptdf


def _grouped_periodicity(tdf, start, end, group_column, time_column):

    ptdf_dict = {}

    for name, group in tdf.groupby(group_column, sort=False):
        period = group.between_time(start, end)
        period["timedelta"] = period[time_column].diff().dt.seconds
        period.dropna(subset=["timedelta"], inplace=True)

        q_low = period["timedelta"].quantile(0.25)
        q_high = period["timedelta"].quantile(0.75)
        IQR = q_high - q_low

        period_filtered = period[~((period["timedelta"] < (q_low - 1.5 * IQR)) | (period["timedelta"] > (q_high + 1.5 * IQR)))]

        value = period_filtered["timedelta"].mean()
        ptdf_dict[name] = value

    return ptdf_dict

def _periodicity(tdf, start, end, time_column):
    period = tdf.between_time(start, end)
    period["timedelta"] = period[time_column].diff().dt.seconds
    period.dropna(subset=["timedelta"], inplace=True)
    q_low = period["timedelta"].quantile(0.25)
    q_high = period["timedelta"].quantile(0.75)
    IQR = q_high - q_low
    period_filtered = period[~((period["timedelta"] < (q_low - 1.5 * IQR)) | (period["timedelta"] > (q_high + 1.5 * IQR)))]
    value = period_filtered["timedelta"].mean()

    return value

        
    
    
