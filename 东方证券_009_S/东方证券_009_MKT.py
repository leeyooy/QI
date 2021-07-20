#导入模块
import sys
sys.path.append('modules')
from getQuote import quoteclass
from getDate import dateclass
from getStock import stockclass
import pandas as pd
import numpy as np

#设置开始与结束时间
beginDate = '20050101'
endDate  = '20050301'

#获取全部的时间与股票池
dateClass = dateclass()
dates = dateClass.get_dates(beginDate,endDate)

stockClass = stockclass('data/stock/1day',preRead=['MVFloat'])
stockPools = stockClass.get_stockPools(dates,delST=True, delStop=True,delNew=True, minDate=60, showProcess=True)

quoteClass = quoteclass('data/stock/5min')

# 1 计算每支股票每日每个时间段收益率r

#时间分段,单位为分钟
n = 5
orders = int(240 / n)

# 2 计算每日每个时间段MKT
#创建factorMKT储存结果
factorMKT =pd.DataFrame(index = dates,columns = range(0,orders))
for date in dates:
    #获取上个交易日
    lastDate = dateClass.get_beforeDate(date, 1, showProcess=True)
    # 获取昨日MVFloat用于计算昨日流通市值加权权重Weights
    if lastDate != 'out of range':
        MVFloat = stockClass.get_data(secIDs=stockPools[date], dates=[lastDate], fields=['MVFloat'], showProcess=True) ['MVFloat']
        Weight = MVFloat / MVFloat.sum()
    else:
        Weight = np.nan
    Open = quoteClass.get_filename(field = ['Open'], date = [date], type='5min')
    dataOpen = quoteClass.get_data(secIDs = stockPools[date],dates = [date], fields=['Open'], showProcess=True)['Open']
    print(dataOpen)
    # for order in range(0,orders):
    #     factorMKT_D = (SpanReturns * Weight).sum()
    #     factorMKT.loc[date] = factorMKT_D

# print(factorMKT)

# factorMKT.to_csv('factor/middle/东方证券_009_MKT.csv')