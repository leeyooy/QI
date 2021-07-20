# -*- encoding: utf-8 -*-
'''
Filename         :factorTest.py
Description      :该模块用于进行每日的单因子检验
Time             :2021/06/25 10:31:29
Author           :量化投资1组
Version          :1.0
'''

import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib import pyplot as plt
from matplotlib import ticker
from scipy import stats
import time, os
from collections import OrderedDict
import basicFunction as fun
from getDate import dateclass
from getStock import stockclass


plt.style.use('ggplot')
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文字体设置-黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

ticksDaily = ['20050104', '20070104', '20090105', '20110104', '20130104', '20150105', '20170103', '20190102', '20210104']
ticksMonthly = ['200501', '200701', '200901', '201101', '201301', '201501', '201701', '201901', '202101']


class ICIRclass():

    def __init__(self, beginDate, endDate, factor, confidence, frequency):
        # 赋值
        self.beginDate = beginDate
        self.endDate = endDate
        self.factor = factor
        self.confidence = confidence
        self.frequency = frequency
        # 获取必要的数据
        self.dateClass = dateclass(cycleLength=self.frequency)
        self.dates = self.dateClass.get_dates(self.beginDate, self.endDate, showProcess=False)
        self.cycles = self.dateClass.get_cycles(self.beginDate, self.endDate, showProcess=False)
        self.BOCs = self.dateClass.get_BOCs(self.beginDate, self.endDate, showProcess=False)
        self.EOCs = self.dateClass.get_EOCs(self.beginDate, self.endDate, showProcess=False)
        self.stockClass = stockclass('data/stock/1day', preRead=['OpenR', 'CloseR'], showProcess=False)
        self.stockPools = self.stockClass.get_stockPools(self.dates, showProcess=False)
        # 存储全截面因子与期望收益率
        self.dataFullSection = pd.DataFrame(columns=['factor', 'EReturn'])
        # 存储IC值
        self.IC = pd.DataFrame()
        # 存储描述性统计
        self.summary = pd.Series()
        # 存储IC时序图
        self.figureIC, self.axesIC = plt.subplots(figsize=(10, 5))
        # 存储因子与期望收益散点图
        self.figureScatter, self.axesScatter = plt.subplots(figsize=(10, 5))

    def get_result(self):

        # 计算程序运行时间
        print('\nIC计算开始')
        funStart, number = time.perf_counter(), 0
        # 设定存储数据
        spearman, pvalues, significance = OrderedDict(), OrderedDict(), OrderedDict()
        # 遍历所有周期
        for thisCycle in self.cycles:
            next1Cycle = self.dateClass.get_afterCycle(thisCycle, 1, showProcess=False)
            next2Cycle = self.dateClass.get_afterCycle(thisCycle, 2, showProcess=False)
            # 计算收益率数据
            # 如果能够获取下期与下下期的数据
            if next1Cycle != 'out of range' and next2Cycle != 'out of range':
                thisEOC, next1BOC, next2BOC = self.EOCs[thisCycle], self.BOCs[next1Cycle], self.BOCs[next2Cycle]
                # 获取下期期初的证券池
                stockPool = self.stockPools[next1BOC]
                # 计算下期期初开盘至下下期期初开盘的收益率
                dates = self.dateClass.get_dates(next1BOC, next2BOC, showProcess=False)
                dataPrice = self.stockClass.get_data(secIDs=stockPool, dates=dates, fields=['OpenR'], showProcess=False)
                next1Price = dataPrice[dataPrice['dates'] == next1BOC]['OpenR']
                next2Price = dataPrice[dataPrice['dates'] == next2BOC]['OpenR']
                dataReturn = next2Price / next1Price - 1
            # 如果能够获得下期的数据，但无法获得下下期的数据
            elif next1Cycle != 'out of range' and next2Cycle == 'out of range':
                thisEOC, nextBOC, nextEOC = self.EOCs[thisCycle], self.BOCs[next1Cycle], self.EOCs[next1Cycle]
                # 获取下期期初的证券池
                stockPool = self.stockPools[nextBOC]
                # 计算下期期初开盘至下期期末开盘的收益率
                dates = self.dateClass.get_dates(nextBOC, nextEOC, showProcess=False)
                dataPrice = self.stockClass.get_data(secIDs=stockPool, dates=dates, fields=['OpenR', 'CloseR'], showProcess=False)
                next1Price = dataPrice[dataPrice['dates'] == nextBOC]['OpenR']
                next2Price = dataPrice[dataPrice['dates'] == nextEOC]['CloseR']
                dataReturn = next2Price / next1Price - 1
            # 如果不能够获得下期与下下期的数据
            elif next1Cycle == 'out of range' and next2Cycle == 'out of range':
                stockPool = pd.Series([])
                dataReturn = pd.Series([])
            # 获取本期期末的因子值
            dataFactorOriginal = self.factor[thisEOC]
            # 获取下期期初可交易且本期期末有因子数据的证券列表
            secIDs = fun.extract_samePart(stockPool.tolist(), dataFactorOriginal.index.tolist())
            dataFactor = dataFactorOriginal[secIDs]
            # 整理因子值
            dataCrossSection = pd.DataFrame({'factor': dataFactor, 'EReturn': dataReturn}).dropna()
            # 如果有数据可以进行计算
            if not dataCrossSection.empty:
                self.dataFullSection = self.dataFullSection.append(dataCrossSection)
                # 计算本期IC值 (Spearman相关系数)
                spearman[thisEOC], pvalues[thisEOC] = stats.spearmanr(dataCrossSection['factor'], dataCrossSection['EReturn'])
                # 判断是否显著
                if pvalues[thisEOC] >= (1 - self.confidence):
                    significance[thisEOC] = '不显著'
                elif pvalues[thisEOC] < (1 - self.confidence) and spearman[thisEOC] > 0:
                    significance[thisEOC] = '正显著'
                elif pvalues[thisEOC] < (1 - self.confidence) and spearman[thisEOC] < 0:
                    significance[thisEOC] = '负显著'
            else:
                spearman[thisEOC], pvalues[thisEOC], significance[thisEOC] = np.nan, np.nan, np.nan
            # 显示当前进度
            number += 1; funPerc = number / len(self.cycles)
            fun.processing_bar(funPerc, funStart)
        # 汇总结果
        self.IC['IC'] = pd.Series(spearman, name='IC')
        self.IC['pvalues'] = pd.Series(pvalues, name='pvalues')
        self.IC['显著性'] = pd.Series(significance, name='显著性')
        print('\nIC计算完成')

        # 计算程序运行时间
        print('\n描述性统计计算开始')
        funStart = time.perf_counter()
        # 计算开始
        self.summary = self.IC['IC'].describe()
        self.summary['IR'] = self.IC['IC'].mean() / self.IC['IC'].std()
        ICAll, pvaluesAll = stats.spearmanr(self.dataFullSection['factor'], self.dataFullSection['EReturn'])
        self.summary.loc['ICAll'], self.summary.loc['pvaluesAll'] = ICAll, pvaluesAll
        # 显示进度
        fun.processing_bar(1, funStart)
        print('\n描述性统计计算完成')

        # 计算程序运行时间
        print('\n正负显著性判断开始')
        funStart, number = time.perf_counter(), 0
        # 计算开始
        lastSignType, Sign, PosSign, NegSign, ConSign, RevSign = '', 0, 0, 0, 0, 0
        for signType in self.IC['显著性']:
            # 判断当前是延续还是反转
            if signType != lastSignType and lastSignType != '':
                RevSign += 1
            elif signType == lastSignType:
                ConSign += 1
            # 判断当前是正显著还是负显著
            if signType == '正显著':
                PosSign += 1; Sign += 1; lastSignType = signType
            elif signType == '负显著':
                NegSign += 1; Sign += 1; lastSignType = signType
            # 显示当前进度
            number += 1; funPerc = number / len(self.IC['显著性'])
            fun.processing_bar(funPerc, funStart)
        self.summary.loc['SignRatio'] = Sign / len(self.IC['显著性'])
        self.summary.loc['PosSignRatio'] = PosSign / len(self.IC['显著性'])
        self.summary.loc['NegSignRatio'] = NegSign / len(self.IC['显著性'])
        self.summary.loc['ConSignRatio'] = ConSign / len(self.IC['显著性'])
        self.summary.loc['RevSignRatio'] = RevSign / len(self.IC['显著性'])
        # 显示进度
        print('\n正负显著性判断完成')

        # 计算程序运行时间
        print('\n因子值与期望收益率散点图绘制开始')
        funStart = time.perf_counter()
        # 计算开始
        self.axesScatter.scatter(x=self.dataFullSection['factor'], y=self.dataFullSection['EReturn'])
        self.axesScatter.set_title('因子值与期望收益率散点图', fontsize=14)
        self.axesScatter.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        self.axesScatter.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        # 显示进度
        fun.processing_bar(1, funStart)
        print('\n因子值与期望收益率散点图绘制完成')

        # 计算程序运行时间
        print('\nIC时序图绘制开始')
        funStart = time.perf_counter()
        # 颜色分类
        color = []
        for item in self.IC['显著性']:
            if item == '正显著': color.append('red')
            elif item == '负显著': color.append('green')
            else: color.append('gray')
        # 绘制图像
        self.axesIC.scatter(x=self.IC['IC'].index, y=self.IC['IC'], color=color)
        self.axesIC.set_title('IC时序图', fontsize=14)
        self.axesIC.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        # 划分x轴
        cycleNumber = self.dateClass.data['cycles'].max() + 1
        showLength = int(cycleNumber / 8)
        ticks = [self.EOCs[i * showLength] for i in range(0, 9)]
        self.axesIC.set_xticks(ticks=ticks)
        # 显示进度
        fun.processing_bar(1, funStart)
        print('\nIC时序图绘制完成')

    def save_result(self, path):
        # 计算程序运行时间
        print('\nICIR存储开始')
        funStart = time.perf_counter()
        # 计算开始
        if not os.path.exists('{}/IC'.format(path)):
            os.makedirs('{}/IC'.format(path))
        self.IC.to_csv('{}/IC/ICMonth.csv'.format(path))
        self.summary.to_csv('{}/IC/ICSummary.csv'.format(path))
        self.figureIC.savefig('{}/IC/ICFigure.png'.format(path), dpi=400)
        self.figureScatter.savefig('{}/IC/factor-EReturn.png'.format(path), dpi=400)
        # 显示进度
        fun.processing_bar(1, funStart)
        print('\nICIR存储完成')


