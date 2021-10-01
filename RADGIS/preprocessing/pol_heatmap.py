from ..utils import constants, utils
import numpy as np
import pandas as pd
from collections import Counter
import xlsxwriter


"""
Create a heatmap that depicts the temporal pattern for any dataset that includes a datetime
column. The heatmap does not include a spatial dimension. Also, the module was created for HVI
targeting. This means that when using it for HVI targeting you should filter the input dataset
spatially before running. See the readme file for more information. There are two functions:
one that creates a heatmap with month of year and one that creates a heatmap with week of year. 

------------------------


Example


from RADGIS.preprocessing import pol_heatmap

pol_heatmap.heatmap(dataframe, temporalBinType, save_location, timestamp_column=constants.DATETIME)


"""



# Helper functions

# Fills in missing days.
def _addDays(df):
    all_days = pd.date_range(df.just_date.min(), df.just_date.max(), freq="D")
    po = all_days
    po = po.map(lambda t: t.strftime('%Y-%m-%d'))
    all_days = set(po)
    dfDaySet = set(df.just_date.tolist())
    difference = set(map(str,all_days)) - dfDaySet
    if len(difference) >= 1:
        counter = -1
        for d in difference:
            # Add this as the default. It's a placeholder and will be updated later outside of this function.
            df.loc[counter] = [0,"01", "Monday", d]
            counter -= 1
    else:
        pass

# Fills in missing hours.
def _add_Hours(x):
    fullHourSet = set(range(0, 23+1))
    hourSet = set(x.HourOfDay)
    difference = fullHourSet - hourSet
    return list(difference)





# Main function that formats the data.

