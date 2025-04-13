import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
from config import KEYWORDS, EXCLUDED_KEYWORDS


def is_valid_news(title):
    """
    Проверяет новость: содержит ли она ключевые слова и не содержит запрещённые слова.
    """
    title_lower = title.lower()
    return (
            any(keyword.lower() in title_lower for keyword in KEYWORDS) and
            not any(excluded.lower() in title_lower for excluded in EXCLUDED_KEYWORDS)
    )


def is_valid_link(link):
    """
    Проверяет, является ли ссылка допустимой для парсинга.
    Исключает ссылки на сторонние ресурсы и мессенджеры.
    """
    invalid_protocols = ["tel:", "whatsapp:", "viber:", "tg:", "mailto:"]
    invalid_domains = ["youtube.com", "youtu.be"]  # Добавьте другие домены, если нужно

    if any(link.startswith(protocol) for protocol in invalid_protocols):
        return False

    if any(domain in link for domain in invalid_domains):
        return False

    return True


async def fetch_news_datetime(session, news_url):
    """
    Получает точное время публикации новости с помощью мета-тегов или тега <time>.
    """
    try:
        async with session.get(news_url, ssl=False) as response:
            response.raise_for_status()
            soup = BeautifulSoup(await response.text(), "lxml")

            # Ищем мета-тег с временем публикации
            meta_time = soup.find("meta", {"property": "article:published_time"})
            if meta_time and meta_time.get("content"):
                return datetime.fromisoformat(meta_time["content"][:19])

            # Если мета-тег отсутствует, ищем тег <time>
            date_tag = soup.find("time")
            if date_tag and date_tag.get("datetime"):
                return datetime.fromisoformat(date_tag["datetime"][:19])
    except Exception as e:
        print(f"Ошибка при получении даты публикации: {e}")

    return None

async def fetch_vpravda_news():
    """
    Парсит новости с сайта https://vpravda.ru/ за последние сутки.
    """
    base_url = "https://vpravda.ru/"
    news_list = []
    yesterday = datetime.now().date() - timedelta(days=1)
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        try:
            # Формируем URL для запроса новостей за вчерашний день
            url = f"{base_url}?dateFrom={yesterday.strftime('%d.%m.%Y')}"
            async with session.get(url, ssl=False) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), "lxml")

                # Находим все ссылки на новости
                articles = soup.find_all("a", href=True)
                for article in articles:
                    title = article.text.strip()
                    link = urljoin(base_url, article["href"])

                    # Пропускаем недопустимые ссылки
                    if not is_valid_link(link):
                        continue

                    # Получаем точное время публикации новости
                    news_date = await fetch_news_datetime(session, link)
                    if (
                            news_date and
                            news_date.date() >= yesterday and
                            is_valid_news(title)
                    ):
                        news_list.append({
                            "title": title,
                            "link": link,
                            "date": news_date.strftime("%d.%m.%y %H:%M"),
                            "datetime": news_date  # Сохраняем объект datetime для сортировки
                        })
        except aiohttp.ClientError as e:
            print(f"Ошибка при запросе к сайту: {e}")

    # Сортируем новости по времени публикации (от новых к старым)
    news_list.sort(key=lambda x: x["datetime"], reverse=True)

    return news_list


async def main():
    """
    Основная функция для вывода новостей.
    """
    vpravda_news = await fetch_vpravda_news()

    if not vpravda_news:
        print(f"❗️ Для сайта https://vpravda.ru/ нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")
        return

    seen_links = set()  # Множество для хранения уникальных ссылок
    seen_titles = set()  # Множество для хранения уникальных заголовков

    for news in vpravda_news:
        if news['link'] not in seen_links and news['title'] not in seen_titles:
            seen_links.add(news['link'])
            seen_titles.add(news['title'])
            print(
                f"📢 Заголовок: {news['title']}\n"
                f"🔗 Ссылка: {news['link']}\n"
                f"📅 Дата публикации: {news['date']}\n"
                f"{'-' * 50}"
            )


if __name__ == "__main__":
    asyncio.run(main())