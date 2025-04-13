import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_tz, mktime_tz
from config import KEYWORDS, EXCLUDED_KEYWORDS

async def fetch_bloknot_news():
    """Асинхронно парсит новости с bloknot-volgograd.ru и возвращает список подходящих новостей."""
    rss_url = 'https://bloknot-volgograd.ru/rss_news.php'
    news_list = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_url) as response:
                response.raise_for_status()
                content = await response.text()

                # Парсим RSS с помощью BeautifulSoup
                soup = BeautifulSoup(content, "xml")
                items = soup.find_all("item")

                if not items:
                    print("❗️ Не удалось найти новости.")
                    return []

                now = datetime.now()

                for item in items:
                    title = item.title.text if item.title else "Заголовок не найден"
                    link = item.link.text if item.link else "Ссылка не найдена"
                    description = item.description.text if item.description else ""
                    pub_date = item.pubDate.text if item.pubDate else None

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
        print(f"❗️ Ошибка при запросе или парсинге: {e}")

    # Проверяем, есть ли новости в списке
    if not news_list:
        print(f"❗️ Для сайта {rss_url} нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")

    return news_list

# Асинхронная основная функция
async def main():
    # Получаем новости
    news = await fetch_bloknot_news()

    # Выводим новости, если они есть
    for item in news:
        print(f"📢 Заголовок: {item['title']}\n"
              f"🔗 Ссылка: {item['link']}\n"
              f"📅 Дата публикации: {item['date']}\n"
              f"{'-' * 50}")

# Запуск асинхронной программы
if __name__ == "__main__":
    asyncio.run(main())