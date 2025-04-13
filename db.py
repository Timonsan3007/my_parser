import sqlite3

def init_db():
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            source TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_news(news_list, source):
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    for news in news_list:
        try:
            cursor.execute("INSERT INTO news (title, link, source) VALUES (?, ?, ?)",
                           (news["title"], news["link"], source))
        except sqlite3.IntegrityError:
            pass  # Новость уже есть в базе

    conn.commit()
    conn.close()
