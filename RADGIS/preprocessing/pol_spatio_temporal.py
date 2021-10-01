

import pandas as pd, numpy as np
import seaborn as sns
import datetime
import matplotlib.dates as mdates
import matplotlib.ticker as plticker
from matplotlib.dates import (WEEKLY, MONTHLY,DAILY, DateFormatter,rrulewrapper, RRuleLocator, AutoDateLocator, HourLocator)
from dateutil.relativedelta import relativedelta
from ..utils import constants






def date_time_pol(dataframe, spatialBinField, temporalBinType,  timestamp_column=constants.DATETIME, saveLocation="", inNotebookVisual=False):
    
    '''
    Return a scatter plot in jupyter nootebook or save to disk.

    

    :param dataframe: pandas DataFrame or TrajDataFrame
        DataFrame or TrajDataFrame to be plotted
    :param spatialBinField: unique label that ties a location or object (i.e., contacts) to the record.
    :param temporalBinType: determines the temporal extent of the scatter plot. Options are:
        "month_year"
        "week_year"
        "week_month_year"
        "year_month_day"
    :param timestamp_column: DataFrame or TrajDataFrame column that contains the datetime information.
        Default is constants.DATETIME, which applies if TrajDataFrame and the original tdf datetime column is used.
    :param saveLocation: default is to not save. Provide folder path and name with file extension to save to disk. Example:
        "D:\Projects\20191122_GPS_Stop_Trips\Hell\RADGIS2\preprocessing\name.jpg" OR png
    :param inNotebookVisual: default is False. Change to True to visualize in juyter notebook.
    
    '''    
    
    
    df = dataframe.copy(deep=True)
    


    

    colorCounter = len(df[spatialBinField].unique()) # Used to grab the colors from the colorList using list indexing
    
    
    # Left to show how to change the facecolor of the chart.
    sns.set(rc={'figure.figsize':(11.7,8.27), 'axes.facecolor':'black'})
    
 
    
    #sns.set(rc={'figure.figsize':(11.7,8.27)})
  
    

    
    ax = sns.scatterplot(mdates.datestr2num(df[timestamp_column].dt.strftime("%Y-%m-%d")),mdates.datestr2num(df[timestamp_column].dt.strftime("%H:%M:%S")),hue=df[spatialBinField], palette=colorsList[:colorCounter])
    

        
        
        
    if temporalBinType == "month_year":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%b %Y")).unique()
        
        if type(pp)== np.ndarray:

            xAxisTickerNum = _xAxisLenGenerator(pp)[0]
            
            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(MONTHLY,interval = xAxisTickerNum )
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%b-%Y")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(months=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(months=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(months=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(months=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%b-%Y")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
        else:
            pass
        
        
        
    elif temporalBinType == "week_year":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%Y-%W")).unique()
        
        if type(pp)== np.ndarray:

            xAxisTickerNum = _xAxisLenGenerator(pp)[0]
            
            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(WEEKLY,interval = xAxisTickerNum )
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%Y-%W")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%Y-%W")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
        else:
            pass

        
    elif temporalBinType == "week_month_year":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%Y-%b-%W")).unique()
        
        if type(pp)== np.ndarray:
            
            xAxisTickerNum = _xAxisLenGenerator(pp)[0]

            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(WEEKLY,interval = xAxisTickerNum )
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%Y-%b-%W")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%Y-%b-%W")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
        else:
            pass
        

    elif temporalBinType == "year_month_day":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%b-%d")).unique()
        
        if type(pp)== np.ndarray:

            xAxisTickerNum = _xAxisLenGenerator(pp)[0]

            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(DAILY,interval = xAxisTickerNum )
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%b-%d")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(days=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(days=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(days=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(days=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%b-%d")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
        else:
            pass
        

    
    # This ensures that only the cluster numbers are on the yaxis
    
    ax.yaxis.set_major_locator(HourLocator(interval=2))
    ax.yaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
    ax.set_ylim([mdates.datestr2num("00:00:00"), mdates.datestr2num("23:59:59")])


    # This reverses the legend so that it matches the pattern of the scatter plot color from top-to-bottom
    
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc="center left", bbox_to_anchor=(1.0,0.5),ncol=1)
    
    
    
    # Set xticks: code attempts to ensure the proper number of xticks are included to not overcrowd the chart
    
    #ax.tick_params(axis='x', which='major', pad=15)
   
    
    
    if len(saveLocation)>0:
        #ax.write_image(saveLocation)
        ax.figure.savefig(saveLocation)
    elif inNotebookVisual == True:
        return ax
    else:
        print("Either provide a dir location to save to disk or visualize graphic in notebook")