def heatmap(dataframe, temporalBinType, save_location, timestamp_column=constants.DATETIME):
    
    '''
    Return a xlsx file saved to disk.

    :param dataframe: pandas DataFrame or TrajDataFrame
        DataFrame or TrajDataFrame to be plotted
     :param temporalBinType: determines the temporal extent of the scatter plot. Options are:
        "MonthOfYear"
        "WeekOfYear"
    :param save_location: path and name with file extention (i.e., save_location=r"D:\Projects\20191211_TemporalChart_POL\file_name.xlsx")
    :param timestamp_column: DataFrame or TrajDataFrame column that contains the datetime information.
        Default is constants.DATETIME, which applies if TrajDataFrame and the original tdf datetime column is used.
    
    '''
    
    df = dataframe.copy()
    

    # Add the columns and formatting that will be used to create the heatmap.
    
    # A conditional statement based on the user's temporalBinType input.
    if temporalBinType == "MonthOfYear":
        df[temporalBinType] = df[timestamp_column].dt.year.astype(str) + '-' + df[timestamp_column].dt.month.astype(str).apply(lambda x: "0" + x if len(x) == 1 else x)
    elif temporalBinType == "WeekOfYear":
        df[temporalBinType] = df[timestamp_column].dt.year.astype(str) + '-' + df[timestamp_column].dt.strftime('%U').apply(lambda x: "0" + x if len(x) == 1 else x)
    
    # Create a column for the day of week name and for the hour of day. Add a leading 0 to the hour of day if it's a single digit.
    df["DayOfWeek"] = df[timestamp_column].dt.day_name()
    df['HourOfDay'] = df[timestamp_column].dt.hour.astype(str).apply(lambda x: "0" + x if len(x) == 1 else x)
    
    # Count the events by binning them into the selected temporalBinType, day of week name, and hour of day. 
    df["TotalHrByYearMonthDayNameHour"] = df.groupby([temporalBinType, "DayOfWeek", "HourOfDay"])[timestamp_column].transform(lambda x: len(x.dt.date.unique()))
    
    # Add the date column, which will be used to fill in the missing days using the _addDays helper function.
    df['just_date'] = df[timestamp_column].dt.date
    df["just_date"] = df.just_date.map(lambda t: t.strftime('%Y-%m-%d'))
    
    # Only keep the required columns. This is cleaner and decreases the size of the dataset that is processed.
    df = df.filter(items=["TotalHrByYearMonthDayNameHour", "HourOfDay", "DayOfWeek", "just_date"])

    # Fill in missinges days that are within the min/max range.
    _addDays(df)

    df.reset_index(drop=True,inplace=True)
    
    # Redo these two columns now that the missing dates have been filled in since there could be new rows
    # that represent newly added days with the placeholder values inserted from the _addDays function. Also, the just_date
    # column is redone because it needs to be a pandas timestamp.
    df["just_date"] = pd.to_datetime(df.just_date)
    df["DayOfWeek"] = df.just_date.dt.day_name()
    
    # Redo this column because we did not include it when we filtered the dataframe. It was not included
    # because it had to be redone since we added missings days.
    if temporalBinType == "MonthOfYear":
        df[temporalBinType] = df['just_date'].dt.year.astype(str) + '-' + df['just_date'].dt.month.astype(str).apply(lambda x: "0" + x if len(x) == 1 else x)
    elif temporalBinType == "WeekOfYear":
        df[temporalBinType] = df['just_date'].dt.year.astype(str) + '-' + df['just_date'].dt.strftime('%U').apply(lambda x: "0" + x if len(x) == 1 else x)
        
    
    df["HourOfDay"] = df["HourOfDay"].astype(int)
    
    # Create a groupby object that is passed to the _add_Hours helper function that fills in missing hours.
    day_Group = df.groupby(["just_date"], sort=False)

    # Fill in missing hours.
    results = day_Group.apply(_add_Hours)

    results = pd.DataFrame(results)
    
    # This takes the index, which is the date, and makes it into a column.
    results["just_date"]=results.index.get_level_values("just_date")
    
    # Rename the column that is comprised of the missing hours. Now called HourOfDay.
    results.rename(columns={0:"HourOfDay"}, inplace=True)
    
    # Take each row and stack it on the date where the hours of the day that are in a list are stacked vertically under each date.
    sxy = results.apply(lambda x: pd.Series(x["HourOfDay"]), axis=1).stack()
    
    # Name the series.
    sxy.name = "HourOfDay"
    
    # Turn the series into a dataframe.
    results = pd.DataFrame(sxy)
    
    # Take the index, the date called "just_date", and turn it into a column in the dataframe.
    results["just_date"]=results.index.get_level_values("just_date")

    # Create this column to match the original dataframe because we are going to concat them together.
    results["TotalHrByYearMonthDayNameHour"] = 0
    
    # Drop the date index.
    results.reset_index(drop=True,inplace=True)
    results["HourOfDay"] = results["HourOfDay"].astype(int)
    results["DayOfWeek"] = results.just_date.dt.day_name()
    
    # Create this column in the dataframe to match the original dataframe.
    if temporalBinType == "MonthOfYear":
        results[temporalBinType] = results['just_date'].dt.year.astype(str) + '-' + results['just_date'].dt.month.astype(str).apply(lambda x: "0" + x if len(x) == 1 else x)
    elif temporalBinType == "WeekOfYear":
        results[temporalBinType] = results['just_date'].dt.year.astype(str) + '-' + results['just_date'].dt.strftime('%U').apply(lambda x: "0" + x if len(x) == 1 else x)

    # Concat the two dataframes together.
    new_df = pd.concat([df, results])
    new_df.reset_index(drop=True,inplace=True)

    # Set the object type for the day of week column to a category for ordering days (i.e., Monday, Tuesday, etc.)
    new_df["DayOfWeek"] = new_df["DayOfWeek"].astype("category")
    new_df["DayOfWeek"].cat.set_categories(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], inplace=True)

    # Turn the value 0 to NaN. The rows with a value of 0 are the rows that we added to the dataframe. 
    # They do not have a count. They are turned to NaN, instead of staying "0s" because that is what works
    # with the final heatmap. We want them to have no value in the cells so that they are blank and not colored.
    new_df["TotalHrByYearMonthDayNameHour"] = new_df["TotalHrByYearMonthDayNameHour"].apply(lambda x: np.nan if x==0 else x)
    
    # Create the pivot table object that the final heatmap is built on.
    result1 = new_df.pivot_table(index=[temporalBinType, "DayOfWeek"], columns='HourOfDay', values='TotalHrByYearMonthDayNameHour', aggfunc=np.sum, margins=True, margins_name="Total").replace(0,np.nan)
    
    # Remove the last row that contains the total from the pivot table. 
    result1 = result1.iloc[:-1]
    
    # Creates the temporal bin totals and the grand total.
    result2 = pd.concat([d.append(d.sum().rename((k, "Total"))) for k, d in result1.groupby(level=0)]).append(result1.sum().rename(("Grand", "Total")))

    # Create the grand total list. This is done because we want to insert the words "Grand Total" into the excel doc.
    grand_total_sum = result1.sum().to_list()
    grand_total_sum.insert(0,"Total")
    grand_total_sum.insert(0,"Grand")

    # Continue building out lists with the totals. This creates the hour of day total list and adds the string "total"
    # to the list.
    slog = []
    slog_groupby = result1.groupby(level=0)
    for d, k in slog_groupby:
        slog.append(k.sum())

    slog2=[]
    for p in slog:
        p = p.to_list()
        p.insert(0,"Total")
        for pp in p:
            slog2.append(pp)
    
    # Determine the number of temporal bins that are present in the dataset. Then create a range in a list that is used
    # to determine the cell extent, which is used to apply the heatmap colors.
    range_finder = list(result2.index.get_level_values(temporalBinType))
    range_finder = Counter(range_finder)
    range_finder = list(range_finder.values())


    # The range_finder tells us how many levels are under the MonthOfYear or WeekOfYear pivot. At a minimum there could be
    # two levels, which would occur if there was only one week of data. The range_finder list would look like this:
    # [8,1], where 8 reprsents Monday through Sunday + the Total below Sunday and 1 represents the Grand Total level (two levels).
    # We need to determine how many levels there are to apply the heatmap colors. This loop will iterate over the 
    # range_finder list and return the Monday-Sunday levels minus the total. It will stop the iteration before the Grand
    # Total level is appened to the list. The returned value in the list reflects Monday-Sunday. So [7] is returned if there
    # is only one week of data and [7,7] would be returned for two weeks of data and so on. 
    empty_List1 = []
    counter3 = 1
    for d in range_finder:
        stopper = len(range_finder)
        if counter3 != stopper:
            empty_List1.append(d-1)
            counter3 += 1

    # Build lists that contain the alpha numeric cells in in Excel for conditional formatting. This is and has been a painful
    # process because the conditional formatting is not applied globally across the entire worksheet. It is applied locally. 
    # For example, all of the Monday-Sunday cells, across the worksheet, have the same conditional formatting definition meaning
    # that the heatmap is relative to these values. 
    empty_List2 = []
    main_column_totals = []
    main_row_totals = []
    grand_total_List = []
    grand_total_list_border = []
    counter2 = 1
    index_check = 0
    
    for d in empty_List1:
        # Enter this conditional statement first because we know where we are starting in Excel. There is only
        # one iteration through the first condition upon which it enters the else statement. Because we know 
        # where, position wise, we started in Excel we can enter the else and calculate where the next positions should be.
        if counter2 == 1:
            empty_List2.append("C2:Z" + str(d+1)) # The Monday-Sunday and 0-2300 hours cells.
            main_row_totals.append("C" + str(d+2) + ":" + "Z" + str(d+2)) # The horizontal total for each temporal bin.
            main_column_totals.append("AA2:AA" + str(d+1)) # The vertical total for each day of week per each temporal bin.

            counter2 +=1
            index_check += d+3 # This index_check starts with this pattern, but changes in the next condition.
            grand_total_list_border.append(index_check - 1) # The start of identifying where the Grand Total is located. 
                                                            # The number actually represents the temporal bin level, but
                                                            # we will take care of that later by adding 1.
                                                            
        # Enter this conditional statement second because now we add where we are in excel using the index_check. 
        else:
            empty_List2.append("C" + str(index_check) + ":" + "Z" + str(index_check+d-1))
            main_row_totals.append("C" + str(index_check+d) + ":" + "Z" + str(index_check+d))
            grand_total_List.append(index_check)
            main_column_totals.append("AA" + str(index_check) + ":" + "AA" + str(index_check+d-1))
            index_check += d+1
            grand_total_list_border.append(index_check - 1)

    # Format the vertical total for each day of week per each temporal bin level.
    main_column_totals_color = ",".join(main_column_totals)
    main_column_totals_color = main_column_totals_color.replace(",", " ")
    first_main_column_totals = main_column_totals.pop(0)
    
    if temporalBinType == "WeekOfYear":
        grand_total = len(grand_total_List) - 1
        grand_total = grand_total_List.pop(grand_total)+2
        grand_total = "C" + str(grand_total) + ":" + "Z" + str(grand_total)
    else:
        pass
        


    # Format the Monday-Sunday and 0-2300 cells per each temporal bin.
    main_colorScale = ",".join(empty_List2)
    main_colorScale = main_colorScale.replace(",", " ")
    first_colorScale = empty_List2.pop(0)


    # Format the totals per each temporal bin. We will apply a multi-range selection for conditional formatting these.
    # To do that we will need the first selectiom by itself. For example, 'C9:Z9'. And then we will need all of the
    # other selections by themselvels without the first selection. For example, 'C17:Z17 C25:Z25'. 
    # The main_row_totals_colorScale variable is all of the other selections. The first_main_row_totals_colorScale variable is
    # just the first selection by itself. It will be used to apply conditional formatting later using a multi-range. A
    # multi-range requires two selections of the data. The first selection is only the start to end row (i.e., 'c9:Z9'), 
    # which is what this is.
    main_row_totals_colorScale = ",".join(main_row_totals)
    main_row_totals_colorScale = main_row_totals_colorScale.replace(",", " ")
    
    # Using pop does no work if the time scale is small. Because
    # there may only be on item in this list if it is a small time scale.
    if len(main_row_totals) == 1:
        first_main_row_totals_colorScale = main_row_totals[0]
    else:
        first_main_row_totals_colorScale = main_row_totals.pop(0)

    grand_total = main_row_totals[:]
    grand_total_counter = len(grand_total)
    
    # Using pop does no work if the time scale is small. Because
    # there may only be one item in this list if it is a small time scale.
    # Getting the Grand Total position in Excel. Not quite the correct position. We will need to add 1 to the number. Completed
    # later. 
    if len(grand_total) == 1:
        grand_total = grand_total[0]
    else:
        grand_total = grand_total.pop(grand_total_counter-1)


    # This is where we get the correct position in Excel for the Grand Total. Need to separate the number from the letter.
    # Once we have the number we add 1. Then string concat them back to the correct alpha numeric represenation of 
    # positions in Excel (i.e., 'C121:Z121')
    middle = grand_total.find(":")
    number = grand_total[1:middle]
    new_number = int(number)+1
    grand_total = "C"+str(new_number)+":Z"+str(new_number)

    # The character_range list will be used later for applying font formating. The list is comprised of the
    # Excel alpha characters for the position of where the Total rows extend from Total (B) to the end (AA).
    # Have to manually add AA at then end of this list using the extend function.
    character_range = []
    for x in [chr(i) for i in range(ord('B'),ord('Z')+1)]:
        character_range.append(x)
    character_range.extend(["AA"])

    # Make a copy and insert A at the begining because this will be used for the Grand Total that starts at Column A
    # because "Grand" is in a cell in that column.
    character_range_grandTotal = character_range.copy()
    character_range_grandTotal.insert(0,"A")

    # Get the last number in this list. It is the last temporal bin total. Then add 1 to get the alpha numeric cells
    # in Excel for where the Grand Total is.
    grandTotal_index = grand_total_list_border.copy()
    grandTotal_index = grandTotal_index.pop(len(grandTotal_index)-1)
    grandTotal_index += 1

    # We have the alpha characters for the extent of the Grand Total row. Now we just need to add the row number, which
    # is in the grandTotal_index. Note that this effort is not for the conditional formatting aka the heatmap. It is for
    # changing the font format. The final result is the grandTotal_cells list in which are the Excel alpha numeric characters
    # that represent the position in the workbook of the Grant Total range (i.e., ["A121", "B121", etc])
    grandTotal_cells = []
    for d in character_range_grandTotal:
        grandTotal_cells.append(d+str(grandTotal_index))



    # Where the xlsx document is written to.
    writer = pd.ExcelWriter(save_location, engine='xlsxwriter')
    
    # Result is the pandas dataframe that has been reshaped using pivot. It's the core of the xlsx from which
    # we apply font and conditional formatting changes.
    result2.to_excel(writer, sheet_name=temporalBinType,header = True,index=True)
    
    # Create and name the sheet in the workbook.
    workbook = writer.book
    worksheet = writer.sheets[temporalBinType]
    
    # Apply the conditional format for the Monday-Sunday and 0-2300 hours cells in each temporal bin.
    worksheet.conditional_format(first_colorScale, {"type":"3_color_scale", "min_color":"#63BE7B", "max_color":"#F8696B", "mid_color":"#FFEB84", "multi_range": main_colorScale })
    
    # Use a multi-range to create the condtional format for each total column per each temporal bin.
    worksheet.conditional_format(first_main_column_totals, {"type":"3_color_scale", "min_color":"#63BE7B", "max_color":"#F8696B", "mid_color":"#FFEB84", "multi_range": main_column_totals_color })                            
    format1_topAndbottom = workbook.add_format({"bottom":5, "top":5})
    format2_totalFontSize = workbook.add_format({"font_size": 18, "bold": True, "align":"center"})
    format3_grandTotalFontSize = workbook.add_format({"font_size": 24, "bold": True, "align":"center"})
    total_fontSize = []

    # The grand_total_list_border contains the end (last row) of each total for each temporal bin. Iterate over it 
    # and the alpha range from C-AA to apply the format_1_topAndbottom to each cell. This formal
    # centers the numbers and ensures that blanks aka NaNs are replaced with 0s.
    for d in grand_total_list_border:
        worksheet.conditional_format("AA"+str(d), {"type" : "no_blanks", "format" : format1_topAndbottom })
        for x in [chr(i) for i in range(ord('C'),ord('Z')+1)]:
            worksheet.conditional_format(x+str(d), {"type" : "no_blanks", "format" : format1_topAndbottom })
            #worksheet.conditional_format("AA"+str(d), {"type" : "no_blanks", "format" : format1_topAndbottom })

         # Make the total_fontSize list used right below. This is the Excel cell position for each total row per 
         # temporal bin.
        for c in character_range:
            total_fontSize.append(c+str(d))
    # Zip the slog2 list (value in the cells for each total row per temporal bin) and the total_fontSize
    # list (Excel alpha numeric cell for each total row per tempioral bin) together. Then apply
    # the font format.
    for f, b in zip(slog2,total_fontSize ):
        worksheet.write(b, f, format2_totalFontSize)
        
    # Zip these two list together. grandTotal_cells is a list of the all of the excel alpha numeric cells
    # that comprise the Grand Total row. The grand_total_sum is a list of all of the values in each cell for the
    # Grand Total row. The character format is edited using the dictionary format3_grandTotalFontSize.
    for t, y in zip(grand_total_sum, grandTotal_cells):
        worksheet.write(y, t, format3_grandTotalFontSize)

    # Use a multi-range selection to apply the heatmap aka conditional formatting to the each total row per 
    # temporal bin.
    worksheet.conditional_format(first_main_row_totals_colorScale, {"type":"3_color_scale", "min_color":"#63BE7B", "max_color":"#F8696B", "mid_color":"#FFEB84", "multi_range": main_row_totals_colorScale })
    
    # Apply the conditional format aka heatmap to the Grand Total cells.
    worksheet.conditional_format(grand_total, {"type":"3_color_scale", "min_color":"#63BE7B", "max_color":"#F8696B", "mid_color":"#FFEB84"})
    #return print(grand_total)
    #return print(first_main_row_totals_colorScale)

    writer.save()
