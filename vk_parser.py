import requests
from datetime import datetime, timedelta
import asyncio
from config import VK_GROUPS, KEYWORDS, EXCLUDED_KEYWORDS, VK_SERVICE_KEY

API_VERSION = "5.131"
VK_API_URL = "https://api.vk.com/method/wall.get"


def parse_date(timestamp):
    """
    Преобразует Unix-время в формат ДД.ММ.ГГ ЧЧ:ММ.
    """
    try:
        post_date = datetime.fromtimestamp(timestamp)
        return post_date.strftime("%d.%m.%y %H:%M")
    except Exception as e:
        print(f"Ошибка при преобразовании даты: {e}")
        return None


async def fetch_vk_posts():
    """
    Получает посты из групп ВК и фильтрует их по ключевым словам.
    """
    news_list = []
    one_day_ago = datetime.now() - timedelta(days=1)

    for group in VK_GROUPS:
        try:
            response = requests.get(
                VK_API_URL,
                params={
                    "owner_id": f"-{group.replace('club', '')}" if group.isdigit() else group,
                    "count": 10,
                    "access_token": VK_SERVICE_KEY,
                    "v": API_VERSION,
                },
                timeout=10,
            )
            data = response.json()

            if "response" in data:
                for post in data["response"]["items"]:
                    text = post.get("text", "").strip()
                    post_id = post.get("id")
                    group_id = post.get("owner_id")
                    date = post.get("date")
                    link = f"https://vk.com/wall{group_id}_{post_id}"

                    formatted_date = parse_date(date)
                    if not formatted_date:
                        continue

                    post_date = datetime.fromtimestamp(date)
                    if post_date < one_day_ago:
                        continue

                    text_lower = text.lower()
                    if (
                        any(keyword.lower() in text_lower for keyword in KEYWORDS)
                        and not any(excluded.lower() in text_lower for excluded in EXCLUDED_KEYWORDS)
                    ):
                        news_list.append({
                            "title": text[:100] + "..." if len(text) > 100 else text,
                            "link": link,
                            "date": formatted_date,
                        })

            elif "error" in data:
                error_code = data["error"].get("error_code")
                error_msg = data["error"].get("error_msg")
                print(f"Ошибка при получении данных от {group}: [{error_code}] {error_msg}")

            # Добавляем задержку между запросами
            await asyncio.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса для {group}: {e}")

    return news_list


if __name__ == "__main__":
    vk_news = asyncio.run(fetch_vk_posts())

    # Сортируем новости по времени публикации (от новых к старым)
    vk_news.sort(key=lambda x: datetime.strptime(x["date"], "%d.%m.%y %H:%M"), reverse=True)

    # Выводим новости
    seen_links = set()
    for news in vk_news:
        if news['link'] not in seen_links:
            seen_links.add(news['link'])
            print(
                f"📢 Заголовок: {news['title']}\n"
                f"🔗 Ссылка: {news['link']}\n"
                f"📅 Дата публикации: {news['date']}\n"
                f"{'-' * 50}"
            )