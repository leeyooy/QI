# -*- encoding: utf-8 -*-
'''
Filename         :basicFunction.py
Description      :该模块用于提供一些基础的功能函数
Time             :2021/06/25 11:47:58
Author           :量化投资1组
Version          :1.0
'''

import time


def processing_bar(perc, start):
    """进度条函数，通过输入函数开始时间与当前执行百分比显示函数执行进度

    Args:
        perc (float): 目标函数的运行进度
        start (time): 目标函数开始运行的时间。在目标函数的开头插入start = time.perf_counter()，该函数会自动计算执行时间。
    """
    scale = 50
    number = int(perc * scale)
    done = "*" * number
    remain = "." * (scale - number)
    dur = time.perf_counter() - start
    print("\r{:^3.0f}%[{}->{}]{:.2f}s".format(perc * 100, done, remain, dur), end="")


def extract_samePart(list1, list2):
    set1, set2 = set(list1), set(list2)
    samePart = set1.intersection(set2)
    return list(samePart)
