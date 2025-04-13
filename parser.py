import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.filters import Command

from config import TELEGRAM_BOT_TOKEN, CHAT_ID, VK_ACCESS_TOKEN, VK_GROUPS, KEYWORDS, EXCLUDED_KEYWORDS

# Сайты
from Sites.bloknot_volgograd import fetch_bloknot_news
from Sites.gorvesti import fetch_gorvesti_news
from Sites.mtv_online import fetch_mtv_news
from Sites.novostivolgograda import fetch_novostivolgograda_news
from Sites.riac34 import fetch_riac34_news
from Sites.v1 import fetch_v1_news
from Sites.v102 import fetch_v102_news
from Sites.volgograd_kp import fetch_kp_news
from Sites.vpravda import fetch_vpravda_news

import requests

API_VERSION = "5.131"
VK_API_URL = "https://api.vk.com/method/wall.get"

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot
bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


def parse_date(timestamp):
    try:
        post_date = datetime.fromtimestamp(timestamp)
        return post_date.strftime("%d.%m.%y %H:%M")
    except Exception as e:
        logger.error(f"Ошибка при преобразовании даты: {e}")
        return None


async def fetch_vk_posts():
    news_list = []
    one_day_ago = datetime.now() - timedelta(days=1)

    for group in VK_GROUPS:
        try:
            response = requests.get(
                VK_API_URL,
                params={
                    "owner_id": f"-{group.replace('club', '')}" if group.isdigit() else group,
                    "count": 10,
                    "access_token": VK_ACCESS_TOKEN,
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
                        first_line = text.split("\n")[0] if "\n" in text else text
                        news_list.append({
                            "title": first_line,
                            "link": link,
                            "date": formatted_date,
                        })

            elif "error" in data:
                logger.error(f"Ошибка от {group}: [{data['error']['error_code']}] {data['error']['error_msg']}")
            await asyncio.sleep(0.5)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса для {group}: {e}")

    return news_list


async def collect_all_news():
    tasks = [
        fetch_bloknot_news(),
        fetch_gorvesti_news(),
        fetch_mtv_news(),
        fetch_novostivolgograda_news(),
        fetch_riac34_news(),
        fetch_v1_news(),
        fetch_v102_news(),
        fetch_kp_news(),
        fetch_vpravda_news(),
        fetch_vk_posts(),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_news = []

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Ошибка при выполнении задачи: {result}")
            continue
        all_news.extend(result)

    # Фильтрация по формату даты
    valid_news = []
    for news in all_news:
        try:
            datetime.strptime(news["date"], "%d.%m.%y %H:%M")
            valid_news.append(news)
        except ValueError:
            logger.error(f"Неверный формат даты: {news['date']} для: {news['title']}")

    # Сортировка от старых к новым
    valid_news.sort(key=lambda x: datetime.strptime(x["date"], "%d.%m.%y %H:%M"))
    return valid_news


@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer(
        "🔍 Собираю свежие новости, подождите немного...\n\n"
        "📌 По возникшим вопросам обращаться: @Blackfox3007"
    )

    news_list = await collect_all_news()
    if not news_list:
        await message.answer("❗️ Новостей за последние сутки не найдено.")
        return

    seen_links = set()
    for news in news_list:
        if news["link"] not in seen_links:
            seen_links.add(news["link"])
            await message.answer(
                f"<b>📢 Заголовок:</b> {news['title']}\n"
                f"<b>🔗 Ссылка:</b> {news['link']}\n"
                f"<b>📅 Дата:</b> {news['date']}\n"
                f"{'-' * 72}"
            )


if __name__ == "__main__":
    dp.run_polling(bot)
