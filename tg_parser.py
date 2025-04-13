from telethon.sync import TelegramClient


TELEGRAM_CHANNELS = [
    "Volgograda1",
    "volgograd1",
    "bIoknot_vlg",
    "ghestvolgograd",
    "newsv1",
    "NovostiVLG",
    "vlzjest",
    "volgograd_smi"
]

client = TelegramClient("session_name", API_ID, API_HASH)


async def fetch_telegram_news():
    await client.start()
    all_news = []

    for channel in TELEGRAM_CHANNELS:
        try:
            async for message in client.iter_messages(channel, limit=5):
                all_news.append({"title": message.text[:200], "link": f"https://t.me/{channel}/{message.id}"})
        except Exception as e:
            print(f"Ошибка при получении сообщений из {channel}: {e}")

    await client.disconnect()
    return all_news


if __name__ == "__main__":
    import asyncio

    news = asyncio.run(fetch_telegram_news())

    for item in news:
        print(f"Заголовок: {item['title']}\nСсылка: {item['link']}\n")
