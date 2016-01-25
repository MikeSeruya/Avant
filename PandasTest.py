"""
Pandas test

@author: Mike Seruya
"""

from numpy.random import randn
from pandas import *
import matplotlib.pyplot as plt

def withinHalf(rng, ts):
    "This takes a date range and a series and returns a series\
    where the absolute difference between a number and the next\
    number in the series is less than .5"
    newDict = {}  #empty Dictionary to store value

    #for each item in rng except the last
    for pos in range(rng.size-1):
        #if current item is within 0.5 of next item
        if abs(ts[pos] - ts[pos+1]) <= .5:
            # add current item to newDict
            newDict[rng[pos].strftime("%Y-%m-%d %X")] = ts[pos]
            #add next item to newDict
            newDict[rng[pos+1].strftime("%Y-%m-%d %X")] = ts[pos+1]
    newSeries = Series(newDict) #convert newDict to Series and store in newSeries
    return newSeries; # return newSeries


rng = date_range('1/1/2011', periods=72, freq='H')
ts = Series(randn(len(rng)), index=rng)

withinHalfSeries = withinHalf(rng, ts)
print withinHalfSeries

plt.figure()
ts.plot(kind='hist') #plot histogram of ts
plt.show() # display histogram

# create a series with the the rolling average of 
averageSeries = ts.add(ts.pct_change(periods=5))

# create a dataFrame with ts and the rolling averages in a second column
myDf = concat([ts,averageSeries], join='inner', axis=1)
print myDf

# change all negative numbers in the rolling average column to 0
myDf[1] = myDf[1].clip(lower=0)
print myDf

# write myDf to excel
writer = ExcelWriter('myDf.xlsx')
myDf.to_excel(writer,'Sheet1')
worksheet = writer.sheets['Sheet1']
worksheet.set_column('A:C',20)
worksheet.hide_gridlines(2)
writer.save()