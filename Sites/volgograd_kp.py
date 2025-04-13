import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
from config import KEYWORDS, EXCLUDED_KEYWORDS
import pytz

async def fetch_news_datetime(session, news_url):
    """Получает точное время публикации новости в часовом поясе Волгограда"""
    try:
        async with session.get(news_url, ssl=False) as response:
            response.raise_for_status()
            soup = BeautifulSoup(await response.text(), "lxml")
            meta_time = soup.find("meta", {"property": "article:published_time"})
            if meta_time and meta_time.get("content"):
                news_time = datetime.fromisoformat(meta_time["content"][:19])  # Создаем объект datetime без учета часового пояса
                utc_time = news_time.replace(tzinfo=pytz.utc)  # Присваиваем UTC
                volgograd_time = utc_time.astimezone(pytz.timezone("Europe/Volgograd"))  # Конвертируем в Волгоградское время
                return volgograd_time
    except Exception as e:
        print(f"Ошибка при получении даты: {e}")
    return None


BASE_URL = "https://www.volgograd.kp.ru/online/"  # Раздел с новостями

def is_valid_news(title):
    """Проверяет новость: содержит ли ключевые слова и не содержит запрещённые слова"""
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in KEYWORDS) and not any(
        excluded.lower() in title_lower for excluded in EXCLUDED_KEYWORDS)

async def fetch_kp_news():
    """Парсинг новостей с сайта КП-Волгоград"""
    news_list = []
    yesterday = datetime.now().date() - timedelta(days=1)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        try:
            async with session.get(BASE_URL, ssl=False) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), "lxml")

                # Универсальный поиск ссылок на новости
                articles = soup.find_all("a", href=True)

                for article in articles:
                    link = urljoin(BASE_URL, article["href"])
                    title = article.get_text(strip=True)

                    if title and is_valid_news(title):
                        news_date = await fetch_news_datetime(session, link)
                        if news_date and news_date.date() >= yesterday:
                            news_list.append({
                                "title": title,
                                "link": link,
                                "date": news_date.strftime("%d.%m.%y %H:%M")
                            })
        except aiohttp.ClientError as e:
            print(f"Ошибка при запросе: {e}")
    return news_list

async def main():
    """Основная функция"""
    kp_news = await fetch_kp_news()

    if not kp_news:
        print(f"❗️ Для сайта {BASE_URL} нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")
        return

    seen_links = set()  # Множество для хранения уникальных ссылок
    seen_titles = set()  # Множество для хранения уникальных заголовков

    for news in kp_news:
        if news['link'] not in seen_links and news['title'] not in seen_titles:
            seen_links.add(news['link'])  # Добавляем ссылку в множество
            seen_titles.add(news['title'])  # Добавляем заголовок в множество
            print(
                f"📢 Заголовок: {news['title']}\n"
                f"🔗 Ссылка: {news['link']}\n"
                f"📅 Дата публикации: {news['date']}\n"
                f"{'-' * 50}"
            )


if __name__ == "__main__":
    asyncio.run(main())