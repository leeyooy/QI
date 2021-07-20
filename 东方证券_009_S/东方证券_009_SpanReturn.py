# 1 计算每支股票每日每个时间段收益率r
#导入模块
import sys
sys.path.append('modules')
from getQuote import quoteclass
from getDate import dateclass
from getStock import stockclass
import pandas as pd
import numpy as np

#设置开始与结束时间
beginDate_data = '20050101'  #用于获取数据设定日期，可调整
endDate_data  = '20050110'   #用于获取数据设定日期，可调整
beginDate_test = '20050101'  #用于测试设定日期，可调整
endDate_test  = '20050110'   #用于测试设定日期，可调整

#获取全部的时间与股票池
dateClass = dateclass('data/date')
dates_data  = dateClass.get_dates(beginDate_data,endDate_data)  
dates_test = dateClass.get_dates(beginDate_test,endDate_test)  

stockClass = stockclass('data/stock/1day',preRead=['MVFloat'])
stockPools = stockClass.get_stockPools(dates_data ,delST=True, delStop=True,delNew=True, minDate=60, showProcess=True)

#获取参数——开盘与收盘（data1），用于计算收益率（data1）
quoteClass = quoteclass('data/stock/5min',preReadDates=dates_data ,preReadFields =['Open','Close'])
data1 = quoteClass.get_dataMultiDates(secIDs=stockPools[dates_test [0]], dates=dates_test , fields=['Open','Close'], showProcess=True)

#计算每支股票每日每个时间段简单收益率r
data1['dataSpanReturn'] = (data1['Close']- data1['Open'])/data1['Open']
dataSpanReturn = data1.drop(columns=['Open', 'Close'])
dataSpanReturn.reset_index(inplace = True)
dataSpanReturn = np.array(dataSpanReturn)

#保存为npy文件
np.save('data/stock/5min/StockSpanReturn5Min.npy',dataSpanReturn)