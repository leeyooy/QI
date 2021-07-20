# -*- encoding: utf-8 -*-
'''
Filename         :getDate.py
Description      :该模块用于获取日期
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import numpy as np
import pandas as pd
from collections import OrderedDict
import time
import basicFunction as fun


class dateclass:

    def __init__(self, cycleLength=20):
        # 读取交易日数据
        self.datesOriginal = np.load('data/stock/stockTradeDate.npy', allow_pickle=True)
        self.datesOriginal = pd.Series(self.datesOriginal, name='dates')
        # 获取日期及周期数据
        self.data = self.get_data(cycleLength)

    def get_data(self, cycleLength):
        # 存储计算结果
        data = OrderedDict()
        # 根据周期长度计算周期数
        cycleNumber = int(len(self.datesOriginal) / cycleLength)
        # 裁切交易日序列并给出交易日顺序
        datesStart = len(self.datesOriginal) % cycleLength
        datesTarget = self.datesOriginal.iloc[datesStart:].reset_index()['dates']
        data['dates'] = datesTarget.apply(lambda x: str(x))
        data['order'] = pd.Series(data['dates'].index)
        # 计算周期编号
        cycleOrders = []
        for cycleOrder in range(0, cycleNumber):
            cycleOrders = cycleOrders + ([cycleOrder] * cycleLength)
        data['cycles'] = pd.Series(cycleOrders)
        # 判断周期首尾
        BOCs = pd.Series([np.nan] * len(data['dates']))
        EOCs = pd.Series([np.nan] * len(data['dates']))
        for cycleOrder in range(0, cycleNumber):
            BOCs.iloc[(cycleOrder - 1) * cycleLength] = True
            EOCs.iloc[cycleOrder * cycleLength - 1] = True
        data['BOCs'], data['EOCs'] = BOCs, EOCs
        # 计算月份数
        data['months'] = data['dates'].apply(lambda x: x[: -2])
        # 判断月份首尾
        data['BOM'], testBOM = pd.Series([np.nan] * len(data['dates'])), ''
        for i in range(0, len(data['months']), 1):
            if data['months'].iloc[i] != testBOM:
                data['BOM'].iloc[i] = True
                testBOM = data['months'].iloc[i]
        data['EOM'], testEOM = pd.Series([np.nan] * len(data['dates'])), ''
        for i in range(len(data['months']) - 1, -1, -1):
            if data['months'].iloc[i] != testEOM:
                data['EOM'].iloc[i] = True
                testEOM = data['months'].iloc[i]
        # 将数据转为dataframe
        data = pd.DataFrame(data).set_index('dates')
        return data

    def get_dates(self, beginDate, endDate, printType='交易日序列', showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            print('\n获取{}开始'.format(printType))
            funStart, number = time.perf_counter(), 0
            # 开始函数主体
            beginDate, endDate, start, end = int(beginDate), int(endDate), '', ''
            if beginDate > int(self.data.index[0]):
                for date in self.data.index:
                    # 显示当前进度
                    number += 1
                    funcPerc = number / len(self.data.index)
                    fun.processing_bar(funcPerc, funStart)
                    if int(date) >= beginDate and start == '':
                        start = date
                        break
            else:
                start = self.data.index[0]
            if endDate < int(self.data.index[-1]):
                for date in self.data.loc[start:, :].index:
                    # 显示当前进度
                    number += 1
                    funcPerc = number / len(self.data.index)
                    fun.processing_bar(funcPerc, funStart)
                    if int(date) > endDate and end == '':
                        end = date
                        fun.processing_bar(1, funStart)
                        break
                targetDates = self.data.loc[start: end, :].iloc[: -1, :].index
            else:
                end = self.data.index[-1]
                fun.processing_bar(1, funStart)
                targetDates = self.data.loc[start: end, :].index
            targetDates = pd.Series(targetDates, name='dates')
            # 输出结果
            print('\n{}获取完成'.format(printType))
            return targetDates
        # 如果不需要显示运行进度
        else:
            beginDate, endDate, start, end = int(beginDate), int(endDate), '', ''
            if beginDate > int(self.data.index[0]):
                for date in self.data.index:
                    if int(date) >= beginDate and start == '':
                        start = date; break
            else:
                start = self.data.index[0]
            if endDate < int(self.data.index[-1]):
                for date in self.data.loc[start:, :].index:
                    if int(date) > endDate and end == '':
                        end = date; break
                targetDates = self.data.loc[start: end, :].iloc[: -1, :].index
            else:
                end = self.data.index[-1]
                targetDates = self.data.loc[start: end, :].index
            targetDates = pd.Series(targetDates, name='dates')
            return targetDates

    def get_beforeDate(self, currentDate, dateSpan, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n获取{} {}天前的交易日开始'.format(currentDate, dateSpan))
            funStart = time.perf_counter()
            currentOrder = self.data.loc[currentDate, 'order']
            beforeOrder = currentOrder - dateSpan
            if beforeOrder >= 0:
                beforeDate = self.data[self.data['order'] == beforeOrder].index[0]
                fun.processing_bar(1, funStart)
                print('\n{} {}天前的交易日获取完成'.format(currentDate, dateSpan))
                return beforeDate
            else:
                fun.processing_bar(1, funStart)
                print('\n{} {}天前的交易日获取完成'.format(currentDate, dateSpan))
                return 'out of range'
        # 如果不需要显示运行进度
        else:
            currentOrder = self.data.loc[currentDate, 'order']
            beforeOrder = currentOrder - dateSpan
            if beforeOrder >= 0:
                beforeDate = self.data[self.data['order'] == beforeOrder].index[0]
                return beforeDate
            else:
                return 'out of range'

    def get_afterDate(self, currentDate, dateSpan, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n获取{} {}天后的交易日开始'.format(currentDate, dateSpan))
            funStart = time.perf_counter()
            currentOrder = self.data.loc[currentDate, 'order']
            afterOrder = currentOrder + dateSpan
            if afterOrder <= self.data['order'].iloc[-1]:
                afterDate = self.data[self.data['order'] == afterOrder].index[0]
                fun.processing_bar(1, funStart)
                print('\n{} {}天前的交易日获取完成'.format(currentDate, dateSpan))
                return afterDate
            else:
                fun.processing_bar(1, funStart)
                print('\n{} {}天前的交易日获取完成'.format(currentDate, dateSpan))
                return 'out of range'
        # 如果不需要显示运行进度
        else:
            currentOrder = self.data.loc[currentDate, 'order']
            afterOrder = currentOrder + dateSpan
            if afterOrder <= self.data['order'].iloc[-1]:
                afterDate = self.data[self.data['order'] == afterOrder].index[0]
                return afterDate
            else:
                return 'out of range'

    def get_cycles(self, beginDate, endDate, showProcess=True):
        dateRange = self.get_dates(beginDate, endDate, printType='周期序列', showProcess=showProcess)
        targetData = self.data.loc[dateRange, :]
        targetMonths = []
        for month in targetData['cycles']:
            if month not in targetMonths:
                targetMonths.append(month)
        targetMonths = pd.Series(targetMonths, name='cycles')
        return targetMonths

    def get_BOCs(self, beginDate, endDate, showProcess=True):
        dateRange = self.get_dates(beginDate, endDate, printType='周期初交易日序列', showProcess=showProcess)
        targetData = self.data.loc[dateRange, :].reset_index()
        targetBOM = targetData[targetData['BOCs'] == True].set_index('cycles')
        return targetBOM['dates']

    def get_EOCs(self, beginDate, endDate, showProcess=True):
        dateRange = self.get_dates(beginDate, endDate, printType='周期末交易日序列', showProcess=showProcess)
        targetData = self.data.loc[dateRange, :].reset_index()
        targetEOM = targetData[targetData['EOCs'] == True].set_index('cycles')
        return targetEOM['dates']

    def get_DUCs(self, targetCycle, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n周期{}中的所有交易日获取开始'.format(targetCycle))
            funStart = time.perf_counter()
            targetData = self.data[self.data['cycles'] == targetCycle]
            targetDUM = pd.Series(targetData.index.tolist(), name='DUCs')
            fun.processing_bar(1, funStart)
            print('\n周期{}中的所有交易日获取完成'.format(targetCycle))
            return targetDUM
        # 如果不需要显示运行进度
        else:
            targetData = self.data[self.data['cycles'] == targetCycle]
            targetDUM = pd.Series(targetData.index.tolist(), name='DUCs')
            return targetDUM

    def get_beforeCycle(self, currentCycle, cycleSpan, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n{}前{}的周期数获取开始'.format(currentCycle, cycleSpan))
            funStart = time.perf_counter()
            targetCycle = currentCycle - cycleSpan
            fun.processing_bar(1, funStart)
            print('\n{}前{}的周期数获取完成'.format(currentCycle, cycleSpan))
            if targetCycle >= self.data['cycles'].min():
                return targetCycle
            else:
                return 'out of range'
        # 如果不需要显示运行进度
        else:
            targetCycle = currentCycle - cycleSpan
            if targetCycle >= self.data['cycles'].min():
                return targetCycle
            else:
                return 'out of range'

    def get_afterCycle(self, currentCycle, cycleSpan, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n{}后{}的周期数获取开始'.format(currentCycle, cycleSpan))
            funStart = time.perf_counter()
            targetCycle = currentCycle + cycleSpan
            fun.processing_bar(1, funStart)
            print('\n{}后{}的周期数获取完成'.format(currentCycle, cycleSpan))
            if targetCycle <= self.data['cycles'].max():
                return targetCycle
            else:
                return 'out of range'
        # 如果不需要显示运行进度
        else:
            targetCycle = currentCycle + cycleSpan
            if targetCycle <= self.data['cycles'].max():
                return targetCycle
            else:
                return 'out of range'

    def get_whichCycle(self, currentDate, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n获取{}的周期数开始'.format(currentDate))
            funStart = time.perf_counter()
            targetCycle = self.data.loc[currentDate, 'cycles']
            fun.processing_bar(1, funStart)
            print('\n获取{}的周期数完成'.format(currentDate))
            return targetCycle
        # 如果不需要显示运行进度
        else:
            targetCycle = self.data.loc[currentDate, 'cycles']
            return targetCycle

    def get_months(self, beginDate, endDate, showProcess=True):
        dateRange = self.get_dates(beginDate, endDate, printType='月份序列', showProcess=showProcess)
        targetData = self.data.loc[dateRange, :]
        targetMonths = []
        for month in targetData['months']:
            if month not in targetMonths:
                targetMonths.append(month)
        targetMonths = pd.Series(targetMonths, name='months')
        return targetMonths

    def get_BOMs(self, beginDate, endDate, showProcess=True):
        dateRange = self.get_dates(beginDate, endDate, printType='月初交易日序列', showProcess=showProcess)
        targetData = self.data.loc[dateRange, :].reset_index()
        targetBOM = targetData[targetData['BOM'] == True].set_index('months')
        return targetBOM['dates']

    def get_EOMs(self, beginDate, endDate, showProcess=True):
        dateRange = self.get_dates(beginDate, endDate, printType='月末交易日序列', showProcess=showProcess)
        targetData = self.data.loc[dateRange, :].reset_index()
        targetEOM = targetData[targetData['EOM'] == True].set_index('months')
        return targetEOM['dates']

    def get_DUMs(self, targetMonth, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n获取{}中的所有交易日开始'.format(targetMonth))
            funStart = time.perf_counter()
            targetData = self.data[self.data['months'] == targetMonth]
            targetDUM = pd.Series(targetData.index.tolist(), name='DUMs')
            fun.processing_bar(1, funStart)
            print('\n{}中的所有交易日获取完成'.format(targetMonth))
            return targetDUM

        # 如果不需要显示运行进度
        else:
            targetData = self.data[self.data['months'] == targetMonth]
            targetDUM = pd.Series(targetData.index.tolist(), name='DUMs')
            return targetDUM

    def get_beforeMonth(self, currentMonth, monthSpan, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n获取{} {}月前的月份数开始'.format(currentMonth, monthSpan))
            funStart = time.perf_counter()
            spread = int(currentMonth[-2:]) - monthSpan
            if spread > 0:
                beforeMonth = str(int(currentMonth) - monthSpan)
            else:
                if abs(spread) // 12 == 0:
                    year = int(currentMonth[:4]) - 1
                    month = 12 - abs(spread)
                elif abs(spread) // 12 > 0:
                    year = int(currentMonth[:4]) - 1 - (abs(spread) // 12)
                    month = 12 - (abs(spread) % 12)
                if month < 10:
                    beforeMonth = str(year) + '0' + str(month)
                else:
                    beforeMonth = str(year) + str(month)
            if beforeMonth in self.data['months'].tolist():
                fun.processing_bar(1, funStart)
                print('\n{} {}月前的月份数获取完成'.format(currentMonth, monthSpan))
                return beforeMonth
            else:
                fun.processing_bar(1, funStart)
                print('\n{} {}月前的月份数获取完成'.format(currentMonth, monthSpan))
                return 'out of range'

        # 如果不需要显示运行进度
        else:
            spread = int(currentMonth[-2:]) - monthSpan
            if spread > 0:
                beforeMonth = str(int(currentMonth) - monthSpan)
            else:
                if abs(spread) // 12 == 0:
                    year = int(currentMonth[:4]) - 1
                    month = 12 - abs(spread)
                elif abs(spread) // 12 > 0:
                    year = int(currentMonth[:4]) - 1 - (abs(spread) // 12)
                    month = 12 - (abs(spread) % 12)
                if month < 10:
                    beforeMonth = str(year) + '0' + str(month)
                else:
                    beforeMonth = str(year) + str(month)
            if beforeMonth in self.data['months'].tolist():
                return beforeMonth
            else:
                return 'out of range'

    def get_afterMonth(self, currentMonth, monthSpan, showProcess=True):
        # 如果需要显示运行进度
        if showProcess:
            # 计算函数运行时间
            print('\n获取{} {}月后的月份数开始'.format(currentMonth, monthSpan))
            funStart = time.perf_counter()
            spread = (12 - int(currentMonth[-2:])) - monthSpan
            if spread > 0:
                afterMonth = str(int(currentMonth) + monthSpan)
            else:
                if abs(spread) // 12 == 0:
                    year = int(currentMonth[:4]) + 1
                    month = abs(spread)
                elif abs(spread) // 12 > 0:
                    year = int(currentMonth[:4]) + 1 + (abs(spread) // 12)
                    month = abs(spread) % 12
                if month < 10:
                    afterMonth = str(year) + '0' + str(month)
                else:
                    afterMonth = str(year) + str(month)
            if afterMonth in self.data['months'].tolist():
                fun.processing_bar(1, funStart)
                print('\n{} {}月前的月份数获取完成'.format(currentMonth, monthSpan))
                return afterMonth
            else:
                fun.processing_bar(1, funStart)
                print('\n{} {}月前的月份数获取完成'.format(currentMonth, monthSpan))
                return 'out of range'

        # 如果不需要显示运行进度
        else:
            spread = (12 - int(currentMonth[-2:])) - monthSpan
            if spread > 0:
                afterMonth = str(int(currentMonth) + monthSpan)
            else:
                if abs(spread) // 12 == 0:
                    year = int(currentMonth[:4]) + 1
                    month = abs(spread)
                elif abs(spread) // 12 > 0:
                    year = int(currentMonth[:4]) + 1 + (abs(spread) // 12)
                    month = abs(spread) % 12
                if month < 10:
                    afterMonth = str(year) + '0' + str(month)
                else:
                    afterMonth = str(year) + str(month)
            if afterMonth in self.data['months'].tolist():
                return afterMonth
            else:
                return 'out of range'
