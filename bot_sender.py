import requests
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_to_telegram():
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute("SELECT title, link FROM news ORDER BY date DESC LIMIT 5")
    news_list = cursor.fetchall()

    for title, link in news_list:
        text = f"{title}\n{link}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})

    conn.close()


if __name__ == "__main__":
    send_to_telegram()
