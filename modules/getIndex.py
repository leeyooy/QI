# -*- encoding: utf-8 -*-
'''
Filename         :getIndex.py
Description      :该模块用于获取指数数据
Time             :2021/06/25 11:47:58
Author           :量化投资1组
Version          :1.0
'''
import numpy as np
import pandas as pd
import time
from collections import OrderedDict
import basicFunction as fun


class indexclass:

    def __init__(self, dataPath, preReadFields, showProcess=True):
        self.dataPath = dataPath
        self.preReadFields = preReadFields
        # 读取表头数据
        self.indexTradeDate = np.load('{}/{}'.format(self.dataPath, 'indexTradeDate.npy'), allow_pickle=True)
        self.indexTradeDate = pd.Series(self.indexTradeDate, name='dates').apply(lambda x: str(x))
        self.indexList = np.load('{}/{}'.format(dataPath, 'indexList.npy'), allow_pickle=True)
        self.indexList = pd.Series(self.indexList, name='indexIDs')
        # 存储预读取数据
        self.preRead = self.get_preRead(showProcess=showProcess)

    def get_readStyle(self, field):
        if field == 'Open': return 'indexOpen'
        elif field == 'High': return 'indexHigh'
        elif field == 'Low': return 'indexLow'
        elif field == 'Close': return 'indexClose'
        elif field == 'Amount': return 'indexAmount'
        elif field == 'Volume': return 'indexVolume'
        elif field == 'Change': return 'indexChange'
        elif field == 'ChangePerc': return 'indexChangePerc'

    def read_data(self, filename, index=True):
        """数据读取函数，从data文件夹中读取数据

        Args:
            filename (str): 要求读取的文件名称。带后缀，不需要指定文件夹
            index (bool, optional): 读取后是否加载表头。默认为True

        Returns:
            pd.DataFrame: 返回读取的结果，行按证券排序，列按日期排序
        """
        # 读取.npy文件，并转为dataframe
        data = np.load('{}/{}.npy'.format(self.dataPath, filename))
        data = pd.DataFrame(data)
        # 加载表头
        if index:
            data.columns = self.indexList
            data.index = self.indexTradeDate
        return data

    def get_preRead(self, showProcess):
        # 如果需要显示运行进度
        if showProcess:
            print('\n数据预读取提取开始')
            funStart, number = time.perf_counter(), 0
            self.preRead = OrderedDict()
            for field in self.preReadFields:
                filename = self.get_readStyle(field)
                self.preRead[field] = self.read_data(filename=filename)
                # 显示当前进度
                number += 1; funcPerc = number / len(self.preReadFields)
                fun.processing_bar(funcPerc, funStart)
            fun.processing_bar(1, funStart)
            print('\n数据预读取提取完成')

        # 如果不需要显示运行进度
        else:
            self.preRead = OrderedDict()
            for field in self.preReadFields:
                filename = self.get_readStyle(field)
                self.preRead[field] = self.read_data(filename=filename)

    def get_data(self, indexIDs, dates, fields, showProcess=True):
        """数据查找函数，查找目标指数在一段时间内的数据

        Args:
            indexIDs (pd.Series): 希望查询的指数代码
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
                dataTarget = self.preRead[field].loc[dates, indexIDs]
                dataResult[field] = dataTarget.stack()
                # 显示当前进度
                number += 1; funcPerc = number / (len(fields) + 1)
                fun.processing_bar(funcPerc, funStart)
            # 将已获取的数据转为pd.DataFrame类型
            dataResult = pd.DataFrame(dataResult).reset_index().set_index('indexIDs')
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
                dataTarget = self.preRead[field].loc[dates, indexIDs]
                dataResult[field] = dataTarget.stack()
            # 将已获取的数据转为pd.DataFrame类型
            dataResult = pd.DataFrame(dataResult).reset_index().set_index('indexIDs')
            return dataResult

    def get_infos(self, indexIDs, showProcess=True):
        """指数信息获取函数

        Args:
            indexIDs (pd.Series): 希望查询的指数代码

        Returns:
            pd.DataFrame: 返回查询的结果
        """
        # 如果需要显示运行进度
        if showProcess:
            print('\n股票简称获取开始')
            funStart = time.perf_counter()
            secNames = {}
            # 读取stockName数据
            indexInfos = pd.read_csv('{}/{}'.format(self.dataPath, 'indexInfos.csv'), encoding='utf-8-sig').set_index('indexID')
            # 根据输入的股票代码获取其所在位置，进而获取股票名称
            targetInfos = indexInfos.loc[indexIDs, :]
            fun.processing_bar(1, funStart)
            secNames = pd.Series(secNames, name='secNames')
            print('\n股票简称获取完成')
            return targetInfos

        # 如果不需要显示运行进度
        else:
            secNames = {}
            # 读取stockName数据
            indexInfos = pd.read_csv('{}/{}'.format(self.dataPath, 'indexInfos.csv'), encoding='utf-8-sig').set_index('indexID')
            # 根据输入的股票代码获取其所在位置，进而获取股票名称
            targetInfos = indexInfos.loc[indexIDs, :]
            secNames = pd.Series(secNames, name='secNames')
            return targetInfos
