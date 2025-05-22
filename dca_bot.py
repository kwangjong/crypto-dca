import os
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN, getcontext
import ccxt
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# ========== Setup ==========
load_dotenv()
getcontext().prec = 10

# ========== Logging Setup ==========
log_dir = os.path.expanduser('~/logs')
os.makedirs(log_dir, exist_ok=True)

log_filename = f"dca_{datetime.now().strftime('%Y-%m-%d')}.log"
log_path = os.path.join(log_dir, log_filename)

handler = TimedRotatingFileHandler(
    log_path,
    when='W0',           # Rotate every Monday
    interval=1,
    backupCount=50,
    encoding='utf-8'
)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# ========== Config ==========
DRY_RUN = True
WEEKLY_TOTAL = Decimal('50000')

chunk_config = {
    'BTC/KRW': {'budget': Decimal('25000'), 'splits': 3},
    'ETH/KRW': {'budget': Decimal('15000'), 'splits': 3},
    'SOL/KRW': {'budget': Decimal('5000'),  'splits': 1},
    'LINK/KRW': {'budget': Decimal('5000'), 'splits': 1},
}

# ========== Main Bot Logic ==========
def run_dca():
    logger.info(f"⏱️ DCA bot started at {datetime.now()}")
    today_index = datetime.now().weekday()

    bithumb = ccxt.bithumb({
        'apiKey': os.getenv("ACCESS_KEY"),
        'secret': os.getenv("SECRET_KEY"),
        'enableRateLimit': True
    })

    try:
        balance = bithumb.fetch_balance()
        available_krw = Decimal(str(balance['free']['KRW']))
        logger.info(f"Available KRW balance: {available_krw}")
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        return

    tickers = {}
    for symbol in chunk_config:
        try:
            tickers[symbol] = bithumb.fetch_ticker(symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch ticker for {symbol}: {e}")
            continue

    for symbol, config in chunk_config.items():
        splits = config['splits']
        budget = config['budget']
        chunk_krw = (budget / splits).quantize(Decimal('1.'), rounding=ROUND_DOWN)

        step = 7 / splits
        scheduled_days = [round(i * step) % 7 for i in range(splits)]

        if today_index not in scheduled_days:
            logger.info(f"Skipping {symbol} today (scheduled for {scheduled_days})")
            continue

        if symbol not in tickers:
            logger.warning(f"No ticker data for {symbol}, skipping.")
            continue

        price = Decimal(str(tickers[symbol]['close']))
        amount = (chunk_krw / price).quantize(Decimal('0.000001'), rounding=ROUND_DOWN)

        logger.info(f"[{symbol}] Price: {price}, Budget: {chunk_krw}, Amount: {amount}")

        if chunk_krw < Decimal('5000'):
            logger.warning(f"Chunk for {symbol} below minimum order size. Skipping.")
            continue

        if chunk_krw > available_krw:
            logger.warning(f"Insufficient KRW for {symbol}. Skipping.")
            continue

        if DRY_RUN:
            logger.info(f"[Dry Run] Would buy {amount} of {symbol} for {chunk_krw} KRW")
        else:
            try:
                resp = bithumb.create_market_buy_order(symbol=symbol, amount=float(amount))
                logger.info(f"Executed order: {resp}")
            except Exception as e:
                logger.error(f"Failed to buy {symbol}: {e}")

# ========== Scheduler ==========
if __name__ == '__main__':
    scheduler = BlockingScheduler(timezone='Asia/Seoul')
    scheduler.add_job(run_dca, 'cron', hour=9, minute=0)
    logger.info("✅ DCA Scheduler started. Waiting for next run at 09:00 KST daily...")
    scheduler.start()