# -*- encoding: utf-8 -*-
'''
Filename         :东方证券_002_IVCAPM.py
Description      :该模块用于计算因子IVCAPM
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import numpy as np
import pandas as pd
import time, os, sys
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor
sys.path.append('modules')
from getStock import stockclass
from getDate import dateclass
from getQuote import quoteclass
import basicFunction as fun

# 设定开始与结束日期
beginDate = '20050101'
endDate = '20071231'

# 创建日期数据获取对象
dateClass = dateclass()
dates = dateClass.get_dates(beginDate, endDate, showProcess=False)

# 创建股票日频数据获取对象
stockClass = stockclass('data/stock/1day', preRead=['MVFloat', 'PB'], showProcess=False)
stockPools = stockClass.get_stockPools(dates, showProcess=False)

# 创建股票分钟频数据获取对象
quoteClass = quoteclass('data/stock/5min')

# 设定聪明钱判定阈值
smartThreshold = 0.2

funStart = 0


# 定义计算主体
def get_results(thisDate):
    print(thisDate)

    # 获取当日证券池
    stockPool = stockPools[thisDate]

    # 获取量价数据
    dataOriginal = quoteClass.get_data(secIDs=stockPool, dates=[thisDate], fields=['Volume', 'Open', 'Close'], showProcess=False)
    # 计算聪明钱分钟指标
    factorOrder = pd.DataFrame(columns=stockPool)
    for order in range(0, 48):
        RetOrder = dataOriginal[dataOriginal['order'] == order]['Close'] / dataOriginal[dataOriginal['order'] == order]['Open'] - 1
        VolOrder = dataOriginal[dataOriginal['order'] == order]['Volume']
        factorOrder.loc[order, :] = np.abs(RetOrder) / np.sqrt(VolOrder)

    # 计算聪明钱每日指标
    factorDate = OrderedDict()
    for secID in stockPool:
        # 取得该证券当日的数据，并进行整理
        factorSec = factorOrder[secID].sort_values(ascending=False)
        if not factorSec.empty:
            # 获取聪明钱所在K线
            factorCum = factorSec.cumsum()
            for index in factorCum.index.tolist():
                if factorCum.loc[index] >= (factorSec.sum() * smartThreshold):
                    SmartIndex = factorSec[: index + 1].index.tolist()
                    break
            # 计算当日所有交易的加权平均成交价
            CloseAll = dataOriginal[dataOriginal['dates'] == thisDate]['Close']
            VolumeAll = dataOriginal[dataOriginal['dates'] == thisDate]['Volume']
            VWAPAll = (CloseAll * (VolumeAll / VolumeAll.sum())).sum()
            # 计算当日聪明钱交易的加权平均成交价
            CloseSmart, VolumeSmart = CloseAll[SmartIndex], VolumeAll[SmartIndex]
            VWAPSmart = (CloseSmart * (VolumeSmart / VolumeSmart.sum())).sum()
            # 计算该证券的当日聪明钱因子
            factorDate[secID] = VWAPSmart / VWAPAll
        else:
            factorDate[secID] = np.nan
    factorDate = pd.Series(factorDate)

    # 显示当前进度
    index = dates[dates == thisDate].index.tolist()[0]
    funcPerc = len(dates[: index]) / len(dates)
    fun.processing_bar(funcPerc, funStart)

    return factorDate


if __name__ == '__main__':
    # 计算程序运行时间
    print('\n因子计算开始')
    funStart = time.perf_counter()

    # 设置数据框存储因子
    factorResult = OrderedDict()

    # 使用多进程并发计算
    with ProcessPoolExecutor() as pool:
        results = pool.map(get_results, dates)
        results = list(zip(dates, results))

    # 整理计算结果
    for date, result in results:
        factorResult[date] = result

    print('\n因子计算完成')

    # 将所有期限的所有证券的因子值转变为数据框类型(pd.DataFrame)
    factorResult = pd.DataFrame(factorResult)
    factorResult.index = pd.Series(factorResult.index, name='secIDs')

    # 输出计算结果
    print(factorResult)

    # 存储计算结果
    pathResult = 'factor/方正证券_003'
    if not os.path.exists(pathResult):
        os.makedirs(pathResult)
    factorResult.to_csv('{}/方正证券_003_SmartMoney.csv'.format(pathResult))
