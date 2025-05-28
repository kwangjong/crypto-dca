import ccxt
import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

def get_bithumb_client():
    exchange = ccxt.bithumb({
        'apiKey': os.getenv("ACCESS_KEY"),
        'secret': os.getenv("SECRET_KEY"),
        'enableRateLimit': True
    })
    
    exchange.verbose = True
    return exchange

def get_available_krw(balance):
    return Decimal(str(balance['free']['KRW']))

def fetch_tickers(exchange, symbols, logger):
    tickers = {}
    for symbol in symbols:
        try:
            tickers[symbol] = exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch ticker for {symbol}: {e}")
    return tickers
