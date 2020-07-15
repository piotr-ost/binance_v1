from spot import SpotTrade, current_time
from data import SpotData
from client import client
from cross_overs import CrossesOver
from indicators import Indicators
import time
import webbrowser


class Main:

	"""
	if btc in uptrend - trade btc pairings, hold btc
	if btc is falling - trade usdt pairings, hold tether

	# TODO (sorry for using this docs as a notepad)
	add:
	consider fibonacci an awesome strategy, peaks from codewars
	add volume param and whenever volume is significantly higher on 1 min -
	trigger a buy signal
	(lets say average of the day for the given interval)
	"""

	client = client

	def __init__(self, symbol, interval):
		self.symbol = symbol
		self.trade = SpotTrade(client, symbol)
		self.data = SpotData(client, symbol, interval)
		self.indicators = Indicators(client, symbol, interval)
		self.ignored = []

	def converter(self, quantity):
		"""
		the precision value varies depending on symbol
		it tends to : higher price <==> more decimal points
		"""
		min_qty = self.client.get_symbol_info(
			self.symbol)['filters'][2]['minQty']
		precision = min_qty.split('.')[1].find('1') + 1
		if self.symbol.endswith('BTC'):
			quantity = self.to_btc(quantity)/self.data.last_price()
		if self.symbol.endswith('USDT'):
			quantity = quantity/self.data.last_price()
		return round(quantity, precision)

	def to_btc(self, quantity):
		return quantity/self.data.btc_price()

	def altcoin_scanner(self, quantity):
		"""
		NOTE! using weekly open and daily open to point trend is only good for
		very short timeframes, a better way for most time frames would be to
		use weekly open and some other trend tool,
		for example a moving average, continue research
		"""
		last_price = self.data.last_price()
		weekly_open = self.data.weekly_open()
		daily_open = self.data.daily_open()
		if last_price > weekly_open and self.symbol not in self.ignored:
			MFI = round(self.indicators.get_mfi(), 2)
			print(f'Symbol: {self.symbol},\
				\nLatest MFI vals: {MFI[-2]}, {MFI[-1]}\
				\nDaily change: {round((1-last_price/daily_open)*100,2)}%\
				\n------------')
			if CrossesOver(MFI, 20):
				ATR = Indicators(client, self.symbol, '4h').get_atr()
				take_profit = last_price + 2*ATR
				stop_loss = last_price - ATR
				print(
					f'Buy signal!\
					\nEntry: {last_price}\
					\nTake Profit: {take_profit}\
					\nStop Loss: {stop_loss}\
					\nTime: {current_time()}\
					\nShow chart? (y/n)'
				)
				if input() == 'y':
					# link assumes we are trading -btc pairs
					link = 'https://www.binance.com/en/trade/pro/{}_{}'.format(
						self.symbol[:-3], self.symbol[-3:])
					webbrowser.open(link)

				print('Enter? (y/n)')
				if input() == 'y':
					qty = self.converter(quantity)
					self.trade.market_order_buy(qty)
					self.trade.oco_sell(price=int(take_profit),
										stopPrice=int(stop_loss),
										quantity=qty,
										)
					self.ignored.append(self.symbol)


if __name__ == '__main__':
	all_tickers = client.get_all_tickers()
	pool = [x['symbol'] for x in all_tickers if x['symbol'].endswith('BTC')]
	while 1:
		for i in pool:
			a = Main(i, '5m')
			a.altcoin_scanner(10)
			time.sleep(1)
		time.sleep(5)
