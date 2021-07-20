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
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor
import time, os, sys, warnings
sys.path.append('modules')
import basicFunction as fun
from getStock import stockclass

warnings.filterwarnings("ignore")

plt.style.use('ggplot')
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文字体设置-黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

stockClass = stockclass('data/stock/1day', preReadFields=['MVFloat', 'IndZX'], showProcess=False)

data = pd.read_csv('factor/东方证券_009/东方证券_009_iDStd.csv').set_index('secIDs')
path = 'result/东方证券_009/iDStd_afterProcess'
columns = pd.Series(data.columns.tolist())

funStart = 0


def describe(data, type='show', path=''):
    '''描述性统计'''
    # 计算描述性统计量
    summary = data.stack().describe()

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

    # 根据所选类型进行操作
    if type == 'show':
        print(summary)
        plt.show()
    elif type == 'save':
        if not os.path.exists(path): os.makedirs(path)
        figurePDF.savefig('{}/PDF.png'.format(path), dpi=400)
        summary.to_csv('{}/summary.csv'.format(path))


def winsorize(column, type='Boxplot', times=5, threshold=0.1, scope=3):
    '''去极值'''
    # 采用固定比例法去极值，即将头尾某一固定比例的极值去除
    if type == 'FixRate':
        dataColumn = data[column].dropna()
        if not dataColumn.empty:
            min = dataColumn.quantile(threshold / 2)
            max = dataColumn.quantile(1 - threshold / 2)
            afterWinsorize = np.clip(dataColumn, min, max)
        else:
            afterWinsorize = pd.Series()
        # 显示当前进度
        index = columns[columns == column].index.tolist()[0]
        funcPerc = len(columns[: index]) / len(columns)
        fun.processing_bar(funcPerc, funStart)
        return afterWinsorize

    # 采用均值方差法去极值，即假定因子在截面上服从正态分布，去除超过均值上下一定比例标准差的数值
    elif type == 'MeanStd':
        dataColumn = data[column].dropna()
        if not dataColumn.empty:
            afterWinsorize = dataColumn; NofTime = 0
            while NofTime < times:
                min = dataColumn.mean() - scope * dataColumn.std()
                max = dataColumn.mean() + scope * dataColumn.std()
                afterWinsorize = np.clip(afterWinsorize, min, max)
                NofTime += 1
        else:
            afterWinsorize = pd.Series()
        # 显示当前进度
        index = columns[columns == column].index.tolist()[0]
        funcPerc = len(columns[: index]) / len(columns)
        fun.processing_bar(funcPerc, funStart)
        return afterWinsorize

    # 采用中值绝对偏差法去极值
    elif type == 'MAD':
        dataColumn = data[column].dropna()
        if not dataColumn.empty:
            afterWinsorize = dataColumn; NofTime = 0
            while NofTime < times:
                median = dataColumn.median()
                MAD = (dataColumn - median).abs().median()
                min = median - scope * (1.483 * MAD)
                max = median + scope * (1.483 * MAD)
                afterWinsorize = np.clip(afterWinsorize, min, max)
                NofTime += 1
        else:
            afterWinsorize = pd.Series()
        # 显示当前进度
        index = columns[columns == column].index.tolist()[0]
        funcPerc = len(columns[: index]) / len(columns)
        fun.processing_bar(funcPerc, funStart)
        return afterWinsorize

    # 采用Boxplot法去极值
    elif type == 'Boxplot':
        dataColumn = data[column].dropna()
        if not dataColumn.empty:
            afterWinsorize = dataColumn; NofTime = 0
            while NofTime < times:
                IQR = dataColumn.quantile(0.75) - dataColumn.quantile(0.25)
                median, medCouple = dataColumn.median(), medcouple(dataColumn)
                if medCouple >= 0:
                    min = dataColumn.quantile(0.25) - 1.5 * np.exp(-3.5 * medCouple) * IQR
                    max = dataColumn.quantile(0.75) + 1.5 * np.exp(4 * medCouple) * IQR
                elif medCouple < 0:
                    min = dataColumn.quantile(0.25) - 1.5 * np.exp(-4 * medCouple) * IQR
                    max = dataColumn.quantile(0.75) + 1.5 * np.exp(3.5 * medCouple) * IQR
                afterWinsorize = np.clip(afterWinsorize, min, max)
                NofTime += 1
        else:
            afterWinsorize = pd.Series()
        # 显示当前进度
        index = columns[columns == column].index.tolist()[0]
        funcPerc = len(columns[: index]) / len(columns)
        fun.processing_bar(funcPerc, funStart)
        return afterWinsorize


