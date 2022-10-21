import datetime
import lineTool
import fugle_trade
from fugle_realtime import WebSocketClient
import time
import json
from fugle_trade.constant import *

from fugle_trade.order import OrderObject
from fugle_trade.sdk import SDK
from configparser import ConfigParser

API_TOKEN = ''
LINE_NOTIFY_TOKEN = ''


# v2
class GridTrading:

    def __init__(self, symbol_id, grid_size_ratio, first_position):

        # 初始化下單API 並取得sdk object
        # self.sdk = self._init_fugle_trade()

        # 設定交易標的
        self.symbol_id = symbol_id

        # 首筆交易建倉幾張
        self.first_position = first_position

        # 網格大小的比例
        self.grid_size_ratio = grid_size_ratio
        # 設定網格大小
        self.grid_size = None
        # 設定第一次買進的價格
        self.base_price = None
        # 網格大小的比例 * 第一次買進的價格 = 網格大小

        # 目前價格
        self.now_price = None
        # 目前持有部位數量
        self.now_position = 0

    def _init_fugle_trade(self):
        # 讀取設定檔
        config = ConfigParser()
        config.read('./config.simulation.ini')  # 使用模擬環境
        # 登入
        sdk = SDK(config)
        sdk.login()

        return sdk

    def _on_new_price(self, message):
        json_data = json.loads(message)

        if json_data['data']['info']['type'] == "EQUITY":
            # 更新目前價格
            self.now_price = json_data['data']['quote']['trade']['price']
            print(json_data)

    def create_ws_quote(self):

        ws_client = WebSocketClient(api_token=API_TOKEN)
        ws = ws_client.intraday.quote(symbolId=self.symbol_id, on_message=self._on_new_price)
        ws.run_async()

        time.sleep(1)

    def buy(self, qty):
        order = OrderObject(
            buy_sell=Action.Buy,
            price_flag=PriceFlag.Market,
            price='',
            stock_no=self.symbol_id,
            quantity=qty,
            ap_code=APCode.Common,
            trade=Trade.Cash
        )
        #
        self.sdk.place_order(order)
        msg = '\n' + f'目前有 {str(self.now_position)} 張部位' + '\n' + '買進' + self.symbol_id + '\n' + str(
            qty) + "張" + '\n' + str(self.now_price) + '元'
        lineTool.lineNotify(LINE_NOTIFY_TOKEN, msg)

    def sell(self, qty):
        order = OrderObject(
            buy_sell=Action.Sell,
            price_flag=PriceFlag.Market,
            price='',
            stock_no=self.symbol_id,
            quantity=qty,
            ap_code=APCode.Common,
            trade=Trade.DayTradingSell  # 當沖賣
        )
        #
        self.sdk.place_order(order)
        msg = '\n' + f'目前有 {str(self.now_position)} 張部位' + '\n' + '賣出' + self.symbol_id + '\n' + str(
            qty) + "張" + '\n' + str(self.now_price) + '元'
        lineTool.lineNotify(LINE_NOTIFY_TOKEN, msg)

    def run_trade(self):

        # 以市價買入 5 張
        if self.now_price is not None:
            # 設定第一次買進的價格
            self.base_price = self.now_price
            # 設定網格大小
            self.grid_size = self.base_price * self.grid_size_ratio

            # 買進部位
            self.now_position = self.first_position
            self.buy(self.now_position)

        # 如果是盤中
        while datetime.time(9, 0, 0) < datetime.datetime.now().time() < datetime.time(13, 25, 0):

            if self.now_position > 0 and self.now_price >= self.base_price + (
                    (self.first_position + 1 - self.now_position) * self.grid_size):

                # 賣出一部位
                self.sell(1)
                # 更新
                self.now_position = self.now_position - 1

            # 最多持有上限
            elif self.now_position < 10 and self.now_price <= self.base_price - (
                    (self.now_position - (self.first_position - 1)) * self.grid_size):

                # 買進一部位
                self.buy(1)
                # 更新
                self.now_position = self.now_position + 1

        # 13:25 最後一盤 市價賣出所有部位
        if self.now_position > 0:
            self.sell(self.now_position)


if __name__ == '__main__':
    # 輸入要交易的標的，以第一筆成交價格的 1% 作為網格大小
    gt = GridTrading('6150', 0.005, 2)
    gt.create_ws_quote()
    gt.run_trade()
