### The method to capture packet and to know well about the website routine of *[12306.cn](#12306.cn)*
First, we can use the developer tools of Chorme browser to capture packet on the purpose of finding data.   
![shootimg1](/image/packetcapture12306.PNG "packet capture")  
Click the first one, then we can catch an interesting URL, and the reason why it is interesting is the URL seems to have a lot of familier characters like **`2018-10-08`** , **`from_station`**, **`to_station`**, **`ADULT`**. That is the difference between other messy code. Actually, the 4 variables before the assignment symbol '=' representing *the date you select*, *the station you start your trip*, *you end your trip* and *the type of the ticket: 'adult'* respectively.  
![shootimg2](/image/urlget.PNG "got a URL")  
```
https://kyfw.12306.cn/otn/leftTicket/queryA?leftTicketDTO.train_date=2018-10-08&leftTicketDTO.from_station=BJP&leftTicketDTO.to_station=SHH&purpose_codes=ADULT
```
Then we copy the URL see what happend in there:  
```
{"data":{"flag":"1","map":{"AOH":"上海虹桥","BJP":"北京","SHH":"上海","VNP":"北京南"},"result":["|预订|240000G1010F|G101|VNP|AOH|VNP|AOH|06:43|12:40|05:57|N|iaSVq15uuXPnU8K6j%2F3U6282aflCCRyKWCVKO9LQtV%2FOOY3wUeWKMUZSPi8%3D|20181008|3|P2|01|11|1|0|||||||无||||无|无|无||O090O0M0|O9OM|0","pMBGX3CwVvaOgL2p0C%2Ba4OhdRtVCnKKbM6PJC4O1ml7MCnAva1vJzFMd5UIfJE2V4miarHoEIcsr%0Ay0k%2BndX2WvWSx%2Fv7y12WCmg%2B2eyt%2BARunLkHjyMT7XWfxbzgBgEOxxNIpGbJH8MfBL%2F8jT17QTiz%0Aa8%2FTlkDS2%2FLwwDEcG0tK4OesOgYO5mDxmyn6jG7MK2rj5WlieiSQPKOn5BXo8GNwYM48Kcpd9kDM%0A4yHwMmcvwiSaJ%2FF20maPP7s35NM1gf9kjw%3D%3D|预订|240000G1032H|G103|VNP|AOH|VNP|AOH|06:53|12:48|05:55|Y|JD55P%2BXuL34kX7B%2F4R%2F4lcSEMYsxrFy895WLEj4qVreJjqhv|20181008|3|P3|01|10|1|0|||||||||||1|无|无||O0M090|OM9|0","RjuXrpVVDVB4liMESHEoJtV3cPWFx4%2BEsiGTmPq4wWUJRU%2FytnZne2X%2F7AiBrdzaMD7o1qpZNR8b%0ARKGWanuXcnmuq3HeI4R6WEg89YO0SMPNN5lLDqMFYVpRHkmqOcharMRX5vR9cbS%2F5nmn9usWRHfL%0AhnbBFcl2oB77TmSbyP4kx%2FyuhtkZl%2Ff7q8H0lTz4RR%2BeVS2JteU2%2FEiujZJseC0Jd5OafmcsUu21%0Aztn4fSxlhf6ik26A8YY1Vug%3D|预订|24000000G505|G5|VNP|SHH|VNP|SHH|07:00|11:40|04:40|Y|JfeW5%2BeLQzhtQpP6ZbFTV6cIdVXY50m%2B0QRyOzLt2u%2FgcAvB|20181008|3|P2|01|05|1|0|||||||||||无|1|3||O0M090|OM9|0","E5tOWIQU3
```
This is absolutely what we need.  
And the map of `"BJP"` to "北京" as well as `"SHH"` to "上海" is just the ones in the URL. And the whole map has been found in the following URL:   
```
https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9066
```
And it can be found in website [12306.cn](#12306.cn) through the method of viewing web page source.  
Since the mapping is rarely chaged, we can write the data into a `CSV` file so that we don't have to crawl the webpage every time. The code to implement writing data to file is as follows:    
```Python
import re
import requests
import pandas as pd

if __name__ == '__main__':
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9066'
    r = requests.get(url)
    quoets = re.findall(u'([\u4e00-\u9fa5]+)\|([A-Z]+)', r.text)# Match at least one Chinese character or a upper letter
    dataframe = pd.DataFrame(quoets)
    # write data to .csv file
    dataframe.to_csv('themappingfile.csv', index = False, sep = ',', encoding = 'utf_8_sig')
    # read data from .csv file
    df = pd.read_csv('themappingfile.csv')# The type of 'df' is 'DataFrame'
```
Anyway, I've put the CSV file in the repository and you can [download](./themappingfile.csv) and use it directly.  

Then we can itegrate and manage the huge database through the `pandas` library of `Python`. Exceting~ 
Thanks for reading!
@author: llwang
