# -*- encoding: utf-8 -*-
'''
Filename         :东方证券_002_MKT.py
Description      :该模块用于计算市场因子MKT
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import pandas as pd
import time, sys
from collections import OrderedDict
sys.path.append('modules')
from getStock import stockclass
from getDate import dateclass
import basicFunction as fun

# 设定开始与结束日期
beginDate = '20050101'
endDate = '20210531'

# 创建日期和数据获取对象
stockClass = stockclass('data/stock/1day', preRead=['MVFloat', 'DailyReturnSimple'])
dateClass = dateclass('data/date')

# 获取月份数据和月初日期数据
dates = dateClass.get_dates(beginDate, endDate)
EOMs = dateClass.get_EOMs(beginDate, endDate)

# 获取证券池
stockPools = stockClass.get_stockPools(dates, minDate=60)

# 设置有序字典存储因子
factorResult = OrderedDict()

# 计算程序运行时间
print('\n因子计算开始')
funStart, number = time.perf_counter(), 0

for date in dates:

    # 如果碰到调仓日，则重新计算权重
    if date == dates[0] or date in EOMs.tolist():
        # 获取数据
        stockPool = stockPools[date]
        dataMVFloat = stockClass.get_data(secIDs=stockPool, dates=[date], fields=['MVFloat'], showProcess=False)['MVFloat']
        # 计算权重
        weights = dataMVFloat / dataMVFloat.sum()

    # 获取数据
    dataOriginal = stockClass.get_data(secIDs=stockPool, dates=[date], fields=['DailyReturnSimple'], showProcess=False)
    # 计算因子数值
    dailyReturn = dataOriginal['DailyReturnSimple']
    factorResult[date] = (dailyReturn * weights).sum()
    # 显示当前进度
    number += 1; funcPerc = number / len(dates)
    fun.processing_bar(funcPerc, funStart)

print('\n因子计算完成')

# 将所有期限的所有证券的因子值转变为数据框类型(pd.DataFrame)
factorResult = pd.Series(factorResult)

# 输出计算结果
print(factorResult)

# 存储计算结果
factorResult.to_csv('factor/middle/东方证券_002_MKT.csv')
