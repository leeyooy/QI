# -*- encoding: utf-8 -*-
'''
Filename         :groups.py
Description      :该模块用于进行单因子分层法检验
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import numpy as np
import pandas as pd
import time
from collections import OrderedDict
from getData import dataClass
from getDays import daysClass
import basicFunction as fun

# 设定开始与结束日期
beginDate = '20050101'
endDate = '20210531'

# 创建日期和数据获取对象
daysclass = daysClass('days')
dataclass = dataClass('data')

# 获取交易日历、筛选后的证券池
months = daysclass.get_months(beginDate, endDate)
BOMs = daysclass.get_BOMs(beginDate, endDate)
stockPools = dataclass.get_stockPools(dates=BOMs, delST=True, delStop=True, delNew=True, minDate=60)

# 读取因子与期望收益率数据
factor = pd.read_csv('factor/mom20.csv').set_index('Unnamed: 0')
EReturn = pd.read_csv('factor/EReturn.csv').set_index('Unnamed: 0')

groupNumber = 5
groupResult = pd.DataFrame(columns=range(1, groupNumber + 1))

for month in months:
    # 输出当前交易日
    BOM = BOMs[month]
    print('\n当前交易日为：{}'.format(BOM))

    # 计算主程序运行时间
    print('\n分层计算开始')
    funStart, number = time.perf_counter(), 0

    # 获取本月因子数据与期望收益率数据
    dataMonth = pd.DataFrame({'factor': factor[BOM], 'EReturn': EReturn[BOM]}).dropna()

    # 如果本月有数据可用于分层
    if not dataMonth.empty:
        secIDOrdered = dataMonth['factor'].sort_values(ascending=False).index
        # 分配各组所含证券数量
        groupLength = OrderedDict()
        for groupOrder in range(1, groupNumber + 1):
            if groupOrder <= len(secIDOrdered) % groupNumber:
                groupLength[groupOrder] = int(len(secIDOrdered) / groupNumber) + 1
            else:
                groupLength[groupOrder] = int(len(secIDOrdered) / groupNumber)
        groupLength = pd.Series(groupLength)
        # 分配各组所含证券代码
        secIDGrouped = OrderedDict()
        for groupOrder in range(1, groupNumber + 1):
            if groupOrder == 1:
                start = 0
                end = groupLength.loc[groupOrder]
            else:
                start = groupLength.loc[1: groupOrder - 1].sum()
                end = start + groupLength[groupOrder]
            secIDGrouped[groupOrder] = secIDOrdered[start: end]
        # 计算各组投资组合期望收益率(等权重)
        groupReturn = OrderedDict()
        for groupOrder in range(1, groupNumber + 1):
            groupReturn[groupOrder] = dataMonth['EReturn'].loc[secIDGrouped[groupOrder]].mean()
    else:
        groupReturn = OrderedDict()
        for groupOrder in range(1, groupNumber + 1):
            groupReturn[groupOrder] = np.nan
    groupResult = groupResult.append(pd.Series(groupReturn, name=month))
    fun.processing_bar(1, funStart)
    print('\n分层计算完成')

print(groupResult)
groupResult.to_csv('result/mom/groups.csv')