def neutralize(column):
    '''中性化'''
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
        afterNeutralize = resid
    else:
        afterNeutralize = pd.Series()
    # 显示当前进度
    index = columns[columns == column].index.tolist()[0]
    funcPerc = len(columns[: index]) / len(columns)
    fun.processing_bar(funcPerc, funStart)
    return afterNeutralize


def normalize(column):
    '''正态化'''
    # 获取lambda均值
    lambdas = OrderedDict()
    dataColumn = data[column].dropna()
    if not dataColumn.empty:
        afterBoxCox, lambdas[column] = stats.boxcox(dataColumn)
    else:
        lambdas[column] = np.nan
    lambdaMean = pd.Series(lambdas).mean()
    # 进行数据处理
    dataColumn = data[column].dropna()
    if not dataColumn.empty:
        afterBoxCox = pd.Series(stats.boxcox(dataColumn, lambdaMean))
        afterBoxCox.index = dataColumn.index
        afterNormalize = afterBoxCox
    else:
        afterNormalize = pd.Series()
    # 显示当前进度
    index = columns[columns == column].index.tolist()[0]
    funcPerc = len(columns[: index]) / len(columns)
    fun.processing_bar(funcPerc, funStart)
    return afterNormalize


def standardize(column):
    '''标准化'''
    # 进行数据处理
    dataColumn = data[column].dropna()
    if not dataColumn.empty:
        mean, std = dataColumn.mean(), dataColumn.std()
        afterStandardize = (dataColumn - mean) / std
    else:
        afterStandardize = pd.Series()
    # 显示当前进度
    index = columns[columns == column].index.tolist()[0]
    funcPerc = len(columns[: index]) / len(columns)
    fun.processing_bar(funcPerc, funStart)
    return afterStandardize


if __name__ == '__main__':

    describe(data, type='save', path='{}/describe/original'.format(path))

    # 计算程序运行时间
    print('\n去极值计算开始')
    funStart = time.perf_counter()
    # 去极值计算
    afterWinsorize = OrderedDict()
    with ProcessPoolExecutor() as pool:
        results = pool.map(winsorize, columns)
        results = list(zip(columns, results))
    for column, result in results:
        afterWinsorize[column] = result
    afterWinsorize = pd.DataFrame(afterWinsorize)
    # 提示程序计算完成
    print('\n去极值计算完成')

    describe(afterWinsorize, type='save', path='{}/describe/afterWinsorize'.format(path))

    # 计算程序运行时间
    print('\n中性化计算开始')
    funStart = time.perf_counter()
    # 去极值计算
    afterNeutralize = OrderedDict()
    with ProcessPoolExecutor() as pool:
        results = pool.map(neutralize, columns)
        results = list(zip(columns, results))
    for column, result in results:
        afterNeutralize[column] = result
    afterNeutralize = pd.DataFrame(afterNeutralize)
    # 提示程序计算完成
    print('\n中性化计算完成')

    describe(afterNeutralize, type='save', path='{}/describe/afterNeutralize'.format(path))

    # 计算程序运行时间
    print('\n正态化计算开始')
    funStart = time.perf_counter()
    # 去极值计算
    afterNormalize = OrderedDict()
    with ProcessPoolExecutor() as pool:
        results = pool.map(normalize, columns)
        results = list(zip(columns, results))
    for column, result in results:
        afterNormalize[column] = result
    afterNormalize = pd.DataFrame(afterNormalize)
    # 提示程序计算完成
    print('\n正态化计算完成')

    describe(afterNormalize, type='save', path='{}/describe/afterNormalize'.format(path))

    # 计算程序运行时间
    print('\n标准化计算开始')
    funStart = time.perf_counter()
    # 去极值计算
    afterStandardize = OrderedDict()
    with ProcessPoolExecutor() as pool:
        results = pool.map(standardize, columns)
        results = list(zip(columns, results))
    for column, result in results:
        afterStandardize[column] = result
    afterStandardize = pd.DataFrame(afterStandardize)
    # 提示程序计算完成
    print('\n标准化计算完成')

    describe(afterStandardize, type='save', path='{}/describe/afterStandardize'.format(path))

    afterStandardize.to_csv(path)