def date_pol(dataframe, spatialBinField, temporalBinType, timestamp_column=constants.DATETIME, saveLocation="", inNotebookVisual=False):
    
    
    '''
    Return a scatter plot in jupyter nootebook or save to disk.

    

    :param dataframe: pandas DataFrame or TrajDataFrame
        DataFrame or TrajDataFrame to be plotted
    :param spatialBinField: unique label that ties a location or object (i.e., contacts) to the record.
    :param temporalBinType: determines the temporal extent of the scatter plot. Options are:
        "month_year"
        "week_year"
        "week_month_year"
        "year_month_day"
    :param timestamp_column: DataFrame or TrajDataFrame column that contains the datetime information.
        Default is constants.DATETIME, which applies if TrajDataFrame and the original tdf datetime column is used.
    :param saveLocation: default is to not save. Provide folder path and name with file extension to save to disk. Example:
        "D:\Projects\20191122_GPS_Stop_Trips\Hell\RADGIS2\preprocessing\name.jpg" OR png
    :param inNotebookVisual: default is False. Change to True to visualize in juyter notebook.
    
    '''   
    
    
    df = dataframe.copy(deep=True)
    

    colorCounter = len(df[spatialBinField].unique()) # Used to grab the colors from the colorList using list indexing
    
    
    # Left as an example on how to set the chart color.
    sns.set(rc={'figure.figsize':(11.7,8.27), 'axes.facecolor':'black'})
    
    #sns.set(rc={'figure.figsize':(11.7,8.27)})


    
    ax = sns.scatterplot(df[timestamp_column],df[spatialBinField],hue=df[spatialBinField], palette=colorsList[:colorCounter]) # create the sns scatter
    

    
    if temporalBinType == "month_year":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%b %Y")).unique()
        
        if type(pp)== np.ndarray:
        
            xAxisTickerNum = _xAxisLenGenerator(pp)[0]
            
            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(MONTHLY,interval = xAxisTickerNum )
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%b-%Y")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(months=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(months=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(months=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(months=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%b-%Y")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
        else:
            pass
        
    
    elif temporalBinType == "week_year":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%Y-%W")).unique()
        
        if type(pp) == np.ndarray:
        
            xAxisTickerNum = _xAxisLenGenerator(pp)[0]
            
            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(WEEKLY, interval = xAxisTickerNum)
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%Y-%W")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%Y-%W")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
        else:
            pass
                
        
    elif temporalBinType == "week_month_year":

        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%Y-%b-%W")).unique()
        
        if type(pp)== np.ndarray:
        
            xAxisTickerNum = _xAxisLenGenerator(pp)[0]
            
            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(WEEKLY, interval = xAxisTickerNum)
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%Y-%b-%W")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(weeks=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(weeks=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%Y-%b-%W")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
        else:
            pass
    
    elif temporalBinType == "year_month_day":
        qq = df[timestamp_column].dt.date.unique()
        qq = sorted(qq)
        qqIndex = len(qq)
        date_start = qq.pop(0)
        date_end = qq.pop(qqIndex-2)
        
        pp = df[timestamp_column].map(lambda x: x.strftime("%b-%d")).unique()
        
        if type(pp)== np.ndarray:
        
            xAxisTickerNum = _xAxisLenGenerator(pp)[0]
            
            if type(xAxisTickerNum) == int:
        
                rule = rrulewrapper(DAILY, interval = xAxisTickerNum)
                loc = RRuleLocator(rule)
                formatter = DateFormatter("%b-%d")
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(days=-xAxisTickerNum)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(days=xAxisTickerNum), "%Y-%m-%d"))])
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
            else:
                ax.set_xlim([mdates.datestr2num(datetime.datetime.strftime(date_start + relativedelta(days=-1)
                                                                              , "%Y-%m-%d")), mdates.datestr2num
                             (datetime.datetime.strftime(date_end + relativedelta(days=1), "%Y-%m-%d"))])
                loc = plticker.MaxNLocator()
                formatter = DateFormatter("%b-%d")
                ax.xaxis.set_major_locator(loc)
                ax.xaxis.set_major_formatter(formatter)
                
        else:
            pass
        


    
    # This ensures that only the cluster numbers are on the yaxis
    
    ax.set_yticks(df[spatialBinField].unique().tolist())
    
    # This reverses the legend so that it matches the pattern of the scatter plot color from top-to-bottom
    
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc="center left", bbox_to_anchor=(1.0,0.5),ncol=1)
    

    if len(saveLocation)>0:
        #ax.write_image(saveLocation)
        ax.figure.savefig(saveLocation)
    elif inNotebookVisual == True:
        return ax
    else:
        print("Either provide a dir location to save to disk or visualize graphic in notebook")
    






colorsList = [(0/255.0,255/255.0,0/255.0),
              (0/255.0,0/255.0,255/255.0),
              (255/255.0,255/255.0,0/255.0),
              (0/255.0,255/255.0,0/255.0),
              (0/255.0,0/255.0,255/255.0),
              (255/255.0,255/255.0,0/255.0),
              (0/255.0,255/255.0,0/255.0)
              ]





def _xAxisLenGenerator(InputList):
    emptyList=[]
    if len(InputList) <= 12:
        emptyList.append(1)
    elif 12 < len(InputList) <= 24:
        emptyList.append(2)
    elif 24 <  len(InputList) <= 36:
        emptyList.append(4)
    elif 36 < len(InputList) <= 48:
        emptyList.append(5)
    elif 48 < len(InputList) <= 60:
        emptyList.append(6)
    elif 60 < len(InputList) <= 72:
        emptyList.append(7)
    elif 72 < len(InputList) <= 84:
        emptyList.append(8)
    elif 84 < len(InputList) <= 96:
        emptyList.append(9)
    elif 96 < len(InputList) <= 108:
        emptyList.append(10)
    elif 108 < len(InputList) <= 120:
        emptyList.append(11)
    elif 120 < len(InputList) <= 132:
        emptyList.append(12)
    else:
        loc = AutoDateLocator() # this locator puts ticks at regular intervals
        emptyList.append(loc)

    return emptyList
