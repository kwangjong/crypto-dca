import os
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN, getcontext
import ccxt
import logging

# ========== Setup ==========
load_dotenv()
getcontext().prec = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRY_RUN = True  # Toggle for testing without executing real orders
TOTAL_KRW = Decimal('50000')

# ========== Portfolio Class ==========
class Portfolio:
    def __init__(self, ratios, total_krw):
        self.portfolio = {}
        for symbol, ratio in ratios.items():
            self.portfolio[symbol] = {
                'symbol': symbol,
                'ratio': Decimal(str(ratio)),
                'buy_volume_krw': Decimal(str(ratio)) * total_krw
            }

    def __iter__(self):
        return iter(self.portfolio.values())

# ========== Portfolio Ratios ==========
ratios = {
    'BTC/KRW': 0.5,
    'ETH/KRW': 0.3,
    'SOL/KRW': 0.1,
    'LINK/KRW': 0.1
}

portfolio = Portfolio(ratios, TOTAL_KRW)

# ========== Bithumb Setup ==========
bithumb = ccxt.bithumb({
    'apiKey': os.getenv("ACCESS_KEY"),
    'secret': os.getenv("SECRET_KEY"),
    'enableRateLimit': True
})

balance = bithumb.fetch_balance()
available_krw = Decimal(str(balance['free']['KRW']))
logger.info(f"Available KRW balance: {available_krw}")

# Cache prices
tickers = {}
for symbol in ratios:
    tickers[symbol] = bithumb.fetch_ticker(symbol)

# ========== Execute Orders ==========
for coin in portfolio:
    symbol = coin['symbol']
    price = Decimal(str(tickers[symbol]['close']))
    buy_krw = coin['buy_volume_krw']

    if buy_krw > available_krw:
        logger.warning(f"Insufficient funds for {symbol}. Skipping.")
        continue

    amount = (buy_krw / price).quantize(Decimal('0.000001'), rounding=ROUND_DOWN)

    logger.info(
        f"Symbol: {symbol}, Ratio: {coin['ratio']}, "
        f"Buy KRW: {buy_krw}, Price: {price}, Amount: {amount}"
    )

    if DRY_RUN:
        logger.info(f"[Dry Run] Would buy {amount} {symbol}")
    else:
        try:
            resp = bithumb.create_market_buy_order(
                symbol=symbol,
                amount=amount
            )
            logger.info(f"Executed order: {resp}")
        except Exception as e:
            logger.error(f"Order failed for {symbol}: {e}")
