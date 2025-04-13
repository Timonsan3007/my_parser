import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse
from config import KEYWORDS, EXCLUDED_KEYWORDS
import sys

BASE_URL = "https://gorvesti.ru"
FEED_URL = "https://gorvesti.ru/feed/"

async def fetch_gorvesti_news():
    """
    Асинхронно парсит новости с https://gorvesti.ru/feed/ за последние сутки.
    Возвращает список словарей с заголовком, ссылкой и датой публикации.
    """
    try:
        # Отправляем асинхронный GET-запрос
        async with aiohttp.ClientSession() as session:
            async with session.get(FEED_URL, timeout=10, ssl=False) as response:
                response.raise_for_status()
                content = await response.text()

        # Парсим HTML-код
        soup = BeautifulSoup(content, "html.parser")

        # Проверяем доступность новостей
        news_blocks = soup.find_all("div", class_="itm")
        if not news_blocks:
            print(f"❗️ Для сайта {BASE_URL} не удалось найти новости на странице.")
            return []

        # Определяем временной порог (последние сутки)
        cutoff_time = datetime.now() - timedelta(days=1)

        # Список для хранения новостей
        news_items = []

        for item in news_blocks:
            # Извлекаем заголовок
            title_tag = item.find("h2")
            title = title_tag.get_text(strip=True) if title_tag else None

            # Пропускаем, если заголовок не найден
            if not title:
                continue

            # Извлекаем ссылку
            link = BASE_URL + title_tag.find_parent("a")["href"] if title_tag and title_tag.find_parent("a") else None
            if not link:
                continue

            # Извлекаем дату
            date_tag = item.find("span", class_="dt")
            date_str = date_tag.get_text(strip=True) if date_tag else None

            # Преобразуем дату в объект datetime
            try:
                date = parse(date_str, dayfirst=True)
            except Exception:
                continue  # Пропускаем, если дата не парсится

            # Фильтрация по дате
            if date < cutoff_time:
                continue  # Пропускаем старые новости

            # Фильтрация по ключевым словам
            if any(kw.lower() in title.lower() for kw in KEYWORDS):
                if not any(ex_kw.lower() in title.lower() for ex_kw in EXCLUDED_KEYWORDS):
                    news_items.append({
                        "title": title,
                        "link": link,
                        "date": date.strftime("%d.%m.%y %H:%M")  # Форматируем дату в требуемом виде
                    })

        return news_items

    except aiohttp.ClientError as e:
        print(f"❗️ Ошибка при запросе к сайту {BASE_URL}: {e}")
        return []
    except Exception as e:
        print(f"❗️ Ошибка при парсинге: {e}")
        return []


def display_news(news_items):
    """
    Выводит новости в требуемом формате.
    Удаляет дубликаты по заголовкам и ссылкам.
    """
    if not news_items:
        print(f"❗️ Для сайта {BASE_URL} нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")
        return

    seen_links = set()  # Множество для хранения уникальных ссылок
    seen_titles = set()  # Множество для хранения уникальных заголовков

    for item in news_items:
        if item['link'] not in seen_links and item['title'] not in seen_titles:
            seen_links.add(item['link'])
            seen_titles.add(item['title'])
            print(
                f"📢 Заголовок: {item['title']}\n"
                f"🔗 Ссылка: {item['link']}\n"
                f"📅 Дата публикации: {item['date']}\n"
                f"{'-' * 50}"
            )


async def main():
    """
    Основная функция для получения и вывода новостей.
    """
    # Проверяем наличие ключевых слов
    if not KEYWORDS:
        print("❗️ Ключевые слова не указаны.")
        sys.exit(1)

    # Получаем новости
    news = await fetch_gorvesti_news()

    # Выводим новости
    display_news(news)


if __name__ == "__main__":
    # Запускаем асинхронную программу
    asyncio.run(main())