class groupclass():

    def __init__(self, beginDate, endDate, factor, groupNumber, ascending=True, frequency=20):
        # 赋值
        self.beginDate = beginDate
        self.endDate = endDate
        self.factor = factor
        self.groupNumber = groupNumber
        self.ascending = ascending
        self.frequency = frequency
        self.groups = [i for i in range(1, self.groupNumber + 1)]
        # 获取必要的数据
        self.dateClass = dateclass(cycleLength=self.frequency)
        self.dates = self.dateClass.get_dates(self.beginDate, self.endDate, showProcess=False)
        self.cycles = self.dateClass.get_cycles(self.beginDate, self.endDate, showProcess=False)
        self.BOCs = self.dateClass.get_BOCs(self.beginDate, self.endDate, showProcess=False)
        self.EOCs = self.dateClass.get_EOCs(self.beginDate, self.endDate, showProcess=False)
        self.months = self.dateClass.get_months(self.beginDate, self.endDate, showProcess=False)
        self.BOMs = self.dateClass.get_BOMs(self.beginDate, self.endDate, showProcess=False)
        self.EOMs = self.dateClass.get_EOMs(self.beginDate, self.endDate, showProcess=False)
        self.stockClass = stockclass('data/stock/1day', preRead=['MVFloat', 'OpenR', 'CloseR'], showProcess=False)
        self.stockPools = self.stockClass.get_stockPools(self.dates, showProcess=False)
        # 存储持仓数据
        self.groupWeights = OrderedDict()
        # 存储换手率数据
        self.turnoverRate = pd.DataFrame(columns=self.groups)
        # 存储各组日收益率数据
        self.groupRetDaily = pd.DataFrame(columns=self.groups)
        self.groupRetDaily.loc[self.dates[0], :] = pd.Series({groupOrder: np.nan for groupOrder in self.groups})
        # 存储各组日净值数据
        self.groupNevDaily = pd.DataFrame(columns=self.groups)
        self.groupNevDaily.loc[self.dates[0], :] = pd.Series({groupOrder: 1 for groupOrder in self.groups})
        # 存储top-bottom日数据
        self.TMBDaily = pd.DataFrame()
        # 存储各组周期收益率数据
        self.groupRetMonthly = pd.DataFrame(columns=self.groups)
        # 存储各组周期净值数据
        self.groupNevMonthly = pd.DataFrame(columns=self.groups)
        # 存储top-bottom月数据
        self.TMBMonthly = pd.DataFrame()
        # 存储summary数据
        self.summary = pd.DataFrame(columns=self.groups + ['TMB'])
        # 存储历史回撤
        self.drawDown = pd.DataFrame(columns=self.groups + ['TMB'])
        # 存储各组年化超额收益率图
        self.figureExcessRet, self.axesExcessRet = plt.subplots(figsize=(10, 5))
        # 存储各组净值图
        self.figureNevDaily, self.axesNevDaily = plt.subplots(figsize=(10, 5))
        # 存储TMB月收益率图
        self.figureTMBRetMonthly, self.axesTMBRetMonthly = plt.subplots(figsize=(10, 5))
        # 存储TMB净值图
        self.figureTMBNevDaily, self.axesTMBNevDaily = plt.subplots(figsize=(10, 5))
        # 存储TMB回撤图
        self.figureTMBDrawDown, self.axesTMBDrawDown = plt.subplots(figsize=(10, 5))

    def get_result(self, type='等权重'):

        print('\n分组组合权重计算开始')
        funStart, number = time.perf_counter(), 0
        # 遍历所有周期
        for thisCycle in self.cycles:
            # 获取下个周期
            nextCycle = self.dateClass.get_afterCycle(thisCycle, 1, showProcess=False)
            # 如果能够获得下期的数据
            if nextCycle != 'out of range':
                thisEOC, nextBOC = self.EOCs[thisCycle], self.BOCs[nextCycle]
                # 存储根据本期数据计算所得的权重
                self.groupWeights[nextBOC] = OrderedDict()
                # 获取下期期初的证券池
                stockPool = self.stockPools[nextBOC]
                # 获取本期期末的因子数据
                dataFactorOriginal = self.factor[thisEOC].dropna()
                # 获取调仓时可交易且本期期末有因子数据的证券列表
                secIDs = fun.extract_samePart(stockPool.tolist(), dataFactorOriginal.index.tolist())
                dataFactor = dataFactorOriginal[secIDs]
                # 如果有符合要求的证券池与因子数据
                if not dataFactor.empty:
                    # 对因子进行排序
                    dataFactorOrdered = dataFactor.sort_values(ascending=self.ascending)
                    # 分配各组所含证券数量
                    lengthOfGroups = OrderedDict()
                    for groupOrder in self.groups:
                        if groupOrder <= len(dataFactorOrdered) % self.groupNumber:
                            lengthOfGroups[groupOrder] = int(len(dataFactorOrdered) / self.groupNumber) + 1
                        else:
                            lengthOfGroups[groupOrder] = int(len(dataFactorOrdered) / self.groupNumber)
                    lengthOfGroups = pd.Series(lengthOfGroups)
                    # 分配各组所含证券代码与对应的因子值
                    factorOfGroups = OrderedDict()
                    for groupOrder in self.groups:
                        if groupOrder == 1:
                            start = 0
                            end = lengthOfGroups.loc[groupOrder]
                        else:
                            start = lengthOfGroups.loc[1: groupOrder - 1].sum()
                            end = start + lengthOfGroups[groupOrder]
                        factorOfGroups[groupOrder] = dataFactorOrdered.iloc[start: end]
                    # 计算各组投资组合权重(等权重)
                    if type == '等权重':
                        for groupOrder in self.groups:
                            # 计算本组内权重
                            weightOfGroup = OrderedDict()
                            for secID in factorOfGroups[groupOrder].index:
                                weightOfGroup[secID] = 1 / len(factorOfGroups[groupOrder])
                            self.groupWeights[nextBOC][groupOrder] = pd.Series(weightOfGroup)
                    # 计算各组投资组合权重(因子权重)
                    elif type == '因子权重':
                        for groupOrder in self.groups:
                            factorOfGroup = factorOfGroups[groupOrder]
                            self.groupWeights[nextBOC][groupOrder] = factorOfGroup / factorOfGroup.sum()
                    # 计算各组投资组合权重(市值权重)
                    elif type == '市值权重':
                        dataMVFloat = self.stockClass.get_data(secIDs=dataFactor.index.tolist(), dates=[thisEOC], fields=['MVFloat'],
                                                               showProcess=False)['MVFloat']
                        for groupOrder in self.groups:
                            LogMVFloatGroup = dataMVFloat.loc[factorOfGroups[groupOrder].index].apply(lambda x: np.log(x))
                            self.groupWeights[nextBOC][groupOrder] = LogMVFloatGroup / LogMVFloatGroup.sum()
                # 如果没有符合要求的证券池与因子数据
                else:
                    for groupOrder in self.groups:
                        self.groupWeights[nextBOC][groupOrder] = pd.Series([])
            # 显示当前进度
            number += 1; funcPerc = number / len(self.cycles)
            fun.processing_bar(funcPerc, funStart)
        # 存储第一期的数据
        self.groupWeights[self.EOCs[0]] = OrderedDict()
        for groupOrder in self.groups:
            self.groupWeights[self.EOCs[0]][groupOrder] = pd.Series([])
        print('\n分组组合权重计算完成')

        # 计算程序运行时间
        print('\n换手率计算开始')
        funStart, number = time.perf_counter(), 0
        # 遍历所有周期
        for thisCycle in self.cycles:
            lastCycle = self.dateClass.get_beforeCycle(thisCycle, 1, showProcess=False)
            if lastCycle != 'out of range':
                thisBOC, lastBOC = self.BOCs[thisCycle], self.BOCs[lastCycle]
                turnoverRate = OrderedDict()
                for groupOrder in self.groups:
                    weightThisCycle = self.groupWeights[thisBOC][groupOrder]
                    weightLastCycle = self.groupWeights[lastBOC][groupOrder]
                    weightTotal = pd.DataFrame({'thisCycle': weightThisCycle, 'lastCycle': weightLastCycle}).fillna(0)
                    turnoverRate[groupOrder] = (weightTotal['thisCycle'] - weightTotal['lastCycle']).abs().sum()
                self.turnoverRate.loc[thisBOC, :] = pd.Series(turnoverRate)
            else:
                thisBOC = self.BOCs[thisCycle]
                turnoverRate = OrderedDict()
                for groupOrder in self.groups:
                    turnoverRate[groupOrder] = np.nan
                self.turnoverRate.loc[thisBOC, :] = pd.Series(turnoverRate)
            # 显示当前进度
            number += 1; funPerc = number / len(self.dates)
            fun.processing_bar(funPerc, funStart)
        # 提示程序运行完成
        print('\n换手率计算完成')

        print('\n分组日频数据计算开始')
        funStart, number = time.perf_counter(), 0
        # 遍历所有日期
        for thisDate in self.dates:
            # 存储当日收益与净值数据
            returnDaily, valueDaily = OrderedDict(), OrderedDict()
            # 获取本期权重数据
            thisCycle = self.dateClass.get_whichCycle(thisDate, showProcess=False)
            weightOfGroups = self.groupWeights[self.BOCs[thisCycle]]
            # 遍历所有组合
            for groupOrder in self.groups:
                # 获取当前组合权重
                weightOfGroup = weightOfGroups[groupOrder]
                # 如果当日权重数据不为空
                if not weightOfGroup.empty:
                    # 判断后一日是否有数据
                    nextDate = self.dateClass.get_afterDate(thisDate, 1, showProcess=False)
                    # 如果下一日有数据的话
                    if nextDate != 'out of range':
                        # 获取当日开盘至下一日开盘的收益率
                        dataPrice = self.stockClass.get_data(secIDs=weightOfGroup.index.tolist(), dates=[thisDate, nextDate],
                                                             fields=['OpenR'], showProcess=False)
                        thisPrice = dataPrice[dataPrice['dates'] == thisDate]['OpenR']
                        nextPrice = dataPrice[dataPrice['dates'] == nextDate]['OpenR']
                        dataReturn = nextPrice / thisPrice - 1
                    # 如果下一日无数据的话
                    else:
                        dataPrice = self.stockClass.get_data(secIDs=weightOfGroup.index.tolist(), dates=[thisDate],
                                                             fields=['OpenR', 'CloseR'], showProcess=False)
                        thisPrice = dataPrice['OpenR']; nextPrice = dataPrice['CloseR']
                        dataReturn = nextPrice / thisPrice - 1
                    # 计算组合收益
                    returnDaily[groupOrder] = (weightOfGroup * dataReturn).sum()
                    # 计算组合净值
                    valueDaily[groupOrder] = self.groupNevDaily.iloc[-1, :].loc[groupOrder] * (1 + returnDaily[groupOrder])
                else:
                    # 延续之前的收益与净值设定
                    returnDaily[groupOrder] = self.groupRetDaily.iloc[-1, :].loc[groupOrder]
                    valueDaily[groupOrder] = self.groupNevDaily.iloc[-1, :].loc[groupOrder]
            # 存储收益与净值
            self.groupRetDaily.loc[thisDate, :] = pd.Series(returnDaily)
            self.groupNevDaily.loc[thisDate, :] = pd.Series(valueDaily)
            # 显示当前进度
            number += 1; funcPerc = number / len(self.dates)
            fun.processing_bar(funcPerc, funStart)
        print('\n分组日频数据计算完成')

        # 计算程序运行时间
        print('\n分组月频数据计算开始')
        funStart, number = time.perf_counter(), 0
        # 遍历所有月份
        for thisMonth in self.months:
            # 存储收益与净值数据
            RetMonthly, NevMonthly = OrderedDict(), OrderedDict()
            # 获取上个月的月份数
            lastMonth = self.dateClass.get_beforeMonth(thisMonth, 1, showProcess=False)
            # 如果上个月在数据范围内
            if lastMonth != 'out of range':
                # 遍历所有组合
                for groupOrder in self.groups:
                    # 获取本月月末与下月月末的组合净值
                    netValueThisEOM = self.groupNevDaily[groupOrder].loc[self.EOMs[thisMonth]]
                    netValuelastEOM = self.groupNevDaily[groupOrder].loc[self.EOMs[lastMonth]]
                    # 计算收益率与净值
                    RetMonthly[groupOrder] = netValueThisEOM / netValuelastEOM - 1
                    NevMonthly[groupOrder] = netValueThisEOM
            else:
                # 遍历所有组合
                for groupOrder in self.groups:
                    # 获取本月月末与下月月末的组合净值
                    netValueThisEOM = self.groupNevDaily[groupOrder].loc[self.EOMs[thisMonth]]
                    netValueThisBOM = self.groupNevDaily[groupOrder].loc[self.BOMs[thisMonth]]
                    # 计算收益率与净值
                    RetMonthly[groupOrder] = netValueThisEOM / netValueThisBOM - 1
                    NevMonthly[groupOrder] = netValueThisEOM
            self.groupRetMonthly.loc[thisMonth, :] = pd.Series(RetMonthly)
            self.groupNevMonthly.loc[thisMonth, :] = pd.Series(NevMonthly)
            # 显示当前进度
            number += 1; funcPerc = number / len(self.months)
            fun.processing_bar(funcPerc, funStart)
        print('\n分组月频数据计算完成')

        # 计算程序运行时间
        print('\ntop-bottom组合日频数据计算开始')
        funStart, number = time.perf_counter(), 0
        # 计算top-bottom组合日收益率数据
        self.TMBDaily['return'] = self.groupRetDaily[1] - self.groupRetDaily[self.groupNumber]
        # 计算top-bottom组合日净值数据
        netValue, value = OrderedDict(), 1
        for date in self.dates:
            returnToday = self.TMBDaily['return'].loc[date]
            if not np.isnan(returnToday):
                value = value * (1 + returnToday)
            else:
                value = value
            netValue[date] = value
            # 显示当前进度
            number += 1; funPerc = number / len(self.dates)
            fun.processing_bar(funPerc, funStart)
        self.TMBDaily['value'] = pd.Series(netValue)
        # 提示程序运行完成
        print('\ntop-bottom组合日频数据计算完成')

        # 计算程序运行时间
        print('\ntop-bottom组合月频数据计算开始')
        funStart, number = time.perf_counter(), 0
        RetMonthly, NevMonthly = OrderedDict(), OrderedDict()
        for thisMonth in self.months:
            lastMonth = self.dateClass.get_beforeMonth(thisMonth, 1, showProcess=False)
            # 如果上个月在数据范围内
            if lastMonth != 'out of range':
                netValueThisEOM = self.TMBDaily['value'].loc[self.EOMs[thisMonth]]
                netValueLastEOM = self.TMBDaily['value'].loc[self.EOMs[lastMonth]]
                RetMonthly[thisMonth] = netValueThisEOM / netValueLastEOM - 1
                NevMonthly[thisMonth] = netValueThisEOM
            else:
                netValueThisEOM = self.TMBDaily['value'].loc[self.EOMs[thisMonth]]
                netValueThisBOM = self.TMBDaily['value'].loc[self.BOMs[thisMonth]]
                RetMonthly[thisMonth] = netValueThisEOM / netValueThisBOM - 1
                NevMonthly[thisMonth] = netValueThisEOM
            # 显示当前进度
            number += 1; funPerc = number / len(self.months)
            fun.processing_bar(funPerc, funStart)
        self.TMBMonthly['return'] = pd.Series(RetMonthly)
        self.TMBMonthly['value'] = pd.Series(NevMonthly)
        # 提示程序运行完成
        print('\ntop-bottom组合月频数据计算完成')

        # 计算程序运行时间
        print('\n指标计算开始')
        funStart, number = time.perf_counter(), 0
        # 读取必要数据
        benchmarkRetDaily = pd.read_csv('factor/benchmark/benchmarkRetDaily.csv')
        benchmarkRetDaily['dates'] = benchmarkRetDaily['dates'].apply(lambda x: str(x))
        benchmarkRetDaily = benchmarkRetDaily.set_index('dates')['RetDaily']
        benchmarkNevDaily = pd.read_csv('factor/benchmark/benchmarkNevDaily.csv')
        benchmarkNevDaily['dates'] = benchmarkNevDaily['dates'].apply(lambda x: str(x))
        benchmarkNevDaily = benchmarkNevDaily.set_index('dates')['NevDaily']
        benchmarkRetMonthly = pd.read_csv('factor/benchmark/benchmarkRetMonthly.csv')
        benchmarkRetMonthly['months'] = benchmarkRetMonthly['months'].apply(lambda x: str(x))
        benchmarkRetMonthly = benchmarkRetMonthly.set_index('months')['RetMonthly']
        benchmarkNevMonthly = pd.read_csv('factor/benchmark/benchmarkNevMonthly.csv')
        benchmarkNevMonthly['months'] = benchmarkNevMonthly['months'].apply(lambda x: str(x))
        benchmarkNevMonthly = benchmarkNevMonthly.set_index('months')['NevMonthly']
        # 计算各组指标
        for groupOrder in self.groups:
            targetRetDaily = self.groupRetDaily[groupOrder]
            targetNevDaily = self.groupNevDaily[groupOrder]
            targetRetMonthly = self.groupRetMonthly[groupOrder]
            indicatorsDaily, drawDown = self.get_indicatorsDaily(targetRetDaily, targetNevDaily, benchmarkRetDaily, benchmarkNevDaily, 0.04)
            indicatorsMonthly = self.get_indicatorsMonthly(targetRetMonthly, benchmarkRetMonthly)
            self.summary[groupOrder] = indicatorsDaily.append(indicatorsMonthly)
            self.drawDown[groupOrder] = drawDown
            # 显示当前进度
            number += 1; funPerc = number / (self.groupNumber + 1)
            fun.processing_bar(funPerc, funStart)
        # 计算TMB指标
        targetRetDaily, targetNevDaily, targetRetMonthly = self.TMBDaily['return'], self.TMBDaily['value'], self.TMBMonthly['return']
        indicatorsDaily, drawDown = self.get_indicatorsDaily(targetRetDaily, targetNevDaily, benchmarkRetDaily, benchmarkNevDaily, 0.04)
        indicatorsMonthly = self.get_indicatorsMonthly(targetRetMonthly, benchmarkRetMonthly)
        self.summary['TMB'] = indicatorsDaily.append(indicatorsMonthly)
        self.drawDown['TMB'] = drawDown
        # 显示当前进度
        fun.processing_bar(1, funStart)
        print('\n指标计算开始')

        # 计算程序运行时间
        print('\n图形绘制开始')
        funStart, number = time.perf_counter(), 0
        # 各组年化超额收益率图
        height = self.summary.loc['excessRet', self.groups]
        index = ['第{}组'.format(order) for order in range(1, len(height) + 1)]
        colors = []
        for item in height:
            if item > 0: colors.append('red')
            else: colors.append('green')
        rects = self.axesExcessRet.bar(x=index, height=height, color=colors)
        self.axesExcessRet.set_title('各组年化超额收益率图', fontsize=14)
        self.axesExcessRet.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        for rect in rects:
            text = '{}%'.format(round(rect.get_height() * 100, 2))
            if rect.get_height() > 0:
                self.axesExcessRet.text(rect.get_x() + rect.get_width() / 2, rect.get_height(), text, ha='center')
            else:
                self.axesExcessRet.text(rect.get_x() + rect.get_width() / 2, rect.get_height(), text, ha='center')
        # 各组净值图
        for group in self.groupNevDaily.columns:
            line = self.groupNevDaily[group]
            self.axesNevDaily.plot(line.index, line, label='第{}组'.format(group))
        self.axesNevDaily.set_title('各组净值图', fontsize=14)
        self.axesNevDaily.set_xticks(ticks=ticksDaily)
        # TMB组合月收益率
        height = self.TMBMonthly['return']
        colors = []
        for item in height:
            if item > 0: colors.append('red')
            else: colors.append('green')
        self.axesTMBRetMonthly.bar(x=height.index, height=height, color=colors)
        self.axesTMBRetMonthly.set_title('top-bottom组合月度收益率', fontsize=14)
        self.axesTMBRetMonthly.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        self.axesTMBRetMonthly.set_xticks(ticks=ticksMonthly)
        self.axesNevDaily.legend(loc='upper left')
        # TMB净值图
        line = self.TMBDaily['value']
        self.axesTMBNevDaily.plot(line.index, line)
        self.axesTMBNevDaily.set_title('top-bottom组合净值图', fontsize=14)
        self.axesTMBNevDaily.set_xticks(ticks=ticksDaily)
        # TMB回撤图
        line = self.drawDown['TMB']
        self.axesTMBDrawDown.plot(line.index, line)
        self.axesTMBDrawDown.set_title('top-bottom组合回撤图', fontsize=14)
        self.axesTMBDrawDown.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        self.axesTMBDrawDown.set_xticks(ticks=ticksDaily)
        # 显示当前进度
        fun.processing_bar(1, funStart)
        print('\n图形绘制完成')

    def get_indicatorsDaily(self, targetRetDaily, targetNevDaily, benchmarkRetDaily, benchmarkNevDaily, riskfreeRate):
        indicatorsDaily = OrderedDict()
        # 计算日均收益率
        indicatorsDaily['meanRetDaily'] = np.mean(targetRetDaily)
        # 计算日胜率
        excessRetDaily = targetRetDaily - benchmarkRetDaily
        winNumber = 0
        for item in excessRetDaily:
            if item > 0: winNumber += 1
        indicatorsDaily['winRateDaily'] = winNumber / len(excessRetDaily)
        # 计算年化收益率及年化超额收益率
        indicatorsDaily['targetRet'] = (targetNevDaily.iloc[-1] / targetNevDaily.iloc[0]) ** (250 / len(targetNevDaily))
        indicatorsDaily['benchmarkRet'] = (benchmarkNevDaily.iloc[-1] / benchmarkNevDaily.iloc[0]) ** (250 / len(benchmarkNevDaily))
        indicatorsDaily['excessRet'] = indicatorsDaily['targetRet'] - indicatorsDaily['benchmarkRet']
        # 计算收益波动率
        indicatorsDaily['sigma'] = np.sqrt(250 / (len(targetRetDaily) - 1) * np.sum((targetRetDaily - targetRetDaily.mean()).apply(lambda x: x**2)))
        # 计算夏普比率
        indicatorsDaily['sharpeRatio'] = (indicatorsDaily['targetRet'] - riskfreeRate) / indicatorsDaily['sigma']
        # 计算信息比
        indicatorsDaily['IR'] = (indicatorsDaily['targetRet'] - indicatorsDaily['benchmarkRet']) / (np.std(excessRetDaily) * np.sqrt(250))
        # 计算历史回撤
        drawDown = OrderedDict()
        for date in targetNevDaily.index:
            previousNevDaily = targetNevDaily.loc[: date]
            drawDown[date] = 1 - previousNevDaily.iloc[-1] / previousNevDaily.max()
        drawDown = pd.Series(drawDown)
        # 计算最大回撤
        indicatorsDaily['maxDrawDown'] = drawDown.max()
        # 结构化数据
        indicatorsDaily = pd.Series(indicatorsDaily)
        return indicatorsDaily, drawDown

    def get_indicatorsMonthly(self, targetRetMonthly, benchmarkRetMonthly):
        indicatorsMonthly = OrderedDict()
        # 计算月均收益率
        indicatorsMonthly['meanRetMonthly'] = np.mean(targetRetMonthly)
        # 计算月胜率
        excessRetMonthly = targetRetMonthly - benchmarkRetMonthly
        winNumber = 0
        for item in excessRetMonthly:
            if item > 0: winNumber += 1
        indicatorsMonthly['winRateMonthly'] = winNumber / len(excessRetMonthly)
        # 结构化数据
        indicatorsMonthly = pd.Series(indicatorsMonthly)
        return indicatorsMonthly

    def save_result(self, path):
        # 计算程序运行时间
        print('\n分层结果存储开始')
        funStart = time.perf_counter()
        if not os.path.exists('{}/groups'.format(path)):
            os.makedirs('{}/groups'.format(path))
        self.turnoverRate.to_csv('{}/groups/turnoverRate.csv'.format(path))
        self.groupRetDaily.to_csv('{}/groups/groupRetDaily.csv'.format(path))
        self.groupNevDaily.to_csv('{}/groups/groupNevDaily.csv'.format(path))
        self.TMBDaily.to_csv('{}/groups/TMBDaily.csv'.format(path))
        self.groupRetMonthly.to_csv('{}/groups/groupRetMonthly.csv'.format(path))
        self.groupNevMonthly.to_csv('{}/groups/groupNevMonthly.csv'.format(path))
        self.TMBMonthly.to_csv('{}/groups/TMBMonthly.csv'.format(path))
        self.summary.to_csv('{}/groups/summary.csv'.format(path))
        self.drawDown.to_csv('{}/groups/drawDown.csv'.format(path))
        self.figureExcessRet.savefig('{}/groups/figureExcessRet.png'.format(path), dpi=400)
        self.figureNevDaily.savefig('{}/groups/figureNevDaily.png'.format(path), dpi=400)
        self.figureTMBRetMonthly.savefig('{}/groups/figureTMBRetMonthly.png'.format(path), dpi=400)
        self.figureTMBNevDaily.savefig('{}/groups/figureTMBNevDaily.png'.format(path), dpi=400)
        self.figureTMBDrawDown.savefig('{}/groups/figureTMBDrawDown.png'.format(path), dpi=400)
        fun.processing_bar(1, funStart)
        print('\n分层结果存储完成')


