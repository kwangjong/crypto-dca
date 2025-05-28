from decimal import Decimal
from datetime import datetime
from utils.logger import setup_logger
from utils.math_utils import quantize_up, calculate_purchase_amount
from utils.exchange import get_bithumb_client, get_available_krw, fetch_tickers
from utils.notifier import TelegramNotifier

class DCA:
    
    def __init__(self, dry_run:bool=True, weekly_total:int=50000):
        self.dry_run = dry_run
        self.weekly_total = weekly_total

        self.logger = setup_logger("dca")
        self.exchange = get_bithumb_client()
        self.notifier = TelegramNotifier(token_env='DCA_BOT_TELEGRAM_TOKEN', chat_id_env='DCA_BOT_CHAT_ID')
        
        self.chunk_config = {
            'BTC/KRW': {'budget': Decimal('25000'), 'splits': 3},
            'ETH/KRW': {'budget': Decimal('15000'), 'splits': 3},
            'SOL/KRW': {'budget': Decimal('5000'),  'splits': 1},
            'LINK/KRW': {'budget': Decimal('5000'), 'splits': 1},
        }
        
        self.logger.info("DCA initialized. Waiting for next schedule...")

    def run_dca(self):
        self.logger.info(f"DCA bot started at {datetime.now()}")
        
        summary = ["hi! health check from your dca bot!", ""]
        today_index = datetime.now().weekday()

        try:
            balance = self.exchange.fetch_balance()
            available_krw = get_available_krw(balance)
            self.logger.info(f"Available KRW balance: {available_krw}")
            summary.append(f"Available balance: {available_krw}")
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            self.notifier.send_telegram_message(f"error fetching balance :(\n\n{e}")
            return

        tickers = fetch_tickers(self.exchange, self.chunk_config.keys(), self.logger)


        orders = []
        for symbol, config in self.chunk_config.items():
            splits = config['splits']
            budget = config['budget']
            chunk_krw = quantize_up(budget / splits)

            step = 7 / splits
            scheduled_days = [round(i * step) % 7 for i in range(splits)]

            if today_index not in scheduled_days:
                self.logger.info(f"Skipping {symbol} today (scheduled for {scheduled_days})")
                continue

            if symbol not in tickers:
                self.logger.warning(f"No ticker data for {symbol}, skipping.")
                continue

            price = Decimal(str(tickers[symbol]['close']))
            amount = calculate_purchase_amount(chunk_krw, price)
            
            self.logger.info(f"[{symbol}] Price: {price}, Budget: {chunk_krw}, Amount: {amount}")
            
            if chunk_krw < Decimal('5000'):
                self.logger.warning(f"Chunk for {symbol} below minimum order size. Skipping.")
                continue

            if chunk_krw > available_krw:
                self.logger.warning(f"Insufficient KRW for {symbol}. Skipping.")
                continue
            
            orders.append({
                'symbol': symbol,
                'amount': amount,
                'price': price,
                'chunk_krw': chunk_krw
            })
            
        summary.append("")
        for order in orders:
            symbol, amount, chunk_krw = order['symbol'], order['amount'], order['chunk_krw']
            
            if self.dry_run:
                self.logger.info(f"[Dry Run] Would buy {amount} of {symbol} for {chunk_krw} KRW")
                summary.append(f"[Dry Run] Would buy {amount} of {symbol} for {chunk_krw} KRW")
            else:
                try:
                    resp = self.exchange.create_market_buy_order(symbol=symbol, amount=amount)
                    self.logger.info(f"Executed order: {resp}")
                    summary.append(f"Bought {amount} of {symbol} for {chunk_krw} KRW")
                except Exception as e:
                    self.logger.error(f"Failed to buy {amount} of {symbol}: {e}")
                    self.notifier.send_telegram_message(f"error placing buy order :(\n\n{e}")
        
        summary.append("")
        summary.append("have a nice day :)")          
        self.notifier.send_telegram_message('\n'.join(summary))