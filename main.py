from apscheduler.schedulers.blocking import BlockingScheduler
from dca_strategy import DCA

if __name__ == '__main__':
    scheduler = BlockingScheduler(timezone='Asia/Seoul')
    dca_bot = DCA(dry_run=False)
    #scheduler.add_job(lambda: run_dca(exchange, logger), 'cron', hour=9, minute=0)
    scheduler.add_job(lambda: dca_bot.run_dca(), 'interval', minutes=1)
    scheduler.start()