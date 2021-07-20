# 导入模块
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
beginDate_test = '20050105'  #用于测试设定日期，可调整
endDate_test  = '20050110'   #用于测试设定日期，可调整

n = 5  #时间分段,单位为分钟
orders = int(240 / n)

#获取全部的时间与股票池
dateClass = dateclass('data/date')
dates_data  = dateClass.get_dates(beginDate_data,endDate_data)  
dates_test = dateClass.get_dates(beginDate_test,endDate_test)  

stockClass = stockclass('data/stock/1day',preRead=['MVFloat'])
stockPools = stockClass.get_stockPools(dates_data ,delST=True, delStop=True,delNew=True, minDate=60, showProcess=True)

#读取SpanReturn数据
dataSpanReturn = np.load('data/stock/5min/StockSpanReturn5Min.npy',allow_pickle= True)
dataSpanReturn = pd.DataFrame(dataSpanReturn,index = None,columns =['secIDs','dates','order','SpanReturn'])
dataSpanReturn.set_index('secIDs',inplace = True)

# 计算权重
# 获取昨日MVFloat用于计算昨日SMB加权权重Weights
factorSMB =pd.DataFrame(index = dates_test,columns = range(0,orders))

for date in dates_test:
    #获取上个交易日
    lastDate = dateClass.get_beforeDate(date, 1, showProcess=True)
    MVFloat = stockClass.get_data(secIDs=stockPools[date], dates=[lastDate], fields=['MVFloat'], showProcess=True) ['MVFloat']  
    #排序分组
    MVFloatSmall = MVFloat.sort_values(ascending = True).iloc[:int(len(MVFloat) / 3)]
    MVFloatBig = MVFloat.sort_values(ascending = False).iloc[:int(len(MVFloat) / 3)]
    #计算权重
    WeightSmall = MVFloatSmall / MVFloatSmall.sum()
    WeightBig = MVFloatBig / MVFloatBig.sum()

    for order in range(0,orders):
        SpanReturnSmall = dataSpanReturn['SpanReturn'][(dataSpanReturn['dates'] == date) & (dataSpanReturn['order'] == order)]
        SpanReturnBig = dataSpanReturn['SpanReturn'][(dataSpanReturn['dates'] == date) & (dataSpanReturn['order'] == order)]
        factorSMBD = (SpanReturnSmall * WeightSmall).sum() - (SpanReturnBig * WeightBig).sum()
        factorSMB.loc[date] = factorSMBD 

print(factorSMB)
factorSMB.to_csv('factor/middle/东方证券_009_SMB.csv')