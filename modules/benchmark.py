# -*- encoding: utf-8 -*-
'''
Filename         :return.py
Description      :该模块用于计算月期望收益率
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import pandas as pd
import time
from collections import OrderedDict
from getStock import stockclass
from getDate import dateclass
import basicFunction as fun

# 设定开始与结束日期
beginDate = '20050101'
endDate = '20210531'

# 创建日期和数据获取对象
stockClass = stockclass('data/stock/1day', preRead=['CloseR', 'OpenR'])
dateClass = dateclass()

# 获取日期数据
dates = dateClass.get_dates(beginDate, endDate)
months = dateClass.get_months(beginDate, endDate)
BOMs = dateClass.get_EOMs(beginDate, endDate)
EOMs = dateClass.get_BOMs(beginDate, endDate)

# 获取证券池
stockPools = stockClass.get_stockPools(dates)

# 存储数据
RetDaily, NevDaily, RetMonthly, NevMonthly = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()

netValue = 1

# 计算程序运行时间
print('\n日频数据计算开始')
funStart, number = time.perf_counter(), 0

for thisDate in dates:
    nextDate = dateClass.get_afterDate(thisDate, 1, showProcess=False)
    stockPool = stockPools[thisDate]
    if nextDate != 'out of range':
        dataPrice = stockClass.get_data(secIDs=stockPool, dates=[thisDate, nextDate], fields=['OpenR'], showProcess=False)
        thisPrice = dataPrice[dataPrice['dates'] == thisDate]['OpenR']
        nextPrice = dataPrice[dataPrice['dates'] == nextDate]['OpenR']
        dataReturn = nextPrice / thisPrice - 1
    else:
        dataPrice = stockClass.get_data(secIDs=stockPool, dates=[thisDate], fields=['OpenR', 'CloseR'], showProcess=False)
        thisPrice = dataPrice['OpenR']
        nextPrice = dataPrice['CloseR']
        dataReturn = nextPrice / thisPrice - 1
    # 存储全市场等权收益
    RetDaily[thisDate] = dataReturn.mean()
    # 计算当日净值
    netValue = netValue * (1 + RetDaily[thisDate])
    NevDaily[thisDate] = netValue
    # 显示当前进度
    number += 1; funPerc = number / len(dates)
    fun.processing_bar(funPerc, funStart)

RetDaily = pd.Series(RetDaily, name='RetDaily')
RetDaily.index = pd.Series(RetDaily.index, name='dates')
NevDaily = pd.Series(NevDaily, name='NevDaily')
NevDaily.index = pd.Series(NevDaily.index, name='dates')

print('\n日频数据计算完成')

print(RetDaily)
print(NevDaily)

# 计算程序运行时间
print('\n月频数据计算开始')
funStart, number = time.perf_counter(), 0

for thisMonth in months:
    lastMonth = dateClass.get_beforeMonth(thisMonth, 1, showProcess=False)
    if lastMonth != 'out of range':
        # 获取本月月初与下月月初的组合净值
        netValueThisEOM = NevDaily.loc[EOMs[thisMonth]]
        netValuelastEOM = NevDaily.loc[EOMs[lastMonth]]
        # 计算收益率与净值
        RetMonthly[thisMonth] = netValueThisEOM / netValuelastEOM - 1
        NevMonthly[thisMonth] = netValueThisEOM
    else:
        # 获取本月月初与下月月初的组合净值
        netValueThisEOM = NevDaily.loc[EOMs[thisMonth]]
        netValueThisBOM = NevDaily.loc[BOMs[thisMonth]]
        # 计算收益率与净值
        RetMonthly[thisMonth] = netValueThisEOM / netValueThisBOM - 1
        NevMonthly[thisMonth] = netValueThisEOM
    # 显示当前进度
    number += 1; funPerc = number / len(months)
    fun.processing_bar(funPerc, funStart)

RetMonthly = pd.Series(RetMonthly, name='RetMonthly')
RetMonthly.index = pd.Series(RetMonthly.index, name='months')
NevMonthly = pd.Series(NevMonthly, name='NevMonthly')
NevMonthly.index = pd.Series(NevMonthly.index, name='months')

print('\n月频数据计算完成')

print(RetMonthly)
print(NevMonthly)


RetDaily.to_csv('factor/benchmark/benchmarkRetDaily.csv')
NevDaily.to_csv('factor/benchmark/benchmarkNevDaily.csv')
RetMonthly.to_csv('factor/benchmark/benchmarkRetMonthly.csv')
NevMonthly.to_csv('factor/benchmark/benchmarkNevMonthly.csv')
