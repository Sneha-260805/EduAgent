import sqlite3
from config.settings import DB_FILE


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            sessions INTEGER NOT NULL DEFAULT 0,
            questions_asked INTEGER NOT NULL DEFAULT 0,
            last_level TEXT NOT NULL DEFAULT 'beginner',
            topics_seen TEXT NOT NULL DEFAULT '[]',
            question_history TEXT NOT NULL DEFAULT '[]',
            topic_question_counts TEXT NOT NULL DEFAULT '{}',
            weak_areas TEXT NOT NULL DEFAULT '[]',
            recommended_next_topics TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """
    )
    cur.execute("PRAGMA table_info(user_profiles)")
    existing_cols = {row[1] for row in cur.fetchall()}
    if "question_history" not in existing_cols:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN question_history TEXT NOT NULL DEFAULT '[]'")
    if "topic_question_counts" not in existing_cols:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN topic_question_counts TEXT NOT NULL DEFAULT '{}'")
    if "weak_areas" not in existing_cols:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN weak_areas TEXT NOT NULL DEFAULT '[]'")
    if "recommended_next_topics" not in existing_cols:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN recommended_next_topics TEXT NOT NULL DEFAULT '[]'")
    conn.commit()
    conn.close()
