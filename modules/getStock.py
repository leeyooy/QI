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
import time
from collections import OrderedDict
import basicFunction as fun


class stockclass:

    def __init__(self, dataPath, preRead, showProcess=True):
        self.dataPath = dataPath
        self.preRead = preRead
        # 读取必要数据
        self.stockTradeDate = np.load('data/stock/stockTradeDate.npy', allow_pickle=True)
        self.stockTradeDate = pd.Series(self.stockTradeDate, name='dates').apply(lambda x: str(x))
        self.stockList = np.load('data/stock/stockList.npy', allow_pickle=True)
        self.stockList = pd.Series(self.stockList, name='secIDs')
        # 预读取数据
        self.preReadData = self.get_preRead(showProcess=showProcess)

    def get_readStyle(self, field):
        if field == 'Open': return 'stockOpen', False
        elif field == 'OpenR': return 'stockOpen', True
        elif field == 'High': return 'stockHigh', False
        elif field == 'HighR': return 'stockHigh', True
        elif field == 'Low': return 'stockLow', False
        elif field == 'LowR': return 'stockLow', True
        elif field == 'Close': return 'stockClose', False
        elif field == 'CloseR': return 'stockClose', True
        elif field == 'Amount': return 'stockAmount', False
        elif field == 'AmountR': return 'stockAmount', True
        elif field == 'Volume': return 'stockVolume', False
        elif field == 'VolumeR': return 'stockVolume', True
        elif field == 'DailyReturnLog': return 'stockDailyReturnLog', False
        elif field == 'DailyReturnSimple': return 'stockDailyReturnSimple', False
        elif field == 'tCap': return 'tCap', False
        elif field == 'IndZX': return 'stockZx', False
        elif field == 'isST': return 'stockSt', False
        elif field == 'isStop': return 'stockStop', False
        elif field == 'tradeDays': return 'stockTradeDayCount', False
        elif field == 'MVTotal': return 'tushareMVTotal', False
        elif field == 'MVFloat': return 'tushareMVFloat', False
        elif field == 'ShareTotal': return 'tushareShareTotal', False
        elif field == 'ShareFloat': return 'tushareShareFloat', False
        elif field == 'ShareFree': return 'tushareShareFree', False
        elif field == 'TurnoverRate': return 'tushareTurnoverRate', False
        elif field == 'TurnoverRateFree': return 'tushareTurnoverRateFree', False
        elif field == 'VolumeRatio': return 'tushareVolumeRatio', False
        elif field == 'PB': return 'tusharePB', False
        elif field == 'PE': return 'tusharePE', False
        elif field == 'PETTM': return 'tusharePETTM', False
        elif field == 'PS': return 'tusharePS', False
        elif field == 'PSTTM': return 'tusharePSTTM', False
        elif field == 'DividRatio': return 'tushareDividRatio', False
        elif field == 'DividRatioTTM': return 'tushareDividRatioTTM', False

    def read_data(self, filename, index=True, factor=False):
        """数据读取函数，从data文件夹中读取数据

        Args:
            filename (str): 要求读取的文件名称。带后缀，不需要指定文件夹
            index (bool, optional): 读取后是否加载表头。默认为True
            factor (bool, optional): 读取后是否进行复权。默认为False

        Returns:
            pd.DataFrame: 返回读取的结果，行按证券排序，列按日期排序
        """
        # 读取.npy文件，并转为dataframe
        data = np.load('{}/{}.npy'.format(self.dataPath, filename))
        data = pd.DataFrame(data)
        # 价格复权
        if factor:
            factor = np.load('{}/{}.npy'.format(self.dataPath, 'stockFactor'))
            data = data * factor
        # 加载表头
        if index:
            data.columns = self.stockList
            data.index = self.stockTradeDate
        return data

    def get_preRead(self, showProcess):
        # 如果需要显示运行进度
        if showProcess:
            print('\n数据预读取提取开始')
            funStart, number = time.perf_counter(), 0
            preRead = OrderedDict()
            for field in self.preRead:
                filename, isfactor = self.get_readStyle(field)
                preRead[field] = self.read_data(filename=filename, factor=isfactor)
                # 显示当前进度
                number += 1; funcPerc = number / len(self.preRead)
                fun.processing_bar(funcPerc, funStart)
            fun.processing_bar(1, funStart)
            print('\n数据预读取提取完成')
            return preRead

        # 如果不需要显示运行进度
        else:
            preRead = OrderedDict()
            for field in self.preRead:
                filename, isfactor = self.get_readStyle(field)
                preRead[field] = self.read_data(filename=filename, factor=isfactor)
            return preRead

    def get_stockPools(self, dates, delST=True, delStop=True, delNew=True, minDate=60, showProcess=True):
        """证券池函数，获取所有指定日期的，经过去ST、去停牌、去次新股后的证券池

        Args:
            dates (pd.Series): 获取证券池的日期序列
            delST (bool, optional): 是否需要删除ST股票。默认为True。
            delStop (bool, optional): 是否需要删除停牌股票。默认为True
            delNew (bool, optional): 是否需要删除次新股。默认为True
            minDate (int, optional): 次新股的定义，上市多少个交易日内定义为次新股。默认为60

        Returns:
            OrderedDict(): 返回一个有顺序的字典对象，键为日期(str)，值为对应证券池(pd.Series)
        """
        # 记录数据情况
        self.delST = delST
        self.delStop = delStop
        self.delNew = delNew
        self.minDate = minDate
        # 如果需要显示运行进度
        if showProcess:
            print('\n股票池筛选开始')
            funStart, number = time.perf_counter(), 0
            stockPools = OrderedDict()
            # 读取目标期限的ST、停牌、上市时间情况
            dataST = self.read_data('stockSt')
            dataStop = self.read_data('stockStop')
            dataTrade = self.read_data('stockTradeDayCount')
            # 遍历目标期限中的每一个交易日
            for date in dates:
                # 获取当日的ST、停牌、上市时间情况
                dataSTNow = dataST.loc[date, :]
                dataStopNow = dataStop.loc[date, :]
                dataTradeNow = dataTrade.loc[date, :]
                # 筛选出上市时间超过minDate、非ST、非停牌的股票
                secIDs = self.stockList
                if delNew: secIDs = dataTradeNow[secIDs][dataTradeNow > minDate].index
                if delST: secIDs = dataSTNow[secIDs][dataSTNow != 1.0].index
                if delStop: secIDs = dataStopNow[secIDs][dataStopNow != 1.0].index
                # 获取满足要求的股票代码，并加入筛选结果中
                stockPools[date] = pd.Series(secIDs.tolist())
                number += 1; funcPerc = number / len(dates)
                fun.processing_bar(funcPerc, funStart)
            print('\n股票池筛选完成')
            return stockPools

        # 如果不需要显示运行进度
        else:
            stockPools = OrderedDict()
            # 读取目标期限的ST、停牌、上市时间情况
            dataST = self.read_data('stockSt')
            dataStop = self.read_data('stockStop')
            dataTrade = self.read_data('stockTradeDayCount')
            # 遍历目标期限中的每一个交易日
            for date in dates:
                # 获取当日的ST、停牌、上市时间情况
                dataSTNow = dataST.loc[date, :]
                dataStopNow = dataStop.loc[date, :]
                dataTradeNow = dataTrade.loc[date, :]
                # 筛选出上市时间超过minDate、非ST、非停牌的股票
                secIDs = self.stockList
                if delNew: secIDs = dataTradeNow[secIDs][dataTradeNow > minDate].index
                if delST: secIDs = dataSTNow[secIDs][dataSTNow != 1.0].index
                if delStop: secIDs = dataStopNow[secIDs][dataStopNow != 1.0].index
                # 获取满足要求的股票代码，并加入筛选结果中
                stockPools[date] = pd.Series(secIDs.tolist())
            return stockPools

    def get_data(self, secIDs, dates, fields, showProcess=True):
        """数据查找函数，查找目标证券在一段时间内的数据

        Args:
            secIDs (pd.Series): 希望查询的证券代码
            dates (pd.Series): 希望查询的日期序列
            attributes (list): 希望查询的信息，目前支持查询的信息代码见帮助文档

        Returns:
            pd.DataFrame: 返回一个数据框
        """
        # 如果需要显示运行进度
        if showProcess:
            print('\n数据提取开始')
            funStart, number = time.perf_counter(), 0
            # 提取数据文件
            dataResult = OrderedDict()
            for field in fields:
                # 提取目标数据
                dataTarget = self.preReadData[field].loc[dates, secIDs]
                dataResult[field] = dataTarget.stack()
                # 显示当前进度
                number += 1; funcPerc = number / (len(fields) + 1)
                fun.processing_bar(funcPerc, funStart)
            # 将已获取的数据转为pd.DataFrame类型
            dataResult = pd.DataFrame(dataResult).reset_index().set_index('secIDs')
            # 提示运行完成
            fun.processing_bar(1, funStart)
            print('\n提取数据完成')
            return dataResult

        # 如果不需要显示运行进度
        else:
            # 提取数据文件
            dataResult = OrderedDict()
            for field in fields:
                # 提取目标数据
                dataTarget = self.preReadData[field].loc[dates, secIDs]
                dataResult[field] = dataTarget.stack()
            # 将已获取的数据转为pd.DataFrame类型
            dataResult = pd.DataFrame(dataResult).reset_index().set_index('secIDs')
            return dataResult

    def get_names(self, secIDs, showProcess=True):
        """股票简称获取函数

        Args:
            secIDs (pd.Series): 希望查询的证券代码

        Returns:
            pd.Series: 返回查询的结果，键为证券代码，值为对应的证券简称
        """
        # 如果需要显示运行进度
        if showProcess:
            print('\n股票简称获取开始')
            funStart, number = time.perf_counter(), 0
            secNames = {}
            # 读取stockName数据
            stockName = np.load('data/stock/stockName.npy', allow_pickle=True)
            stockName = pd.Series(stockName.flatten())
            # 根据输入的股票代码获取其所在位置，进而获取股票名称
            for secID in secIDs:
                index = self.stockList[self.stockList == secID].index
                secNames[secID] = stockName.loc[index].iloc[0][0]
                # 显示当前进度
                number += 1
                funcPerc = number / len(secIDs)
                fun.processing_bar(funcPerc, funStart)
            secNames = pd.Series(secNames, name='secNames')
            print('\n股票简称获取完成')
            return secNames

        # 如果不需要显示运行进度
        else:
            secNames = {}
            # 读取stockName数据
            stockName = np.load('data/stock/stockName.npy', allow_pickle=True)
            stockName = pd.Series(stockName.flatten())
            # 根据输入的股票代码获取其所在位置，进而获取股票名称
            for secID in secIDs:
                index = self.stockList[self.stockList == secID].index
                secNames[secID] = stockName.loc[index].iloc[0][0]
            secNames = pd.Series(secNames, name='secNames')
            return secNames
