# -*- encoding: utf-8 -*-
'''
Filename         :factorProcess.py
Description      :该模块用于对因子值进行预处理
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
from statsmodels.stats.stattools import medcouple
import time, os
from collections import OrderedDict
import basicFunction as fun
from getStock import stockclass
import warnings
warnings.filterwarnings("ignore")

plt.style.use('ggplot')
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文字体设置-黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
ticksDaily = ['20050104', '20070104', '20090105', '20110104', '20130104', '20150105', '20170103', '20190102', '20210104']
ticksMonthly = ['200501', '200701', '200901', '201101', '201301', '201501', '201701', '201901', '202101']


def describe(data, type='show', path='', freq='Daily'):
    '''描述性统计'''
    # 绘制概率密度直方图
    figurePDF, axesPDF = plt.subplots(figsize=(10, 5))
    axesPDF.hist(data.stack(), bins=100, density=True)
    # 绘制对应均值方差下的正态分布图
    mean, sigma = data.stack().mean(), data.stack().std()
    x = np.linspace(mean - 3 * sigma, mean + 3 * sigma, len(data.stack()))
    y = np.exp(-(x - mean)**2 / (2 * sigma**2)) / (np.sqrt(2 * np.pi) * sigma)
    axesPDF.plot(x, y, linewidth=2)
    axesPDF.set_title('全截面概率密度图', fontsize=14)
    axesPDF.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))

    # 绘制截面均值时序图
    CSMean = data.mean()
    figureMean, axesMean = plt.subplots(figsize=(10, 5))
    axesMean.plot(CSMean)
    axesMean.set_title('截面平均时序图', fontsize=14)
    axesMean.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
    if freq == 'Daily':
        axesMean.set_xticks(ticks=ticksDaily)
    elif freq == 'Monthly':
        axesMean.set_xticks(ticks=ticksMonthly)

    # 绘制截面波动时序图
    CSStd = data.std()
    figureStd, axesStd = plt.subplots(figsize=(10, 5))
    axesStd.plot(CSStd)
    axesStd.set_title('截面标准差时序图', fontsize=14)
    axesStd.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
    if freq == 'Daily':
        axesStd.set_xticks(ticks=ticksDaily)
    elif freq == 'Monthly':
        axesStd.set_xticks(ticks=ticksMonthly)

    # 计算描述性统计量
    summary = data.stack().describe()

    # 根据所选类型进行操作
    if type == 'show':
        print(summary)
        plt.show()
    elif type == 'save':
        if not os.path.exists(path): os.makedirs(path)
        figurePDF.savefig('{}/ProbabilityDensityFunction.png'.format(path), dpi=400)
        figureStd.savefig('{}/VolatilityTimeSeries.png'.format(path), dpi=400)
        figureMean.savefig('{}/MeanTimeSeries.png'.format(path), dpi=400)
        summary.to_csv('{}/summary.csv'.format(path))


def winsorize(data, type='Boxplot', times=5, threshold=0.1, scope=3):
    '''去极值'''
    # 计算程序运行时间
    print('\n去极值计算开始')
    funStart, number = time.perf_counter(), 0

    # 采用固定比例法去极值，即将头尾某一固定比例的极值去除
    if type == 'FixRate':
        afterWinsorize = OrderedDict()
        for column in data.columns:
            dataColumn = data[column].dropna()
            if not dataColumn.empty:
                min = dataColumn.quantile(threshold / 2)
                max = dataColumn.quantile(1 - threshold / 2)
                afterWinsorize[column] = np.clip(dataColumn, min, max)
            else:
                afterWinsorize[column] = pd.Series()
            # 显示当前进度
            number += 1; funcPerc = number / len(data.columns)
            fun.processing_bar(funcPerc, funStart)
        afterWinsorize = pd.DataFrame(afterWinsorize)
        print('\n去极值计算完成')
        return afterWinsorize

    # 采用均值方差法去极值，即假定因子在截面上服从正态分布，去除超过均值上下一定比例标准差的数值
    elif type == 'MeanStd':
        afterWinsorize = OrderedDict()
        for column in data.columns:
            dataColumn = data[column].dropna()
            if not dataColumn.empty:
                afterWinsorize[column] = dataColumn; NofTime = 0
                while NofTime < times:
                    min = dataColumn.mean() - scope * dataColumn.std()
                    max = dataColumn.mean() + scope * dataColumn.std()
                    afterWinsorize[column] = np.clip(afterWinsorize[column], min, max)
                    NofTime += 1
            else:
                afterWinsorize[column] = pd.Series()
            # 显示当前进度
            number += 1; funcPerc = number / len(data.columns)
            fun.processing_bar(funcPerc, funStart)
        afterWinsorize = pd.DataFrame(afterWinsorize)
        print('\n去极值计算完成')
        return afterWinsorize

    # 采用中值绝对偏差法去极值
    elif type == 'MAD':
        afterWinsorize = OrderedDict()
        for column in data.columns:
            dataColumn = data[column].dropna()
            if not dataColumn.empty:
                afterWinsorize[column] = dataColumn; NofTime = 0
                while NofTime < times:
                    median = dataColumn.median()
                    MAD = (dataColumn - median).abs().median()
                    min = median - scope * (1.483 * MAD)
                    max = median + scope * (1.483 * MAD)
                    afterWinsorize[column] = np.clip(afterWinsorize[column], min, max)
                    NofTime += 1
            else:
                afterWinsorize[column] = pd.Series()
            # 显示当前进度
            number += 1; funcPerc = number / len(data.columns)
            fun.processing_bar(funcPerc, funStart)
        afterWinsorize = pd.DataFrame(afterWinsorize)
        print('\n去极值计算完成')
        return afterWinsorize

    # 采用Boxplot法去极值
    elif type == 'Boxplot':
        afterWinsorize = OrderedDict()
        for column in data.columns:
            dataColumn = data[column].dropna()
            if not dataColumn.empty:
                afterWinsorize[column] = dataColumn; NofTime = 0
                while NofTime < times:
                    IQR = dataColumn.quantile(0.75) - dataColumn.quantile(0.25)
                    median, medCouple = dataColumn.median(), medcouple(dataColumn)
                    if medCouple >= 0:
                        min = dataColumn.quantile(0.25) - 1.5 * np.exp(-3.5 * medCouple) * IQR
                        max = dataColumn.quantile(0.75) + 1.5 * np.exp(4 * medCouple) * IQR
                    elif medCouple < 0:
                        min = dataColumn.quantile(0.25) - 1.5 * np.exp(-4 * medCouple) * IQR
                        max = dataColumn.quantile(0.75) + 1.5 * np.exp(3.5 * medCouple) * IQR
                    afterWinsorize[column] = np.clip(afterWinsorize[column], min, max)
                    NofTime += 1
            else:
                afterWinsorize[column] = pd.Series()
            # 显示当前进度
            number += 1; funcPerc = number / len(data.columns)
            fun.processing_bar(funcPerc, funStart)
        afterWinsorize = pd.DataFrame(afterWinsorize)
        print('\n去极值计算完成')
        return afterWinsorize


def neutralize(data):
    '''中性化'''
    # 计算程序运行时间
    print('\n中性化计算开始')
    funStart, number = time.perf_counter(), 0
    # 建立数据获取对象
    stockClass = stockclass('data/stock/1day', preReadFields=['MVFloat', 'IndZX'], showProcess=False)
    # 进行数据处理
    afterNeutralize = OrderedDict()
    # 遍历每一列数据
    for column in data.columns:
        # 获取该列数据
        dataColumn = data[column].dropna()
        if not dataColumn.empty:
            # 获取对应日期的流通市值与行业数据
            dataOriginal = stockClass.get_data(secIDs=dataColumn.index.tolist(), dates=[column],
                                               fields=['MVFloat', 'IndZX'], showProcess=False).dropna()
            # 为行业数据设定哑变量
            IndTypes = [i for i in range(1, int(dataOriginal['IndZX'].max()) + 1)]
            dataInd = pd.DataFrame(columns=IndTypes)
            for IndType in IndTypes:
                indexIndType = dataOriginal[dataOriginal['IndZX'] == IndType].index
                dataIndType = pd.DataFrame(columns=IndTypes, index=indexIndType).fillna(0)
                dataIndType[IndType] = 1
                dataInd = dataInd.append(dataIndType)
            dataInd = dataInd.loc[dataOriginal.index, :]
            # 整理数据
            dataColumnTotal = pd.DataFrame({'factor': dataColumn, 'MVFloat': np.log(dataOriginal['MVFloat'])}).join(dataInd).dropna()
            # 将因子数据对流通市值对数与行业哑变量进行回归，获取其残差
            X, y = sm.add_constant(dataColumnTotal[['MVFloat'] + IndTypes]), dataColumnTotal['factor']
            resid = sm.OLS(y, X.astype(float)).fit().resid
            resid.index = dataColumnTotal.index
            # 存储计算结果
            afterNeutralize[column] = resid
        else:
            afterNeutralize[column] = pd.Series()
        # 显示当前进度
        number += 1; funcPerc = number / len(data.columns)
        fun.processing_bar(funcPerc, funStart)
    afterNeutralize = pd.DataFrame(afterNeutralize)
    print('\n中性化计算完成')
    return afterNeutralize


def normalize(data, exception):
    '''正态化'''
    # 计算程序运行时间
    print('\n正态化计算开始')
    funStart, number = time.perf_counter(), 0
    # 获取lambda均值
    lambdas = OrderedDict()
    for column in data.columns:
        dataColumn = data[column].dropna()
        print(dataColumn)
        if not dataColumn.empty and column not in exception:
            afterBoxCox, lambdas[column] = stats.boxcox(dataColumn)
        else:
            lambdas[column] = np.nan
    lambdaMean = pd.Series(lambdas).mean()
    # 进行数据处理
    afterNormalize = OrderedDict()
    for column in data.columns:
        dataColumn = data[column].dropna()
        if not dataColumn.empty and column not in exception:
            afterBoxCox = pd.Series(stats.boxcox(dataColumn, lambdaMean))
            afterBoxCox.index = dataColumn.index
            afterNormalize[column] = afterBoxCox
        else:
            afterNormalize[column] = pd.Series()
        # 显示当前进度
        number += 1; funcPerc = number / len(data.columns)
        fun.processing_bar(funcPerc, funStart)
    afterNormalize = pd.DataFrame(afterNormalize)
    print('\n正态化计算完成')
    return afterNormalize


def standardize(data):
    '''标准化'''
    # 计算程序运行时间
    print('\n标准化计算开始')
    funStart, number = time.perf_counter(), 0
    # 进行数据处理
    afterStandardize = OrderedDict()
    for column in data.columns:
        dataColumn = data[column].dropna()
        if not dataColumn.empty:
            mean, std = dataColumn.mean(), dataColumn.std()
            afterStandardize[column] = (dataColumn - mean) / std
        else:
            afterStandardize[column] = pd.Series()
        # 显示当前进度
        number += 1; funcPerc = number / len(data.columns)
        fun.processing_bar(funcPerc, funStart)
    afterStandardize = pd.DataFrame(afterStandardize)
    print('\n标准化计算完成')
    return afterStandardize
