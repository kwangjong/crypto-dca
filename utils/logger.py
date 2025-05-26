import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name=__name__):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(os.path.dirname(base_dir), 'log')
    os.makedirs(log_dir, exist_ok=True)

    log_filename = f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    log_path = os.path.join(log_dir, log_filename)

    handler = TimedRotatingFileHandler(
        log_path,
        when='W0',
        interval=1,
        backupCount=50,
        encoding='utf-8'
    )

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger