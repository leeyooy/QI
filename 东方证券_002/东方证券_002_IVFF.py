# -*- encoding: utf-8 -*-
'''
Filename         :factor.py
Description      :该模块用于计算因子数值
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import numpy as np
import pandas as pd
import statsmodels.api as sm
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
stockClass = stockclass('data/stock/1day', ['DailyReturnSimple'])
dateClass = dateclass('data/date')

# 获取月份数据和月初日期数据
months = dateClass.get_months(beginDate, endDate)
BOMs = dateClass.get_BOMs(beginDate, endDate)
EOMs = dateClass.get_EOMs(beginDate, endDate)

# 获取每月月末的证券池
stockPools = stockClass.get_stockPools(EOMs)

# 获取前期计算好的MKT数据
dataMKT = pd.read_csv('factor/middle/东方证券_002_MKT.csv')
dataMKT.columns = ['dates', 'MKT']
dataMKT['dates'] = dataMKT['dates'].apply(lambda x: str(x))
dataMKT = dataMKT.set_index('dates')['MKT']

# 获取前期计算好的SMB数据
dataSMB = pd.read_csv('factor/middle/东方证券_002_SMB.csv')
dataSMB.columns = ['dates', 'SMB']
dataSMB['dates'] = dataSMB['dates'].apply(lambda x: str(x))
dataSMB = dataSMB.set_index('dates')['SMB']

# 获取前期计算好的HML数据
dataHML = pd.read_csv('factor/middle/东方证券_002_HML.csv')
dataHML.columns = ['dates', 'HML']
dataHML['dates'] = dataHML['dates'].apply(lambda x: str(x))
dataHML = dataHML.set_index('dates')['HML']

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
        # 获取该证券在该月的行情序列
        returnSec = returnMonth.loc[secID, :].sort_values(by='dates').set_index('dates')
        dataTotal = pd.DataFrame({'Return': returnSec['DailyReturnSimple'],
                                  'MKT': dataMKT.loc[BOMs[month]: EOMs[month]],
                                  'SMB': dataSMB.loc[BOMs[month]: EOMs[month]],
                                  'HML': dataHML.loc[BOMs[month]: EOMs[month]]}).dropna()
        # 如果当月有数据可以参与运算
        if not dataTotal.empty:
            X, y = sm.add_constant(dataTotal[['MKT', 'SMB', 'HML']]), dataTotal['Return']
            fit = sm.OLS(y, X).fit()
            factorMonth[secID] = fit.resid.std()
        else:
            factorMonth[secID] = np.nan

    # 将本月因子数据存入总数据中
    factorResult[month] = pd.Series(factorMonth, name=month)

    # 显示当前进度
    number += 1; funcPerc = number / len(months)
    fun.processing_bar(funcPerc, funStart)

print('\n因子计算完成')

# 将所有期限的所有证券的因子值转变为数据框类型(pd.DataFrame)
factorResult = pd.DataFrame(factorResult)
factorResult.index = pd.Series(factorResult.index, name='secIDs')

# 输出计算结果
print(factorResult)

# 存储计算结果
factorResult.to_csv('factor/final/东方证券_002_IVFF.csv')
