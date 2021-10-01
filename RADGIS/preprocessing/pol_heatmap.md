
![](/images/pol_heatmap_header.PNG?raw=True)

# Visually Stunning Heatmap for Temporal Pattern Recognition in Python

## TL;DR
> * Python implementation of a heatmap that teases out the temporal patterns for an HVI at one location.





> Have you ever struggled with conveying the temporal patterns of a High Value Individual (HVI) that you are familiar with to your audience? You may know everything about the HVI that you are following. You may know that the HVI is always at their bed down location (BDL) by 1800 and always leaves their BDL by 0800. Being the great orator that you are you can brief this to your J2 in your sleep. But what if you're an introvert who struggles with briefing? Or what if your HVI's temporal patterns are much more nuanced? Well, if you're anything like me, who falls into the introvert category, you may want to include a colorful picture in your briefing to detract from your fumbling words…I like lamp. Enter the heatmap with it's crisp trio color palette that effortlessly takes the J2's eyes from your face to the slide. Boom! Have no fear Ponyboy, your J2 thinks that you're the bee's knees. 




> All seriousness aside, here's the boring beef that makes this magic-maker possible:

> * A datetime column.


> That's it. I know it sounds too good to be true. And believe me when I say that it is because the Python implementation is messy and almost unreadable so good luck. 


> Why a heatmap? Because you can display dates on the y-axis and time on the x-axis, but mainly because the heatmap colors are visually stimulating and intuitive. It just makes sense.

> Why Python? Because I took a Python course and now I'm a data scientist at the forefront of NGA's 2025 Strategy (ITP gold). Because it's easily reproducible silly. 

> You can totally make these heatmaps using pivot tables in Excel , some quick arthritis writhing copy/paste keyboard strokes (because we ctrl for Pete's sake), and conditional formatting. In fact, I used xlsxwriter, which is a do it in Excel Python library. Why? Because I could not figure out how to stack y-axis labels in Matplotlib or Seaborn. And having the finished heatmap in Excel is better for 99.9% of people whom have no desire to startup a virtual environment in anaconda and start a Jupyter kernel….ana what did he just say with an eye roll.

> What you need to know about the heatmap:

> * It's temporal not spatiotemporal…that's coming in a later post.



> * There are two temporal options aka temporal bins: week of year and month of year. 

> * A green-to-red gradient was used with green displaying the lowest count and red displaying the highest count. Orange is right in the middle. 

> * BYOD - Bring Your Own Dedupe. Sorry, but not sorry because you know your data best and how to best remove the duplicates if there are any (i.e., by minute, hour, etc)

> * Google "Anaconda" or "Python" or "GeekSquad" because this is a Python implementation so you will have to use it in Python and ensure that the dependencies are installed.

> Here's some pictures and stuff:

![](/images/pol_heatmap_2nd.PNG?raw=True)

> * Direct your peepers to the MonthOfYear column. Yep, it's the month of the year. This is the temporal bin that the user chose.

> * The DayOfWeek column is excatly that - the day of the week. 

> * The Total column has the total occurrences for each day of week per each temporal bin (month of year in this example). 

> * The Total row contains the total occurrences for each hour of day per each temporal bin (month of year in this example).

> * There is a Grand Total row at the very bottom of the heatmap (not in picture) that has the grand total for each hour of day for all months of the year (or weeks of year
if the user chose that temporal bin...you get the point). 

> * The colors are local not global. This means that the algorithm that assigns the green-to-red gradient to each cell's value is based on the local selection. 

> The local selections are:
![](/images/pol_heatmap_3rd.PNG?raw=True)

> * Red boxes: all cells in the DayOfWeek across the entire dataset are selected when the heatmap colors are assigned

> * Blue boxes: all cells in the Total column across the entire dataset are selected.

> * Purple boxes: all cells in the Total row across the entire dataset are selected.

> * Lastly, all cells in the Grand Total row at the bottom (not in picture) are selected.

