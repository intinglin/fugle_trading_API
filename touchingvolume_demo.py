# -*- coding: utf-8 -*-
"""# 安裝 fugle-trade 套件"""

# pip install 需要的套件
!pip install fugle-trade==0.1.8

# 安裝富果交易 API sdk
from configparser import ConfigParser
from fugle_trade.sdk import SDK

from fugle_trade.order import OrderObject
from fugle_trade.constant import (APCode, Trade, PriceFlag, BSFlag, Action)

"""# 模擬環境測試

您在首次使用交易 API 取得正式環境的使用權限前，您會需要在模擬環境至少送出一筆委託。
另外，在 colab 環境因安全性考量，會需要增加 keyring 來設置密碼，這邊的第一個密碼是證券登入密碼，第四個則是憑證密碼，中間兩個則是相同的 keyring 密碼
"""

## 取得 new 模擬環境設定檔並登入

config = ConfigParser()

config.read('./config.simulation.ini')

sdk = SDK(config)

sdk.login()

## 模擬金鑰下單測試
order = OrderObject(
    buySell = Action.Buy,
    price = 27.0,
    stockNo = "2884",
    quantity = 2,
)

sdk.place_order(order)

print("Your order has been placed successfully.")

## 查看委託回報
sdk.get_order_results()

## 更改密碼
# sdk.reset_password()

"""# 正式環境

在 colab 環境因安全性考量，會需要增加 keyring 來設置密碼，這邊的第一個密碼是證券登入密碼，第四個則是憑證密碼，中間兩個則是相同的 keyring 密碼
"""

# 取得正式環境設定檔並登入

config = ConfigParser()

config.read('./config.ini')

sdk = SDK(config)

sdk.login()

"""## 下委託"""

# 下委託單
order = OrderObject(
    apCode = APCode.Common,# 盤別
    buySell = Action.Buy,
    priceFlag= PriceFlag.LimitDown, # 下跌停價買進
    price = None,
    stockNo = str(2884),
    quantity = 10,
)

sdk.place_order(order)

# 委託回報
orderResult = sdk.get_order_results()

# 查看委託回報狀況
import pandas as pd
pd.DataFrame(orderResult)

# 刪掉最新一筆委託單
sdk.cancel_order(orderResult[0])

"""# 簡易策略 demo code"""

# pip install fugle-realtime API library from https://github.com/fugle-dev/fugle-realtime-python

!pip install fugle-realtime

# 安裝 富果行情 API sdk
from fugle_realtime import HttpClient

# 請輸入自己的 apiToken，才能查看其他個股 ！！
api_client = HttpClient(api_token='demo')

# 安裝相關套件
import requests
import numpy as np
import pandas as pd
import datetime
import time

# 取得正式環境設定檔並登入

config = ConfigParser()

config.read('./config.ini')

sdk = SDK(config)

sdk.login()

"""## 觸量下單 demo

策略描述：<br>
盤中突然的大單，可以反映大戶的交易意願提升，而外盤成交代表買方願意用比較高的價格買，代表有較強烈的買進意圖<br>
因此這裡建構一個簡單的策略：當最新一筆成交是外盤成交，且成交量是前一筆的 10 倍以上就跟！
"""

## set parameter

# 輸入股票代碼
symbolId = "2884"

# 下單張數
tradingVolume = 10

#----------------------------------
while True:  

    # 從 dealts API 取得最新兩筆成交明細數據 
    price_data = api_client.intraday.dealts(symbolId = symbolId)['data']['dealts'][:5]
 
    
    #策略條件：最新一筆成交量 大於等於 前一筆成交量的10倍 且為外盤成交
    if (price_data[0]['volume'] >= price_data[1]['volume']*10) and (price_data[0]['ask'] <= price_data[0]['price']):

        # 委託資訊
        order = OrderObject(
            apCode = APCode.Common,# 盤別
            buySell = Action.Buy,
            priceFlag= PriceFlag.LimitDown, # 跌停價買進
            price = None,
            stockNo = str(symbolId),
            quantity = tradingVolume,
        )

        # 送下單委託
        sdk.place_order(order)
        
        print('成功送出委託')
        print(f'買進張數：{tradingVolume} 張')

        break
        
    else:
        print(f"最新成交量 {str(price_data[0]['volume'])} 張")
        print(f'外盤成交：',str(price_data[0]['ask'] <= price_data[0]['price']))
        print('未達買進條件!')
        print('---')
        time.sleep(1)

# 查看委託回報
sdk.login()
orderResult = sdk.get_order_results()
print(orderResult[0])

# 刪掉第 0 筆單
sdk.cancel_order(orderResult[0])
