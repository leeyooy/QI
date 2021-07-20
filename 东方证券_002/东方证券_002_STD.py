# -*- encoding: utf-8 -*-
'''
Filename         :factor.py
Description      :该模块用于计算因子数值
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
stockClass = stockclass('data/stock/1day', preRead=['DailyReturnSimple'])
dateClass = dateclass('data/date')

# 获取月份数据和月末日期数据
months = dateClass.get_months(beginDate, endDate)
EOMs = dateClass.get_EOMs(beginDate, endDate)

# 获取每月月末的证券池
stockPools = stockClass.get_stockPools(EOMs)

# 设置有序字典存储因子
factorResult = OrderedDict()

# 计算程序运行时间
print('\n因子计算开始')
funStart, number = time.perf_counter(), 0

for month in months:
    # 获取当前证券池
    stockPool = stockPools[EOMs[month]]

    # 获取本月数据
    DUMs = dateClass.get_DUMs(month, showProcess=False)
    returnMonth = stockClass.get_data(secIDs=stockPool, dates=DUMs, fields=['DailyReturnSimple'], showProcess=False)

    # 计算本月因子数值
    factorMonth = OrderedDict()

    # 遍历当月证券池中的所有股票
    for secID in stockPool:
        # 获取该证券当月的收益率数据
        returnSec = returnMonth.loc[secID, :].sort_values(by='dates').set_index('dates')['DailyReturnSimple']
        # 计算该证券在目标区间的收益率波动率
        factorMonth[secID] = returnSec.std()

    # 显示当前进度
    number += 1
    funcPerc = number / len(months)
    fun.processing_bar(funcPerc, funStart)

    # 将本月因子数据存入总数据中
    factorResult[month] = pd.Series(factorMonth, name=month)

print('\n因子计算完成')

# 将所有期限的所有证券的因子值转变为数据框类型(pd.DataFrame)
factorResult = pd.DataFrame(factorResult)
factorResult.index = pd.Series(factorResult.index, name='secIDs')

# 输出计算结果
print(factorResult)

# 存储计算结果
factorResult.to_csv('factor/final/东方证券_002_STD.csv')
