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
endDate_data  = '20210531'   #用于获取数据设定日期，可调整
beginDate_test = '20050105'  #用于测试设定日期，可调整
endDate_test  = '20210531'   #用于测试设定日期，可调整

n = 5  #时间分段,单位为分钟
orders = int(240 / n)

#获取全部的时间与股票池
dateClass = dateclass('data/date')
dates_data  = dateClass.get_dates(beginDate_data,endDate_data)  
dates_test = dateClass.get_dates(beginDate_test,endDate_test)  

stockClass = stockclass('data/stock/1day',preRead=['MVFloat'])
stockPools = stockClass.get_stockPools(dates_data ,delST=True, delStop=True,delNew=True, minDate=60, showProcess=True)

# 2 计算每日每个时间段MKT

# 2.1计算权重
# 获取昨日MVFloat用于计算昨日流通市值加权权重Weights
factorMKT =pd.DataFrame(index = dates_test,columns = range(0,orders))

# 读取SpanReturn数据
dataSpanReturns = np.load('data/stock/5min/StockSpanReturn5Min.npy')
dataSpanReturns = pd.DataFrame(dataSpanReturns,index = se,columns = [order,])

for date in dates_test:
    #获取上个交易日
    lastDate = dateClass.get_beforeDate(date, 1, showProcess=True)
    
    MVFloat = stockClass.get_data(secIDs=stockPools[date], dates=[lastDate], fields=['MVFloat'], showProcess=True) ['MVFloat']  
    Weight = MVFloat / MVFloat.sum()
    for order in range(0,orders):
        SpanReturns = dataSpanReturns['SpanReturn'][(SpanReturns['dates'] == date)& (SpanReturns['order'] == order)]
        factorMKTD = (SpanReturns * Weight).sum()
        factorMKT.loc[date] = factorMKTD 
print(factorMKT)

factorMKT.to_csv('factor/middle/东方证券_009_MKT.csv')

