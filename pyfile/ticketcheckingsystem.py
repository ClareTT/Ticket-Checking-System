# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 16:27:01 2018
Update on Tuesday Nov 27 18:01:39 2018

@author: llwang
"""

import requests
import json
import pandas as pd
import numpy as np
from functools import reduce

from functions import get_trainstartingdate
from functions import get_fromstationname
from functions import get_tostationname
from functions import is_fast
from functions import text1
from functions import text2
from functions import gain_userinteraction
from functions import judge_begin_end

# https://www.cnblogs.com/yanfengt/p/6305542.html 全局变量的引用和修改
stationNameMapping = pd.read_csv('themappingfile.csv')
stationNameMapping.columns = ['charactor', 'alpha']
stationNameMapping.index = stationNameMapping.charactor


class TicketCheckingSystem(object):
    "define a class of ticket checking system."
    def __init__(self):
        self.results = self.get_rawinformation()
        self.mapdata = self.results['data']['map']
        self.informationTotal = self.get_traininformation()
        self.parameter = self.generate_filteruserselect()
        self.condition = self.generate_filterboolcolumn()
        
    def print_successinformation(self):
        print('\nInformation has been collected successfully!')
        print("\n1. 出发时间\t\t2. 到达时间\t\t3. 高速/普通\n\
4. 出发站\t\t5. 到达站\n\nFiltering...")
    
    def get_rawinformation(self):
        """
        The first STEP, get train information:
            1. get the query URL
            2. crawl information
        """
        
        url = self.get_queryurl()
        r = requests.get(url)
        results = json.loads(r.content)
        return results
        

    
    def get_queryurl(self):
        """
        获取查询存放数据url
        
        eg：from_station_name = '北京'，to_station_name = '上海'
        train_date格式为2018-10-05
                
        To get the query URL:
            1. we get user interaction information
            2. generate query URL and return
        """

        from_station = stationNameMapping.loc[get_fromstationname(), 'alpha']
        to_station = stationNameMapping.loc[get_tostationname(), 'alpha']
        queryUrl = "https://kyfw.12306.cn/otn/leftTicket/query?\
leftTicketDTO.train_date={}&leftTicketDTO.from_station={}\
&leftTicketDTO.to_station={}&purpose_codes=ADULT\
".format (get_trainstartingdate(), from_station, to_station)# 该URL通过browser抓包得到，会变化，及时更新
        return queryUrl

        # 2018年10月11日'...queryA?...'>>>'...queryO?...'
        # 2018年11月27日'...queryO?...'>>>'...query?...'

    
    def get_traininformation(self):
        """
        获取车次信息等
        
        To get train information:
            1. we extract useful information from raw information
            2. set index and columns
            3. add new column of mapped station name(in Chinese)
            4. add new column of if the station is the very begining or end
            4. add new column of if the train is the fast or an ordinary one
        
        """
        results = self.results
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
        
        informationTotal['isFast'] = is_fast(informationTotal, 'TrainNum')
        informationTotal['isSlow'] = [not(x) for x in informationTotal.isFast]
        
        return informationTotal
    
    

    
    def generate_filterboolcolumn(self):
        """
        根据用户输入信息获取筛选条件
        To get filter condition:
            1. we get condition name: para1, para2, para3, ...
            2. we get each column of boolean data
            3. we combine every condition boolean column
        
        """
        para1 = self.parameter[0]
        para2 = self.parameter[1]
        para3 = self.parameter[2]
        para4 = self.parameter[3]
        
        conditionRegular = self.informationTotal.isAvailable == 'Y'
        
        conditionTimeBegin = self.generate_timesegmentation('beginTime')
        conditionTimeEnd = self.generate_timesegmentation('endTime')
        
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
            conditionFastOrdinary = conditionFastOrdinary | self.informationTotal['is' + sCat]
        # 车站筛选
        if para4[2] == 1:
            conditionstation = pd.Series([True]*len(conditionTimeEnd))
        else:
            conditionstation = self.informationTotal[para4[0]] == para4[1]
        
        # 筛选条件列表
        conditionList = [conditionBegin, conditionEnd, conditionFastOrdinary, 
                         conditionstation, conditionRegular]
        condition = reduce(lambda x, y:x & y, conditionList)# 所有筛选条件取与
        
        return condition

    def generate_timesegmentation(self, beginEnd):
        conditionTime1 = (self.informationTotal[beginEnd] >= '00:00') & \
        (self.informationTotal[beginEnd] <= '06:00')# 筛选条件1：时间段00：00~06：00
        conditionTime2 = (self.informationTotal[beginEnd] > '06:00') & \
        (self.informationTotal[beginEnd] <= '09:00')# 和筛选条件1互斥
        conditionTime3 = (self.informationTotal[beginEnd] > '09:00') & \
        (self.informationTotal[beginEnd] <= '12:00')# 和筛选条件1互斥
        conditionTime4 = (self.informationTotal[beginEnd] > '12:00') & \
        (self.informationTotal[beginEnd] <= '15:00')# 和筛选条件1互斥
        conditionTime5 = (self.informationTotal[beginEnd] > '15:00') & \
        (self.informationTotal[beginEnd] <= '18:00')# 和筛选条件1互斥
        conditionTime6 = (self.informationTotal[beginEnd] > '18:00') & \
        (self.informationTotal[beginEnd] <= '21:00')# 和筛选条件1互斥
        conditionTime7 = (self.informationTotal[beginEnd] > '21:00') & \
        (self.informationTotal[beginEnd] <= '23:59')# 和筛选条件1互斥
        
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
    

    
    def generate_filteruserselect(self):
        
        
        para1 = gain_userinteraction(text1(), '1234567')
        para3 = gain_userinteraction(text2(), '12')
        dfMap = self.generate_dfmap()
        self.print_stationselect()
        while True:
            flag = 0
            para4_station = input("Press one station: ").upper()
            if para4_station == '':
                para4_station = dfMap.iat[0, 0]
                flag = 1
            try:
                val = self.mapdata[para4_station]
                break
            except:
                print('Error!! Please type again: ')
        col = ['endName_map', 'beginName_map'][judge_begin_end(dfMap, '出发', val)]# 有问题
        para4 = [col, val, flag]
        
        parameter = [para1, '1234567', para3, para4]
        
        return parameter
        
    def generate_beginlist(self):
        beginList = self.get_beginlist()
        return beginList
    def generate_endlist(self):
        endList = self.get_endlist()
        return endList
    
    
    def generate_dfmap(self):
        beginList = self.generate_beginlist()
        endList = self.generate_endlist()
        dfMap = pd.DataFrame({'出发':beginList})
        dfMap = dfMap.append(pd.DataFrame({'到达':endList}))
              
        return dfMap
    
    def print_stationselect(self):
        beginList = self.generate_beginlist()
        endList = self.generate_endlist()
        print('出发'.center(13, '-'))
        for x in beginList:
            print(x.ljust(3) + '|' + self.mapdata[x].ljust(10))
        print('到达'.center(13, '-'))
        for x in endList:
            print(x.ljust(3) + '|' + self.mapdata[x].ljust(10))
    
    def get_beginlist(self):
        "得到该次搜索出发/到达车站名字列表"
        beginList = []
        for x in self.informationTotal['beginName']:
            if (x not in beginList):
                beginList = beginList + [x]
        return beginList
    
    def get_endlist(self):
        "得到该次搜索出发/到达车站名字列表"
        endList = []
        for x in self.informationTotal['endName']:
            if (x not in endList):
                endList = endList + [x]
        return endList
    
    def get_filtereddata(self):
        columnNeeded = ['TrainNum', 'beginName_map', 'endName_map', 'beginTime', 
                    'endTime', 'diffTime', 'yw', 'yz', 'wz', 'erd', 'yd', 'sw']
        columnNeededMap = ['车次', '出发', '到达', '出发时', 
                        '到达时', '历时', '硬卧', '硬座', '无座', '二等', '一等', '商务']
        filteredData = pd.DataFrame()
        filteredData[columnNeededMap] = self.informationTotal.loc[self.condition, columnNeeded]
        return filteredData
    
    def print_result(self, filteredData):
        
        lstation = len(max([x for x in stationNameMapping.iloc[:,0]], key = len))
        
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
                print(filteredData.iat[i, 1].center(lstation), end = '|')
                print(filteredData.iat[i, 2].center(lstation), end = '|')
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
                
                
                
    def print_catalog(self):
        a = input("Press Enter to search new routine. \n(E)exit system\n")
        return [False, True]['e' in a.lower()]


if __name__ == '__main__':

    while True:
        ticket = TicketCheckingSystem()
        
        try:
            
            ticket.print_successinformation()
            
            filteredData = ticket.get_filtereddata()
            
            ticket.print_result(filteredData)
        except Exception as e:
            print(Exception,':',e)
            print('\nNetwork connection Error, Please check your network!')
            
        if ticket.print_catalog():
            print('Thanks for using!')
            break


            
    