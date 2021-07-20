# -*- encoding: utf-8 -*-
'''
Filename         :test.py
Description      :该模块用于计算单因子检验结果并进行存储
Time             :2021/06/25 11:47:58
Author           :量化投资1组
Version          :1.0
'''

import pandas as pd
import sys
sys.path.append('modules')
from factorTest import ICIRclass, groupclass


# 读取因子数据与期望收益率
factor = pd.read_csv('factor/final/东方证券_002_IVCAPM.csv').set_index('secIDs')
EReturn = pd.read_csv('factor/final/EReturn.csv').set_index('secIDs')
pathResult = 'result/东方证券_002_IVCAPM'
confidence = 0.95
groupNumber = 5

# 设定开始与结束日期
beginDate = '20050101'
endDate = '20210531'

# 进行ICIR法检验
ICIRClass = ICIRclass(factor, EReturn, beginDate, endDate, confidence)

ICIRClass.get_result()

ICIRClass.save_result(pathResult)

# 进行分组法检验
groupClass = groupclass(factor, groupNumber, beginDate, endDate)

groupClass.get_result(type='等权重')

groupClass.save_result(pathResult)
