import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
from config import KEYWORDS, EXCLUDED_KEYWORDS
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_valid_news(title):
    """Проверяет новость на соответствие ключевым словам"""
    if not title:
        return False

    title_lower = title.lower()
    has_keyword = any(keyword.lower() in title_lower for keyword in KEYWORDS)
    no_excluded = not any(excluded.lower() in title_lower for excluded in EXCLUDED_KEYWORDS)

    logger.debug(f"Проверка: '{title}'")
    logger.debug(f"Ключевые слова: {has_keyword}, Исключения: {not no_excluded}")

    return has_keyword and no_excluded


async def fetch_news_datetime(session, news_url):
    """Улучшенный парсер даты с дополнительными источниками"""
    try:
        async with session.get(news_url, ssl=False) as response:
            response.raise_for_status()
            soup = BeautifulSoup(await response.text(), 'lxml')

            # 1. Попробуем получить из JSON
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    # Проверяем несколько возможных путей к дате
                    date_str = (data.get('props', {}).get('pageProps', {}).get('post', {}).get('date') or
                                data.get('props', {}).get('pageProps', {}).get('initialMatters', [{}])[0].get(
                                    'datePublished'))
                    if date_str:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except Exception as e:
                    logger.debug(f"Ошибка парсинга JSON: {e}")

            # 2. Попробуем русский формат даты
            date_div = soup.select_one('div.MatterTop_date__mPSNt, [class*="date"], [class*="Date"]')
            if date_div:
                date_text = date_div.get_text(strip=True)
                try:
                    months = {
                        'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4,
                        'мая': 5, 'июн': 6, 'июл': 7, 'август': 8,
                        'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12
                    }
                    parts = date_text.lower().replace(',', '').split()
                    day = int(parts[0])
                    month_name = next((m for m in months if parts[1].startswith(m)), None)
                    if month_name:
                        month = months[month_name]
                        year = int(parts[2])
                        time_part = parts[3] if len(parts) > 3 else '00:00'
                        hour, minute = map(int, time_part.split(':'))
                        return datetime(year, month, day, hour, minute)
                except Exception as e:
                    logger.debug(f"Ошибка парсинга русской даты: {e}")

            # 3. Попробуем мета-теги
            for meta in soup.find_all('meta'):
                if meta.get('property') in ['article:published_time', 'pubdate'] and meta.get('content'):
                    try:
                        return datetime.fromisoformat(meta['content'][:19])
                    except ValueError:
                        continue

            logger.debug(f"Не удалось определить дату для {news_url}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении даты: {e}")
        return None


async def fetch_novostivolgograda_news():
    """Основная функция с улучшенной обработкой"""
    base_url = "https://novostivolgograda.ru/news"
    news_list = []
    date_threshold = datetime.now() - timedelta(days=1)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(base_url, ssl=False) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), 'lxml')

                # Более гибкий поиск новостных блоков
                news_items = soup.select('a[href^="/news/"]')

                for item in news_items:  # Ограничим для теста
                    try:
                        title = item.get_text(strip=True)
                        if not title or len(title) < 10:  # Фильтр мусора
                            continue

                        link = urljoin(base_url, item['href'])

                        # Пропускаем дубликаты
                        if any(n['link'] == link for n in news_list):
                            continue

                        # Получаем дату
                        pub_date = await fetch_news_datetime(session, link)
                        if not pub_date:
                            logger.debug(f"Не удалось определить дату для: {title}")
                            continue

                        logger.debug(f"Дата новости: {pub_date} - {title}")

                        if pub_date >= date_threshold and is_valid_news(title):
                            news_list.append({
                                'title': title,
                                'link': link,
                                'date': pub_date.strftime('%d.%m.%y %H:%M')  # Форматируем дату
                            })

                    except Exception as e:
                        logger.error(f"Ошибка обработки элемента: {e}")
                        continue

        except Exception as e:
            logger.error(f"Ошибка соединения: {e}")

    return news_list


async def main():
    """Точка входа в программу"""
    news = await fetch_novostivolgograda_news()

    if not news:
        print(f"❗️ Для сайта https://novostivolgograda.ru нет новых новостей, соответствующих заданным критериям!")
        print(f"{'-' * 50}")
        return

    seen_links = set()  # Множество для хранения уникальных ссылок
    seen_titles = set()  # Множество для хранения уникальных заголовков
    for item in news:
        if item['link'] not in seen_links and item['title'] not in seen_titles:
            seen_links.add(item['link'])
            seen_titles.add(item['title'])
            print(
                f"📢 Заголовок: {item['title']}\n"
                f"🔗 Ссылка: {item['link']}\n"
                f"📅 Дата публикации: {item['date']}\n"
                f"{'-' * 50}"
            )


if __name__ == "__main__":
    asyncio.run(main())