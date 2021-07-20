# -*- encoding: utf-8 -*-
'''
Filename         :getStock.py
Description      :该模块用于获取股票数据
Time             :2021/06/25 11:47:58
Author           :量化投资1组
Version          :1.0
'''

import numpy as np
import pandas as pd
import scipy.io as scio
import time
from collections import OrderedDict
import basicFunction as fun
from concurrent.futures import ThreadPoolExecutor
from getDate import dateclass
from getStock import stockclass


class quoteclass:

    def __init__(self, dataPath):
        self.dataPath = dataPath
        # 读取必要数据
        self.stockList = np.load('{}/{}.npy'.format(dataPath, 'stockList'), allow_pickle=True)
        self.stockList = pd.Series(self.stockList, name='secIDs')

    def get_filename(self, field, date, type='5min'):
        # 获取文件名前缀
        if field == 'Open': prefix = 'StockOpen5M'
        elif field == 'High': prefix = 'StockHigh5M'
        elif field == 'Low': prefix = 'StockLow5M'
        elif field == 'Close': prefix = 'StockClose5M'
        elif field == 'Volume': prefix = 'StockVolume5M'
        elif field == 'Amount': prefix = 'StockAmount5M'
        # 获取文件名
        filename = '{}_{}'.format(prefix, date)
        return filename

    def read_data(self, filename, index=True):
        # 读取.mat文件，并转为DataFrame
        data = scio.loadmat('{}/{}.mat'.format(self.dataPath, filename))
        data = pd.DataFrame(data[filename])
        # 加载表头
        if index:
            data.columns = self.stockList
            data.index = pd.Series(data.index, name='order')
        return data

    def get_dataUniDate(self, secIDs, date, fields, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            print('\n数据提取开始')
            funStart, number = time.perf_counter(), 0
            # 存储最终数据
            dataResult = OrderedDict()
            # 获取所需读取的文件名
            filenames = []
            for field in fields:
                filename = self.get_filename(field, date)
                filenames.append(filename)
            # 多线程读取数据
            with ThreadPoolExecutor() as pool:
                results = pool.map(self.read_data, filenames)
                results = list(zip(filenames, results))
            # 整理所读取的数据
            dataSet = OrderedDict()
            for filename, data in results:
                dataSet[filename] = data
            # 提取对应日期与类型的数据
            for field in fields:
                filename = self.get_filename(field, date)
                dataTarget = dataSet[filename].loc[:, secIDs]
                dataResult[field] = dataTarget.stack()
                # 显示当前进度
                number += 1; funcPerc = number / (len(fields) + 1)
                fun.processing_bar(funcPerc, funStart)
            dataResult = pd.DataFrame(dataResult).reset_index().set_index('secIDs')
            # 提示运行完成
            fun.processing_bar(1, funStart)
            print('\n提取数据完成')
            return dataResult

        # 如果不需要显示运行进度
        else:
            # 存储最终数据
            dataResult = OrderedDict()
            # 获取所需读取的文件名
            filenames = []
            for field in fields:
                filename = self.get_filename(field, date)
                filenames.append(filename)
            # 多线程读取数据
            with ThreadPoolExecutor() as pool:
                results = pool.map(self.read_data, filenames)
                results = list(zip(filenames, results))
            # 整理所读取的数据
            dataSet = OrderedDict()
            for filename, data in results:
                dataSet[filename] = data
            # 提取对应日期与类型的数据
            for field in fields:
                filename = self.get_filename(field, date)
                dataTarget = dataSet[filename].loc[:, secIDs]
                dataResult[field] = dataTarget.stack()
            dataResult = pd.DataFrame(dataResult).reset_index().set_index('secIDs')
            return dataResult

    def get_dataMultiDates(self, secIDs, dates, fields, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            print('\n数据提取开始')
            funStart, number = time.perf_counter(), 0
            # 存储最终数据
            dataResult = pd.DataFrame(columns=['dates', 'order'].append(fields))
            # 获取所需读取的文件名
            filenames = []
            for date in dates:
                for field in fields:
                    filename = self.get_filename(field, date)
                    filenames.append(filename)
            # 多线程读取数据
            with ThreadPoolExecutor() as pool:
                results = pool.map(self.read_data, filenames)
                results = list(zip(filenames, results))
            # 整理所读取的数据
            dataSet = OrderedDict()
            for filename, data in results:
                dataSet[filename] = data
            # 提取对应日期与类型的数据
            for date in dates:
                dataDate = OrderedDict()
                for field in fields:
                    # 提取对应日期与类型的数据
                    filename = self.get_filename(field, date)
                    dataTarget = dataSet[filename].loc[:, secIDs]
                    dataDate[field] = dataTarget.stack()
                dataDate = pd.DataFrame(dataDate).reset_index().set_index('secIDs')
                dataDate['dates'] = date
                dataResult = dataResult.append(dataDate)
                # 显示当前进度
                number += 1; funcPerc = number / len(dates)
                fun.processing_bar(funcPerc, funStart)
            # 修改列顺序
            dataDates = dataResult['dates']
            dataResult = dataResult.drop(columns=['dates'])
            dataResult.insert(0, 'dates', dataDates)
            # 提示运行完成
            print('\n提取数据完成')
            return dataResult

        # 如果不需要显示运行进度
        else:
            # 存储最终数据
            dataResult = pd.DataFrame(columns=['dates', 'order'].append(fields))
            # 获取所需读取的文件名
            filenames = []
            for date in dates:
                for field in fields:
                    filename = self.get_filename(field, date)
                    filenames.append(filename)
            # 多线程读取数据
            with ThreadPoolExecutor() as pool:
                results = pool.map(self.read_data, filenames)
                results = list(zip(filenames, results))
            # 整理所读取的数据
            dataSet = OrderedDict()
            for filename, data in results:
                dataSet[filename] = data
            # 提取对应日期与类型的数据
            for date in dates:
                dataDate = OrderedDict()
                for field in fields:
                    # 提取对应日期与类型的数据
                    filename = self.get_filename(field, date)
                    dataTarget = dataSet[filename].loc[:, secIDs]
                    dataDate[field] = dataTarget.stack()
                dataDate = pd.DataFrame(dataDate).reset_index().set_index('secIDs')
                dataDate['dates'] = date
                dataResult = dataResult.append(dataDate)
            # 修改列顺序
            dataDates = dataResult['dates']
            dataResult = dataResult.drop(columns=['dates'])
            dataResult.insert(0, 'dates', dataDates)
            return dataResult


if __name__ == '__main__':
    
    beginDate = '20050101'
    endDate = '20210531'

    dateClass = dateclass('data/date')
    stockClass = stockclass('data/stock/1day', preReadFields=[])

    dates = dateClass.get_dates(beginDate, endDate)
    stockPools = stockClass.get_stockPools(dates)

    quoteClass = quoteclass('data/stock/5min')

    data = quoteClass.get_dataUniDate(secIDs=stockPools[dates[0]], date=dates[0], fields=['Close', 'Open', 'Volume'])

    print(data)

    data = quoteClass.get_dataMultiDates(secIDs=stockPools[dates[0]], dates=dates, fields=['Close', 'Open', 'Volume'])
    print(data)


'''
    def read_MultiData(self, filename):
        # 如果需要显示运行进度
        if showProcess:
            print('\n数据预读取提取开始')
            funStart, number = time.perf_counter(), 0
            preRead = OrderedDict()
            with ThreadPoolExecutor() as pool:
                dataSet = pool.map(self.read_data, self.preReadFiles)
                dataSet = list(zip(self.preReadFiles, dataSet))
            for filename, content in dataSet:
                preRead[filename] = content
                # 显示当前进度
                number += 1; funcPerc = number / (len(self.preReadDates) * len(self.preReadFields))
                fun.processing_bar(funcPerc, funStart)
            fun.processing_bar(1, funStart)
            print('\n数据预读取提取完成')
            return preRead
        # 如果不需要显示运行进度
        else:
            preRead = OrderedDict()
            with ThreadPoolExecutor() as pool:
                dataSet = pool.map(self.read_data, self.preReadFiles)
                dataSet = list(zip(self.preReadFiles, dataSet))
            for filename, content in dataSet:
                preRead[filename] = content
            return preRead

'''