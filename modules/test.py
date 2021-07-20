# -*- encoding: utf-8 -*-
'''
Filename         :test.py
Description      :该模块用于测试已有模块的功能是否正常
Time             :2021/06/25 11:47:58
Author           :量化投资1组
Version          :1.0
'''

import pandas as pd
from getStock import stockclass
from getIndex import indexclass
from getDate import dateclass
from factorTest import ICIRclass, regressionclass, groupclass

'''getDays 模块运行'''
beginDate = '20060101'
endDate = '20061231'
targetMonth = '202005'
currentDate = '20061229'
timeSpan = 20

dateClass = dateclass('data/date')
dates = dateClass.get_dates(beginDate, endDate)
months = dateClass.get_months(beginDate, endDate)
BOMs = dateClass.get_BOMs(beginDate, endDate)
EOMs = dateClass.get_EOMs(beginDate, endDate)
DUMs = dateClass.get_DUMs(targetMonth)
beforeDate = dateClass.get_beforeDate(currentDate, timeSpan)

'''getStock 模块运行'''
fileName = 'stockClose.npy'

stockClass = stockclass('data/stock')
fileContentStock = stockClass.read_data(fileName)
stockPools = stockClass.get_stockPools(BOMs)
dataStock = stockClass.get_data(secIDs=stockPools[dates.iloc[0]], dates=dates.iloc[0:100], fields=['CloseR', 'Volume'])
names = stockClass.get_names(stockPools[dates.iloc[0]])

'''getIndex 模块运行'''
fileName = 'indexClose.npy'
indexIDs = ['000001.SH']

indexClass = indexclass('data/index')
fileContentIndex = indexClass.read_data(fileName)
dataIndex = indexClass.get_data(indexIDs=indexIDs, dates=dates.iloc[0:100], fields=['Close', 'Volume'])
infos = indexClass.get_infos(indexIDs)

'''factorTest 模块运行'''
factor = pd.read_csv('factor/mom20.csv').set_index('Unnamed: 0')
EReturn = pd.read_csv('factor/EReturn.csv').set_index('Unnamed: 0')
groupNumber = 5

ICIRClass = ICIRclass(factor, EReturn, BOMs)
IC, IR = ICIRClass.get_result()

regressionClass = regressionclass(factor, EReturn, BOMs)
regressionResult = regressionClass.get_result()

groupClass = groupclass(factor, EReturn, BOMs, groupNumber)
groupResult = groupClass.get_result()


print('\n')


'''getDate 模块测试'''
# dateclass.get_dates()函数测试
if dates.iloc[0] == '20060104' and dates.iloc[-1] == '20061229' and len(dates) == 241:
    print('{}函数正确'.format('dateclass.get_date()'))
else:
    print('{}函数错误'.format('dateclass.get_date()'))
    print(dates)
# dateclass.get_months()函数测试
if months.iloc[0] == '200601' and months.iloc[-1] == '200612' and len(months) == 12:
    print('{}函数正确'.format('dateclass.get_months()'))
else:
    print('{}函数错误'.format('dateclass.get_months()'))
    print(months)
# dateclass.get_BOMs()函数测试
if BOMs.iloc[0] == '20060104' and BOMs.iloc[-1] == '20061201' and len(BOMs) == 12:
    print('{}函数正确'.format('dateclass.get_BOMs()'))
else:
    print('{}函数错误'.format('dateclass.get_BOMs()'))
    print(BOMs)
# dateclass.get_EOMs()函数测试
if EOMs.iloc[0] == '20060125' and EOMs.iloc[-1] == '20061229' and len(EOMs) == 12:
    print('{}函数正确'.format('dateclass.get_EOMs()'))
else:
    print('{}函数错误'.format('daysClass.get_EOMs()'))
    print(EOMs)
# dateclass.get_DUMs()函数测试
if DUMs.iloc[0] == '20200506' and DUMs.iloc[-1] == '20200529' and len(DUMs) == 18:
    print('{}函数正确'.format('dateclass.get_DUMs()'))
else:
    print('{}函数错误'.format('dateclass.get_DUMs()'))
    print(DUMs)
# dateclass.get_beforeDate()函数测试
if beforeDate == '20061201':
    print('{}函数正确'.format('dateclass.get_beforeDate()'))
else:
    print('{}函数错误'.format('dateclass.get_beforeDate()'))
    print(beforeDate)


