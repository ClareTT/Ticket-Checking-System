# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 16:27:01 2018

@author: llwang
"""

import requests
import json
import pandas as pd
import datetime
import numpy as np
from functools import reduce

    
class ticketcheckingsystem(object):
    "define a class of ticket checking system."
    def __init__(self, name):
        self.name = name
        
    def gain_nowtime(self):
        "获取当前日期"
        return datetime.datetime.now().strftime('%Y-%m-%d')
        
    def fromStationName(self):
        return input("Where shall you START your travel(eg: '北京'): ")
    
    def toStationName(self):
        return input("And the Destination(eg: '上海'): ")
    
    def traindate(self):
        dateNow = self.gain_nowtime()
        yearNow = dateNow[0:5]# 2018-
        return yearNow + input('When to go(FORMAT: ' + dateNow + '): ' + yearNow)
    
    def text1(self):
        return "\n00:00~06:00(1)\t06:00~09:00(2)\n09:00~12:00(3)\
\t12:00~15:00(4)\n15:00~18:00(5)\t18:00~21:00(6)\n21:00~23:59(7)\n\
Tell me when would you like to START most(SECRET: \nmost people \
choose to type '34', you can also type numbers separated by SPACE \
like '3 4'), type your number: "
                                          
    def text2(self):
        return "G/D\t\t\tT/Z/.etc\n\
Select one('1' for the left one and '2' for the right one, OR ignore): "
    
    def gotmap(self, cols, informationTotal):
        "得到该次搜索出发/到达车站名字列表"
        beginList = []
        for x in informationTotal[cols]:
            if (x not in beginList):
                beginList = beginList + [x]
        return beginList
    
    def isbegin_end(self, dataframe, cols, val):
        "判断是出发还是到达"
        a = dataframe[dataframe[cols] == val].index.tolist()
        return [True, False][a == []]

    def isfast(self, dataframe, trainNum):
        "根据车次首字母判断是否为快速列车，返回bool列表"
        newList = []
        for x in dataframe[trainNum]:
            x = x.lower()
            newList.append([False, True][('c' in x) | ('g' in x) | ('d' in x)])
        return newList

    def gain_userInteraction(self, s, defaultPara):
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
    
    def gain_urlchecking(self, station, from_station_name, to_station_name, train_date):
        """
        获取查询存放数据url
        
        eg：from_station_name = '北京'，to_station_name = '上海'
        train_date格式为2018-10-05
        """
        

        station.columns = ['charactor', 'alpha']
        station.index = station.charactor
        from_station = station.loc[from_station_name, 'alpha']
        to_station = station.loc[to_station_name, 'alpha']
        return "https://kyfw.12306.cn/otn/leftTicket/queryO?\
leftTicketDTO.train_date={}&leftTicketDTO.from_station={}\
&leftTicketDTO.to_station={}&purpose_codes=ADULT\
".format (train_date, from_station, to_station)# 该URL通过browser抓包得到，会变化，及时更新
        # 2018年10月11日'...queryA?...'>>>'...queryO?...'


    
    def gain_information(self, results):
        "获取车次信息等"
        
        informationTotal = pd.DataFrame()
        for i in results['data']['result']:
            infoEach = i.split('|')
            gjr = infoEach[21]
            rw = infoEach[23]
            wz = infoEach[26]
            yw = infoEach[28]
            yz = infoEach[29]
            erd = infoEach[30]
            yd = infoEach[31]
            sw = infoEach[32]
            tw = infoEach[33]
            
            seatType = [gjr, rw, wz, yw, yz, erd, yd, sw, tw]
            
            numOfTrain = infoEach[3]
            beginCity = infoEach[4]
            endCity = infoEach[5]
            beginName = infoEach[6]
            endName = infoEach[7]
            beginTime = infoEach[8]
            endTime = infoEach[9]
            diffTime = infoEach[10]
            isAvailable = infoEach[11]
            dateOfTrain = infoEach[13]
            
            infoList = [[numOfTrain, beginCity, endCity,
                         beginName, endName, beginTime, 
                         endTime, diffTime, isAvailable, 
                         dateOfTrain] + seatType]# 此处将列表外加中括号对，变成1行n列的数组
            information = pd.DataFrame(infoList)
            informationTotal = informationTotal.append(information, ignore_index = True)
         
        columnSeat = ['gjr', 'rw', 'wz', 'yw', 'yz', 'erd', 'yd', 'sw', 'tw']
        column = ['TrainNum', 'beginCity', 'endCity', 
                  'beginName', 'endName', 'beginTime',
                  'endTime', 'diffTime', 'isAvailable', 'date'] + columnSeat
        
        informationTotal.index = range(1, len(informationTotal) + 1)
        informationTotal.columns = column
        
        for i in columnSeat:
            informationTotal.loc[informationTotal[i] == '', i] = '-'
            
        sourceColumns = ['beginName', 'endName']
        newColumns = [str(x) + '_map' for x in sourceColumns]
        # newColumns = ['beginName_map', 'endName_map']
        mapData = results['data']['map']
        informationTotal[newColumns] = informationTotal[sourceColumns].applymap(mapData.get)
        
        informationTotal['isVeryBegin'] = np.where(informationTotal['beginCity'] 
                       == informationTotal['beginName'], True, False)
        informationTotal['isVeryEnd'] = np.where(informationTotal['endCity'] 
                       == informationTotal['endName'], True, False)
        
        informationTotal['isFast'] = self.isfast(informationTotal, 'TrainNum')
        informationTotal['isSlow'] = [not(x) for x in informationTotal.isFast]
        
        return (mapData, informationTotal)
    
    
    def gain_conditionTime(self, beginEnd, informationTotal):
        conditionTime1 = (informationTotal[beginEnd] >= '00:00') & \
        (informationTotal[beginEnd] <= '06:00')# 筛选条件1：时间段00：00~06：00
        conditionTime2 = (informationTotal[beginEnd] > '06:00') & \
        (informationTotal[beginEnd] <= '09:00')# 和筛选条件1互斥
        conditionTime3 = (informationTotal[beginEnd] > '09:00') & \
        (informationTotal[beginEnd] <= '12:00')# 和筛选条件1互斥
        conditionTime4 = (informationTotal[beginEnd] > '12:00') & \
        (informationTotal[beginEnd] <= '15:00')# 和筛选条件1互斥
        conditionTime5 = (informationTotal[beginEnd] > '15:00') & \
        (informationTotal[beginEnd] <= '18:00')# 和筛选条件1互斥
        conditionTime6 = (informationTotal[beginEnd] > '18:00') & \
        (informationTotal[beginEnd] <= '21:00')# 和筛选条件1互斥
        conditionTime7 = (informationTotal[beginEnd] > '21:00') & \
        (informationTotal[beginEnd] <= '23:59')# 和筛选条件1互斥
        
        columnTime = ['con1', 'con2', 'con3', 'con4', 'con5', 'con6', 'con7']
        conditionTime = pd.DataFrame(list(zip(conditionTime1, 
                                                   conditionTime2, 
                                                   conditionTime3, 
                                                   conditionTime4, 
                                                   conditionTime5, 
                                                   conditionTime6, 
                                                   conditionTime7)))
        conditionTime.columns = columnTime
        
        return conditionTime
    
    def gain_condition(self, informationTotal, para1, para2, para3, para4):
        "根据用户输入信息获取筛选条件"
        conditionRegular = informationTotal.isAvailable == 'Y'
        
        conditionTimeBegin = self.gain_conditionTime('beginTime', informationTotal)
        conditionTimeEnd = self.gain_conditionTime('endTime', informationTotal)
        
        # 发车时间段筛选条件，根据用户的输入动态调整
        conditionBegin = pd.Series([False]*len(conditionTimeBegin))
        for s in list(para1):
            conditionBegin = conditionBegin | conditionTimeBegin['con' + s]
        # 到达时间筛选    
        conditionEnd = pd.Series([False]*len(conditionTimeEnd))
        for s in list(para2):
            conditionEnd = conditionEnd | conditionTimeEnd['con' + s]
        # 普通车/高速筛选条件
        conditionFastOrdinary = pd.Series([False]*len(conditionTimeEnd))
        for s in list(para3):
            sCat = ['Slow', 'Fast'][s == '1']
            conditionFastOrdinary = conditionFastOrdinary | informationTotal['is' + sCat]
        # 车站筛选
        if para4[2] == 1:
            conditionStation = pd.Series([True]*len(conditionTimeEnd))
        else:
            conditionStation = informationTotal[para4[0]] == para4[1]
        
        # 筛选条件列表
        conditionList = [conditionBegin, conditionEnd, conditionFastOrdinary, 
                         conditionStation, conditionRegular]
        condition = reduce(lambda x, y:x & y, conditionList)# 所有筛选条件取与
        
        return condition

    def gotinfo(self, station):
        url = self.gain_urlchecking(station, self.fromStationName(), self.toStationName(), self.traindate())
        r = requests.get(url)
        results = json.loads(r.content)
        return self.gain_information(results)
    
    def printinfo(self):
        print('\nInformation has been collected successfully!')
        print("\n1. 出发时间\t\t2. 到达时间\t\t3. 高速/普通\n\
4. 出发站\t\t5. 到达站\n\nFiltering...")
    
    def gotcondition(self, informationTotal, mapdata):
        
        para1 = self.gain_userInteraction(self.text1(), '1234567')
        para3 = self.gain_userInteraction(self.text2(), '12')
        
        beginList = self.gotmap('beginName', informationTotal)
        endList = self.gotmap('endName', informationTotal)
        dfMap = pd.DataFrame({'出发':beginList})
        dfMap = dfMap.append(pd.DataFrame({'到达':endList}))
        
        print('出发'.center(13, '-'))
        for x in beginList:
            print(x.ljust(3) + '|' + mapdata[x].ljust(10))
        print('到达'.center(13, '-'))
        for x in endList:
            print(x.ljust(3) + '|' + mapdata[x].ljust(10))
        
        while True:
            flag = 0
            para4_station = input("Press one station: ").upper()
            if para4_station == '':
                para4_station = dfMap.iat[0, 0]
                print(para4_station)
                flag = 1
            try:
                val = mapdata[para4_station]
                break
            except:
                print('Error!! Please type again: ')
        col = ['endName_map', 'beginName_map'][self.isbegin_end(dfMap, '出发', val)]
        para4 = [col, val, flag]
        
        
        return self.gain_condition(informationTotal, para1, 
                                   '1234567', 
                                   para3, 
                                   para4)
        
    def gotfilter(self, condition, informationTotal):
        columnNeeded = ['TrainNum', 'beginName_map', 'endName_map', 'beginTime', 
                    'endTime', 'diffTime', 'yw', 'yz', 'wz', 'erd', 'yd', 'sw']
        columnNeededMap = ['车次', '出发', '到达', '出发时', 
                        '到达时', '历时', '硬卧', '硬座', '无座', '二等', '一等', '商务']
        filteredData = pd.DataFrame()
        filteredData[columnNeededMap] = informationTotal.loc[condition, columnNeeded]
        return filteredData
    
    def printresult(self, filteredData, station):
        
        lStation = len(max([x for x in station.iloc[:,0]], key = len))
        
        if filteredData.empty:
            print('\nSorry~ There is no train left, try other filter combinations: ')
        else:
            p = len(filteredData)
            print('\nCongratulation! There is ' + str(p) + 
                  [' trains.', ' train.'][p == 1])
            print(filteredData.columns[0].center(2,'-') + '|' # 车次
                  + filteredData.columns[1].center(2,'-') + '|' # 出发
                  + filteredData.columns[2].center(2,'-') + '|' # 到达
                  + filteredData.columns[3].center(3,'-') + '|' # 出发时
                  + filteredData.columns[4].center(3,'-') + '|' # 到达时
                  + filteredData.columns[5].center(2,'-') + '|' # 历时
                  + filteredData.columns[6].center(2,'-') + '|' #硬卧 天啦噜，汉字也算一个字符
                  + filteredData.columns[7].center(2,'-') + '|' 
                  + filteredData.columns[8].center(2,'-') + '|' 
                  + filteredData.columns[9].center(2,'-') + '|' 
                  + filteredData.columns[10].center(2,'-') + '|' 
                  + filteredData.columns[11].center(2,'-') + '|' )
            for i in range(len(filteredData)):
                print(filteredData.iat[i, 0].ljust(5), end = '|')
                print(filteredData.iat[i, 1].center(lStation), end = '|')
                print(filteredData.iat[i, 2].center(lStation), end = '|')
                print(filteredData.iat[i, 3].center(5), end = '|')
                print(filteredData.iat[i, 4].center(5), end = '|')
                print(filteredData.iat[i, 5].center(5), end = '|')
                print(filteredData.iat[i, 6].center(1), end = '|')
                print(filteredData.iat[i, 7].center(1), end = '|')
                print(filteredData.iat[i, 8].center(1), end = '|')
                print(filteredData.iat[i, 9].center(1), end = '|')
                print(filteredData.iat[i, 10].center(1), end = '|')
                print(filteredData.iat[i, 11].center(1), end = '|')
                print()
                
    def printcatalog(self):
        a = input("Press Enter to search new routine. \n(E)exit system\n")
        return [False, True]['e' in a.lower()]

if __name__ == '__main__':
    station = pd.read_csv('themappingfile.csv')
    while True:
        ticket = ticketcheckingsystem('Clare')
        
        try:
            mapdata, informationTotal = ticket.gotinfo(station)
            
            ticket.printinfo()
        
            filteredData = ticket.gotfilter(ticket.gotcondition(informationTotal, mapdata), informationTotal)
            
            ticket.printresult(filteredData, station)
        except Exception as e:
            print(Exception,':',e)
            print('\nNetwork connection Error, Please check your network!')
            
        if ticket.printcatalog():
            print('Thanks for using!')
            break


            
    