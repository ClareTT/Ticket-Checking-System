# -*- coding: utf-8 -*-
"""
Created on Sun Oct  7 20:47:48 2018

@author: Administrator
"""

import re
import requests
import pandas as pd


if __name__ == '__main__':
    
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9066'
    r = requests.get(url)
    quoets = re.findall(u'([\u4e00-\u9fa5]+)\|([A-Z]+)', r.text)# Match at least one Chinese character or one upper letter
    dataframe = pd.DataFrame(quoets)
    # write data to .csv file
    dataframe.to_csv('themappingfile.csv', index = False, sep = ',', encoding = 'utf_8_sig')
    # read data from .csv file
    df = pd.read_csv('themappingfile.csv')# The type of 'df' is 'DataFrame'