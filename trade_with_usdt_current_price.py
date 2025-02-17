import requests
import json
import time
import datetime
import sys

trade_ogre_api_key = 'YOUR_TRADEOGRE_API_KEY'
trade_ogre_secret_key = 'YOUR_TRADEOGRE_SECRET_API_KEY'
COINS = ['RVN', 'XRP', 'XMR', 'LTC', 'ETH']

debug = '--debug' in sys.argv
base_url = 'https://tradeogre.com/api/v1'

def timestamp_print(msg):
	date = datetime.datetime.now()
	print(f'\u001b[36m[ {date.year}{date.month}{date.day} {date.hour}:{date.minute} ]\u001b[37m {msg}')

class TradeOgre:
	def __init__(self, trade_ogre_api, trade_ogre_secret):
		self.trade_ogre_secret = trade_ogre_secret
		self.trade_ogre_api = trade_ogre_api

	def get_market_info(self, coin):
		'''
		RVN data at [30]['USDT-RVN']
		'''

		api_response = requests.get(base_url + '/markets', headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.trade_ogre_secret}'})
		j = json.loads(api_response.content.decode('utf-8'))		

		if api_response.status_code == 200:
			for i in j:
				if [k for k in i.keys()][0] == 'USDT-' + coin:
					return i['USDT-' + coin]
		else:
			return None

	def buy_coin(self, coin, amount, price):
		'''
		Buys RVN
		MIN AMOUNT IN USDT IS 1
		'''
		sats = str(price * 100000000)
		sats = sats.split('.')[0] if '.' in sats else sats

		total = format(amount*price, '.8f')

		api_response = requests.post(base_url + '/order/buy', {'market': 'USDT-' + coin, 'quantity': str(round(amount, 2)), 'price': format(price, '.8f')}, auth = (self.trade_ogre_api, self.trade_ogre_secret))
		
		if json.loads(api_response.text)['success']:
			timestamp_print(f'[!] Buy placed for {amount} {coin} at {sats} satoshis, total of {total} USDT')
		
		if debug:
			timestamp_print(json.loads(api_response.content.decode('utf-8')))
		return json.loads(api_response.content.decode('utf-8'))


	def sell_coin(self, coin, amount, price):
		'''
		Sells RVN
		MIN AMOUNT IN USDT IS 0.0001
		'''
		sats = str(price * 100000000)
		sats = sats.split('.')[0] if '.' in sats else sats

		total = format(amount*price, '.8f')

		api_response = requests.post(base_url + '/order/sell', {'market':'BTC-' + coin, 'quantity':amount, 'price': format(price, '.8f')}, auth = (self.trade_ogre_api, self.trade_ogre_secret))
		
		if json.loads(api_response.text)['success']:
			timestamp_print(f'[!] Sell placed for {amount} {coin} at {sats} satoshis, total of {total} BTC')
		
		if debug:
			timestamp_print(json.loads(api_response.content.decode('utf-8')))
		return json.loads(api_response.content.decode('utf-8'))


	def cancel_order(self, uuid):
		api_response = requests.post(base_url + '/order/cancel', data = {'uuid':uuid}, auth = (self.trade_ogre_api, self.trade_ogre_secret))
		timestamp_print(f'[!] Order cancelled for {uuid}')
		return json.loads(api_response.content.decode('utf-8'))


	def get_bal(self, currency_ticker):
		api_response = requests.get(base_url + '/account/balances', auth = (self.trade_ogre_api, self.trade_ogre_secret))
		return float(json.loads(api_response.content.decode('utf-8'))['balances'][currency_ticker])

	def get_order(self):
		api_response = requests.post(base_url + '/account/orders', auth = (self.trade_ogre_api, self.trade_ogre_secret))
		data = json.loads(api_response.content.decode('utf-8'))
		prev_orders = [0, 0]
		ctr = 0

		for i in data:
			if prev_orders[0] != 0 and prev_orders[1] != 0:
				break
			elif i['type'] == 'sell':
				prev_orders[1] = i['price']
			elif i['type'] == 'buy':
				prev_orders[0] = i['price']

		return prev_orders

'''
Create classes with API keys.
'''

trade_ogre = TradeOgre(trade_ogre_api_key, trade_ogre_secret_key)

def get_day_low(coin):
	trade_ogre_day_low = float(trade_ogre.get_market_info(coin)['low'])

	return trade_ogre_day_low

def get_day_high(coin):
	trade_ogre_day_hi = float(trade_ogre.get_market_info(coin)['high'])

	return trade_ogre_day_hi

def get_current_price(coin):
	trade_ogre_current_price = float(trade_ogre.get_market_info(coin)['price'])
	
	return (trade_ogre_current_price)

def buy_low(coin):
	price = get_current_price(coin) - (get_current_price(coin) * 0.01)
	return trade_ogre.buy_coin(coin, (trade_ogre.get_bal('USDT') / len(COINS)) / price, price)['success']

def sell_high(coin):
	return trade_ogre.sell_coin(coin, trade_ogre.get_bal(coin) / 2, get_current_price(coin) + get_current_price(coin) * 0.01)['success']

def algo_one():
	print('\u001b[37m', end='')

	while True:
		trade_ogre.cancel_order('all')
		
		time.sleep(5)

		for c in COINS:
			buy_low(c)
			sell_high(c)

		timestamp_print(f"\u001b[33m[^] Your USDT balance is {trade_ogre.get_bal('USDT')}")

		for c in COINS:
			timestamp_print(f"\u001b[33m[^] Your {c} balance is {trade_ogre.get_bal(c)}")
		
		print('\u001b[37m' + '-' * 30)

		time.sleep(300)

if __name__ == '__main__':	
	algo_one()
