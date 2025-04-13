import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit
from config import KEYWORDS, EXCLUDED_KEYWORDS  # Импортируем ключевые слова из config.py
import asyncio
from datetime import datetime

# Базовый URL сайта
base_url = 'https://мтв.онлайн/feed'

def make_clickable_url(url):
    """Преобразует URL в кликабельный формат (Punycode)"""
    try:
        parsed = urlsplit(url)
        if any(ord(c) > 127 for c in parsed.netloc):
            netloc = parsed.netloc.encode('idna').decode('ascii')
            parsed = parsed._replace(netloc=netloc)
        return parsed.geturl()
    except Exception:
        return url

def contains_keywords(text, keywords):
    """Проверяет, содержит ли текст хотя бы одно ключевое слово"""
    return any(word.lower() in text.lower() for word in keywords)

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
}

def format_date(date_str):
    """
    Преобразует дату из формата '6 Апреля, 14:55' в формат '06.04.25 14:55'.
    """
    try:
        if not date_str:
            return None

        parts = date_str.split(", ")
        if len(parts) != 2:
            return None

        date_part, time_part = parts
        day, month_name = date_part.split(" ")
        month = MONTHS_RU.get(month_name.lower())
        if not month:
            return None

        year = datetime.now().year % 100
        formatted_date = f"{int(day):02}.{month:02}.{year:02} {time_part}"
        return formatted_date
    except Exception as e:
        print(f"Ошибка при форматировании даты '{date_str}': {e}")
        return None

async def fetch_mtv_news():
    """Асинхронно парсит новости с сайта и фильтрует их по ключевым словам"""
    news_list = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://xn--b1ats.xn--80asehdb/feed', ssl=False) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), 'html.parser')

                for item in soup.find_all('div', class_='item-title'):
                    title_tag = item.find('h2')
                    title = title_tag.text.strip() if title_tag else ""

                    link_tag = item.find('a', href=True)
                    if not link_tag:
                        continue
                    relative_link = link_tag['href']
                    absolute_link = urljoin(base_url, relative_link)
                    clickable_link = make_clickable_url(absolute_link)

                    description = ""
                    summary_block = item.find_next_sibling('p', class_='short')
                    if summary_block:
                        description = summary_block.text.strip()

                    date = None
                    summary_block = item.find_next_sibling('div', class_='summary')
                    if summary_block:
                        date_tag = summary_block.find('span', class_='dt')
                        if date_tag:
                            raw_date = date_tag.text.strip().split('|')[0].strip()
                            date = format_date(raw_date)

                    full_text = f"{title} {description}"
                    if contains_keywords(full_text, KEYWORDS) and not contains_keywords(full_text, EXCLUDED_KEYWORDS):
                        news_list.append({
                            "title": title,
                            "link": clickable_link,
                            "date": date
                        })

    except Exception as e:
        print(f"❗️ Ошибка при парсинге: {e}")

    return news_list

def display_news(news_list):
    """Выводит новости в требуемом формате"""
    if not news_list:
        print(f"❗️ Для сайта {base_url} нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")
        return

    seen_links = set()
    for news in news_list:
        if news['link'] not in seen_links:
            seen_links.add(news['link'])
            print(
                f"📢 Заголовок: {news['title']}\n"
                f"🔗 Ссылка: {news['link']}\n"
                f"📅 Дата публикации: {news['date']}\n"
                f"{'-' * 50}"
            )

async def main():
    """Основная функция для получения и вывода новостей"""
    news = await fetch_mtv_news()
    display_news(news)

if __name__ == "__main__":
    asyncio.run(main())