# -*- encoding: utf-8 -*-
'''
Filename         :regression.py
Description      :该模块用于进行单因子回归法检验
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
import statsmodels.api as sm

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

params, tvalues, pvalues = OrderedDict(), OrderedDict(), OrderedDict()

for month in months:
    # 输出当前交易日
    BOM = BOMs[month]
    print('\n当前交易日为：{}'.format(BOM))

    # 计算主程序运行时间
    print('\n回归计算开始')
    funStart, number = time.perf_counter(), 0

    # 获取本月因子数据与期望收益率数据
    dataMonth = pd.DataFrame({'factor': factor[BOM], 'EReturn': EReturn[BOM]}).dropna()

    # 如果本月有数据可用于回归
    if not dataMonth.empty:
        # 在截面上进行稳健回归
        X, y = sm.add_constant(dataMonth['factor']), dataMonth['EReturn']
        fit = sm.RLM(y, X).fit()
        params[month], tvalues[month], pvalues[month] = fit.params.loc['factor'], fit.tvalues.loc['factor'], fit.pvalues.loc['factor']
    # 如果本月无数据可用于回归
    else:
        params[month], tvalues[month], pvalues[month] = np.nan, np.nan, np.nan

    # 显示当前进度
    fun.processing_bar(1, funStart)
    print('\n回归计算完成')

params, tvalues, pvalues = pd.Series(params), pd.Series(tvalues), pd.Series(pvalues)
result = pd.DataFrame({'params': params, 'tvalues': tvalues, 'pvalues': pvalues})

print(result)
result.to_csv('result/mom/regression.csv')
