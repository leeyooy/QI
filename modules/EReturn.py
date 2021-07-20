# -*- encoding: utf-8 -*-
'''
Filename         :return.py
Description      :该模块用于计算月期望收益率
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
stockClass = stockclass('data/stock/1day', preRead=['CloseR', 'OpenR'])
dateClass = dateclass('data/date')

# 获取月份数据、月初和月末日期数据
dates = dateClass.get_dates(beginDate, endDate)
months = dateClass.get_months(beginDate, endDate)
BOMs = dateClass.get_BOMs(beginDate, endDate)
EOMs = dateClass.get_EOMs(beginDate, endDate)

# 获取证券列表
stockList = np.load('data/stock/stockList.npy', allow_pickle=True)
stockList = pd.Series(stockList, name='secIDs')

# 获取收盘价数据
dataCloseR = stockClass.read_data('stockClose', factor=True)
dataStop = stockClass.read_data('stockStop', factor=False)

# 设置有序字典存储因子
factorResult = OrderedDict()

# 计算主程序运行时间
print('\n期望收益率计算开始')
funStart, number = time.perf_counter(), 0

for month in months:
    # 获取本月的收盘价与开盘价数据
    DUMs = dateClass.get_DUMs(month, showProcess=False)
    data = stockClass.get_data(secIDs=stockList, dates=DUMs, fields=['CloseR', 'OpenR'], showProcess=False)
    
    factorMonth = OrderedDict()
    for secID in stockList:
        # 提取该证券的本月数据
        dataSec = data.loc[secID, :].sort_values(by='dates').dropna()
        if not dataSec.empty:
            factorMonth[secID] = dataSec['CloseR'].iloc[-1] / dataSec['OpenR'].iloc[0] - 1
        else:
            factorMonth[secID] = np.nan

    factorResult[month] = pd.Series(factorMonth)

    # 显示当前进度
    number += 1
    funcPerc = number / len(months)
    fun.processing_bar(funcPerc, funStart)

print('\n期望收益率计算完成')

# 将所有期限的所有证券的月期望收益率转变为数据框类型(pd.DataFrame)
factorResult = pd.DataFrame(factorResult)

# 输出计算结果
print(factorResult)

# 存储计算结果
factorResult.to_csv('factor/final/EReturn.csv')
