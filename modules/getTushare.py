import numpy as np
import pandas as pd
import tushare as ts
from collections import OrderedDict
import time
import basicFunction as fun


'''从tushare获取股票数据'''
def csv2npy(stats, stockList):
    dataOriginal = OrderedDict()

    # 从csv中提取数据
    print('\n数据提取开始')
    funStart, number = time.perf_counter(), 0
    for stockID in stockList:
        # 提取数据
        filePath = 'newdata/csv/{}.csv'.format(stockID)
        dataOriginal[stockID] = pd.read_csv(filePath).set_index('trade_date')
        # 显示当前进度
        number += 1
        funcPerc = number / len(stockList)
        fun.processing_bar(funcPerc, funStart)
    print('\n数据提取完成')

    for stat in stats:
        data = OrderedDict()
        print('\n数据{}整理开始'.format(stat))
        funStart, number = time.perf_counter(), 0
        for stockID in stockList:
            data[stockID] = dataOriginal[stockID][stat]
            # 显示当前进度
            number += 1
            funcPerc = number / len(stockList)
            fun.processing_bar(funcPerc, funStart)
        data = pd.DataFrame(data)
        data = np.array(data)
        np.save('newdata/{}.npy'.format(stat), data)
        print('\n数据{}整理完成'.format(stat))


beginDate = '20050101'
endDate = '20210531'

token = '0846d4165aebfdaf92a38b07d829f15d32c31697e62d1b24bd1ba528'
pro = ts.pro_api(token)

indexInfos = pd.read_csv('data/index/indexInfos.csv')
codes = indexInfos['ts_code']

'''
for code in codes:
    data = pro.index_daily(ts_code=code, start_date=beginDate, end_date=endDate)
    path = 'newdata/csv/{}.csv'.format(code)
    data.to_csv(path)
'''

stats = ['close', 'open', 'high', 'low', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']

codes = np.array(codes)
print(codes)
np.save('data/index/indexList.npy', codes)

'''


header = ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
data

indexList = ['MSCI', 'CSI', 'SSE', 'SZSE', 'CICC', 'SW', 'OTH']
indexList = ['000002.SH','000003.SH','399006.SZ','399102.SZ','000159.SH','000300.SH','000010.SH','000009.SH','000001.SH','399001.SZ',
             '399106.SZ','000188.CSI','399005.SZ','399101.SZ','000852.SH','000906.SH','000905.SH','000139.SH','000832.CSI']
header = ['ts_code', 'name', 'market', 'publisher', 'category', 'base_date', 'base_point', 'list_date']
dataTotal = pd.DataFrame(columns=header)

for index in indexList:
    data = pro.index_basic(ts_code=index)
    dataTotal = pd.concat([dataTotal, data])

dataTotal = dataTotal.reset_index().drop(['index'], axis=1)
dataTotal.to_csv('newdata/indexInfos.csv', encoding='utf-8-sig')

print(dataTotal)

'''














'''

stockTradeDate = np.load('data/stockTradeDate.npy')
stockTradeDate = pd.Series(stockTradeDate.flatten())

dataOriginal = OrderedDict()



stats = ['turnover_rate', 'turnover_rate_f', 'volume_ratio', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm',
         'dv_ratio', 'dv_ttm', 'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv']

'''