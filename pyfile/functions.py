# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 21:59:37 2018

@author: Administrator
"""

import datetime


def gain_nowtime():
    "获取当前日期"
    return datetime.datetime.now().strftime('%Y-%m-%d')


def text1():
    return "\n00:00~06:00(1)\t06:00~09:00(2)\n09:00~12:00(3)\
\t12:00~15:00(4)\n15:00~18:00(5)\t18:00~21:00(6)\n21:00~23:59(7)\n\
Tell me when would you like to START most(SECRET: \nmost people \
choose to type '34', you can also type numbers separated by SPACE \
like '3 4'), type your number: "
                                      
def text2():
    return "G/D\t\t\tT/Z/.etc\n\
Select one('1' for the left one and '2' for the right one, OR ignore): "


def get_fromstationname():
    return input("Where shall you START your travel(eg: '北京'): ")

def get_tostationname():
    return input("And the Destination(eg: '上海'): ")

def get_trainstartingdate():
    dateNow = gain_nowtime()
    yearNow = dateNow[0:5]# 2018-
    return yearNow + input('When to go(FORMAT: ' + dateNow + '): ' + yearNow)


def judge_begin_end(dataframe, cols, val):
    "判断是出发还是到达"
    a = dataframe[dataframe[cols] == val].index.tolist()# 无论输入，返回均为空？
    return [True, False][a == []]

def is_fast(dataframe, trainNum):
    "根据车次首字母判断是否为快速列车，返回bool列表"
    newList = []
    for x in dataframe[trainNum]:
        x = x.lower()
        newList.append([False, True][('c' in x) | ('g' in x) | ('d' in x)])
    return newList

def gain_userinteraction(s, defaultPara):
    while True:
        para1 = input(s)
        if para1 == '':
            para1 = defaultPara
        para1 = ''.join(para1.split())# 空格统统去掉
        if para1.isdecimal():# isalnum()意思是判断是否为数字或字母 BUG/输错了，比如超出阈值
            break
        print('Please type a numberic thing!!')
        print('One more chance: ')
    return para1



    
    
