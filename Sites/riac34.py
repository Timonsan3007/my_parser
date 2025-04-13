import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_tz, mktime_tz
import feedparser  # Импортируем feedparser
from config import KEYWORDS, EXCLUDED_KEYWORDS

async def fetch_riac34_news():
    """Асинхронно парсит новости с riac34.ru и возвращает список подходящих новостей."""
    rss_url = 'https://riac34.ru/rss/'
    news_list = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_url, ssl=False) as response:
                response.raise_for_status()
                feed_content = await response.text()

                # Парсим RSS-ленту с помощью feedparser
                feed = feedparser.parse(feed_content)

                if len(feed.entries) == 0:
                    print("❗️ Не удалось найти новости.")
                    return []

                now = datetime.now()

                for entry in feed.entries:
                    title = entry.title
                    link = entry.link
                    description = entry.description if hasattr(entry, 'description') else ""
                    pub_date = entry.published if hasattr(entry, 'published') else None

                    if not pub_date:
                        print(f"❗️ Ошибка: отсутствует дата публикации для новости '{title}'.")
                        continue

                    pub_date = pub_date.replace(",", "")
                    parsed_date = parsedate_tz(pub_date)

                    if parsed_date:
                        pub_date_obj = datetime.fromtimestamp(mktime_tz(parsed_date))
                        if now - pub_date_obj > timedelta(days=1):
                            continue  # Пропускаем новости старше 24 часов

                        formatted_date = pub_date_obj.strftime("%d.%m.%y %H:%M")

                        if (
                            any(keyword.lower() in title.lower() or keyword.lower() in description.lower() for keyword in KEYWORDS)
                            and not any(excluded.lower() in title.lower() or excluded.lower() in description.lower() for excluded in EXCLUDED_KEYWORDS)
                        ):
                            news_list.append({
                                "title": title,
                                "link": link,
                                "date": formatted_date
                            })
                    else:
                        print(f"❗️ Ошибка преобразования даты: {pub_date}")

    except Exception as e:
        print(f"❗️ Ошибка при парсинге: {e}")

    # Проверяем, есть ли новости в списке
    if not news_list:
        print(f"❗️ Для сайта {rss_url} нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")

    return news_list

async def main():
    """Основная функция для получения и вывода новостей."""
    news = await fetch_riac34_news()

    # Выводим новости, если они есть
    for item in news:
        print(f"📢 Заголовок: {item['title']}\n"
              f"🔗 Ссылка: {item['link']}\n"
              f"📅 Дата публикации: {item['date']}\n"
              f"{'-' * 50}")

if __name__ == "__main__":
    asyncio.run(main())