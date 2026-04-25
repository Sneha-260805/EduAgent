import sqlite3
from pathlib import Path

from config.settings import DB_FILE


def get_db_connection():
    """
    Return a SQLite connection with row access by column name.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the SQLite database.

    Tables:
    - users
    - profiles

    Complex profile fields are stored as JSON strings.
    """
    db_path = Path(DB_FILE)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------
    # users table
    # -----------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {row["name"] for row in cursor.fetchall()}
    if "username" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    if "created_at" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")

    # -----------------------------
    # profiles table
    # -----------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            sessions INTEGER DEFAULT 0,
            questions_asked INTEGER DEFAULT 0,
            last_level TEXT DEFAULT 'beginner',

            topics_seen TEXT DEFAULT '[]',
            level_history TEXT DEFAULT '[]',
            topic_counts TEXT DEFAULT '{}',
            weak_areas TEXT DEFAULT '{}',
            mastery TEXT DEFAULT '{}',
            used_explanations TEXT DEFAULT '{}',
            recommended_next_topics TEXT DEFAULT '[]',
            last_evaluation TEXT DEFAULT '{}',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute("PRAGMA table_info(profiles)")
    profile_cols = {row["name"] for row in cursor.fetchall()}
    if "recommended_next_topics" not in profile_cols:
        cursor.execute(
            "ALTER TABLE profiles ADD COLUMN recommended_next_topics TEXT DEFAULT '[]'"
        )
    if "last_evaluation" not in profile_cols:
        cursor.execute(
            "ALTER TABLE profiles ADD COLUMN last_evaluation TEXT DEFAULT '{}'"
        )

    conn.commit()
    conn.close()