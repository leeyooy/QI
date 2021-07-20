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
stockClass = stockclass('data/stock', preRead=['CloseR', 'MVFloat', 'DailyReturnSimple'])
dateClass = dateclass('data/date')

# 获取月份数据和月初日期数据
dates = dateClass.get_dates(beginDate, endDate)
BOMs = dateClass.get_BOMs(beginDate, endDate)
EOMs = dateClass.get_EOMs(beginDate, endDate)

# 获取证券池
stockPools = stockClass.get_stockPools(EOMs, minDate=60)

# 设置有序字典存储因子
factorResult = OrderedDict()

# 计算程序运行时间
print('\n因子计算开始')
funStart, number = time.perf_counter(), 0

for date in dates:

    lastMonth = dateClass.get_beforeMonth(date[: -2], 1, showProcess=False)

    if lastMonth != 'out of range' or date in EOMs.tolist():
        # 如果碰到调仓日，则重新计算权重
        if date in EOMs.tolist():
            # 获取数据
            stockPool, BOM, EOM = stockPools[date], BOMs[date[: -2]], EOMs[date[: -2]]
            dataThisMonth = stockClass.get_data(secIDs=stockPool, dates=[BOM, EOM], fields=['CloseR', 'MVFloat'], showProcess=False)
            # 计算收益
            dataCloseRBOM = dataThisMonth[dataThisMonth['dates'] == BOM]['CloseR']
            dataCloseREOM = dataThisMonth[dataThisMonth['dates'] == EOM]['CloseR']
            dataMVFloat = dataThisMonth[dataThisMonth['dates'] == EOM]
            dataReturn = np.log(dataCloseREOM / dataCloseRBOM)
            # 排序分组
            indexReturnMin = dataReturn.sort_values(ascending=True).iloc[: int(len(dataReturn) / 3)].index
            indexReturnMax = dataReturn.sort_values(ascending=False).iloc[: int(len(dataReturn) / 3)].index
            # 计算权重
            dataMVFloatMin = dataMVFloat.loc[indexReturnMin, 'MVFloat']
            dataMVFloatMax = dataMVFloat.loc[indexReturnMax, 'MVFloat']
            weightsMin = dataMVFloatMin / dataMVFloatMin.sum()
            weightsMax = dataMVFloatMax / dataMVFloatMax.sum()

        # 获取数据
        dataOriginalMin = stockClass.get_data(secIDs=weightsMin.index, dates=[date], fields=['DailyReturnSimple'], showProcess=False)
        dataOriginalMax = stockClass.get_data(secIDs=weightsMax.index, dates=[date], fields=['DailyReturnSimple'], showProcess=False)
        # 计算因子数值
        dailyReturnMin = dataOriginalMin['DailyReturnSimple']
        dailyReturnMax = dataOriginalMax['DailyReturnSimple']
        factorResult[date] = (dailyReturnMin * weightsMin).sum() - (dailyReturnMax * weightsMax).sum()
        # 显示当前进度
        number += 1; funcPerc = number / len(dates)
        fun.processing_bar(funcPerc, funStart)
    else:
        factorResult[date] = np.nan
        # 显示当前进度
        number += 1; funcPerc = number / len(dates)
        fun.processing_bar(funcPerc, funStart)

print('\n因子计算完成')

# 将所有期限的所有证券的因子值转变为数据框类型(pd.DataFrame)
factorResult = pd.Series(factorResult)

# 输出计算结果
print(factorResult)

# 存储计算结果
factorResult.to_csv('factor/middle/东方证券_002_MOM.csv')