'''getStock 模块测试'''
# stockclass.read_data()函数测试
if fileContentStock.loc['20050104', '000005.SZ'] == 2.13 and fileContentStock.loc['20210531', '603511.SH'] == 30.23 \
   and len(fileContentStock.index) == 3986 and len(fileContentStock.columns) == 4462:
    print('{}函数正确'.format('stockclass.read_data()'))
else:
    print('{}函数错误'.format('stockclass.read_data()'))
    print(fileContentStock)
# stockclass.get_stockPools()函数测试
if stockPools[BOMs.iloc[0]].iloc[0] == '600601.SH' and stockPools[BOMs.iloc[0]].iloc[-1] == '002050.SZ' \
   and stockPools[BOMs.iloc[-1]].iloc[0] == '600601.SH' and stockPools[BOMs.iloc[-1]].iloc[-1] == '002066.SZ' \
   and len(stockPools[BOMs.iloc[0]]) == 1112 and len(stockPools[BOMs.iloc[-1]]) == 1154 and len(stockPools) == 12:
    print('{}函数正确'.format('stockclass.get_stockPools()'))
else:
    print('{}函数错误'.format('stockclass.get_stockPools()'))
    print(stockPools)
# stockclass.get_data()函数测试
if int(dataStock.loc['600601.SH', 'CloseR'].iloc[0]) == 10549 \
   and int(dataStock.loc['002050.SZ', 'Volume'].iloc[-1]) == 19579 \
   and len(dataStock.index) == 111200 and len(dataStock.columns) == 3:
    print('{}函数正确'.format('stockclass.get_data()'))
else:
    print('{}函数错误'.format('stockclass.get_data()'))
    print(dataStock)
# stockclass.get_names()函数测试
if names.iloc[0] == 'ST方科' and names.iloc[-1] == '三花智控' and len(names) == 1112:
    print('{}函数正确'.format('stockclass.get_names()'))
else:
    print('{}函数错误'.format('stockclass.get_names()'))
    print(names)

'''getIndex 模块测试'''
# indexclass.read_data()函数测试
if fileContentIndex.loc['20050104', '000001.SH'] == 1242.7740 and fileContentIndex.loc['20210531', '399108.SZ'] == 1159.7966 \
   and len(fileContentIndex.index) == 3986 and len(fileContentIndex.columns) == 19:
    print('{}函数正确'.format('indexclass.read_data()'))
else:
    print('{}函数错误'.format('indexclass.read_data()'))
    print(fileContentIndex)
# indexclass.get_data()函数测试
if int(dataIndex.loc['000001.SH', 'Close'].iloc[0]) == 1180 \
   and int(dataIndex.loc['000001.SH', 'Volume'].iloc[-1]) == 54576873 \
   and len(dataIndex.index) == 100 and len(dataIndex.columns) == 3:
    print('{}函数正确'.format('indexclass.get_data()'))
else:
    print('{}函数错误'.format('indexclass.get_data()'))
    print(dataIndex)
# indexclass.get_infos()函数测试
if infos.loc['000001.SH', 'name'] == '上证指数' and infos.loc['000001.SH', 'listDate'] == 19910715:
    print('{}函数正确'.format('indexclass.get_infos()'))
else:
    print('{}函数错误'.format('indexclass.get_infos()'))
    print(infos)

'''factorTest 模块测试'''
# ICIRclass.get_result()函数测试
if round(IC.iloc[0], 4) == 0.1952 and round(IC.iloc[-1], 4) == 0.1423 and round(IR, 4) == -0.3417:
    print('{}函数正确'.format('ICIRclass.get_result()'))
else:
    print('{}函数错误'.format('ICIRclass.get_result()'))
    print(IC)
    print(IR)
# regressionclass.get_result()函数测试
if round(regressionResult.loc['200601', 'params'], 4) == 0.3068 \
   and round(regressionResult.loc['200612', 'tvalues'], 4) == 7.3301 \
   and len(regressionResult.index) == 12 and len(regressionResult.columns) == 3:
    print('{}函数正确'.format('regressionclass.get_result()'))
else:
    print('{}函数错误'.format('regressionclass.get_result()'))
    print(regressionResult)
# groupclass.get_result()函数测试
if round(groupResult.loc['200601', 1], 4) == 0.0866 \
   and round(groupResult.loc['200612', groupNumber], 4) == 0.0336 \
   and len(groupResult.index) == 12 and len(groupResult.columns) == groupNumber:
    print('{}函数正确'.format('groupclass.get_result()'))
else:
    print('{}函数错误'.format('groupclass.get_result()'))
    print(groupResult)