class regressionclass():

    def __init__(self, factor, EReturn, beginDate, endDate):
        self.factor = factor
        self.EReturn = EReturn
        self.beginDate = beginDate
        self.endDate = endDate
        self.months = dateclass('data/date').get_months(beginDate, endDate, showProcess=False)

    def get_result(self):
        # 计算程序运行时间
        print('\n回归计算开始')
        funStart, number = time.perf_counter(), 0
        params, tvalues, pvalues = OrderedDict(), OrderedDict(), OrderedDict()
        for month in self.months:
            # 获取本月因子数据与期望收益率数据
            dataMonth = pd.DataFrame({'factor': self.factor[month], 'EReturn': self.EReturn[month]}).dropna()
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
            number += 1; funPerc = number / len(self.months)
            fun.processing_bar(funPerc, funStart)
        # 汇总结果
        params, tvalues, pvalues = pd.Series(params), pd.Series(tvalues), pd.Series(pvalues)
        regressionResult = pd.DataFrame({'params': params, 'tvalues': tvalues, 'pvalues': pvalues})
        print('\n回归计算完成')
        return regressionResult

    def save_result(self, path, regressionResult):
        # 计算程序运行时间
        print('\n回归结果存储开始')
        funStart = time.perf_counter()
        if not os.path.exists('{}/regression'.format(path)):
            os.makedirs('{}/regression'.format(path))
        regressionResult.to_csv('{}/regression/regression.csv'.format(path))
        fun.processing_bar(1, funStart)
        print('\n回归结果存储完成')
