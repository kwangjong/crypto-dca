import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self, token_env: str, chat_id_env: str):
        self.token = os.getenv(token_env)
        self.chat_id = os.getenv(chat_id_env)

        if not self.token or not self.chat_id:
            raise ValueError("Telegram token or chat ID not set in environment variables.")

    def send_telegram_message(self, message: str):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
