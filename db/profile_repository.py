import json
import sqlite3
from datetime import datetime
from db.sqlite_store import get_conn


def default_profile():
    return {
        "sessions": 0,
        "questions_asked": 0,
        "last_level": "beginner",
        "topics_seen": [],
        "question_history": [],
        "topic_question_counts": {},
        "weak_areas": [],
        "recommended_next_topics": [],
    }


def create_profile_if_missing(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,))
    existing = cur.fetchone()
    if not existing:
        profile = default_profile()
        cur.execute(
            """
            INSERT INTO user_profiles
            (user_id, sessions, questions_asked, last_level, topics_seen, question_history, topic_question_counts, weak_areas, recommended_next_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                profile["sessions"],
                profile["questions_asked"],
                profile["last_level"],
                json.dumps(profile["topics_seen"]),
                json.dumps(profile["question_history"]),
                json.dumps(profile["topic_question_counts"]),
                json.dumps(profile["weak_areas"]),
                json.dumps(profile["recommended_next_topics"]),
            ),
        )
        conn.commit()
    conn.close()


def load_profile(user_id):
    create_profile_if_missing(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return default_profile()
    return {
        "sessions": int(row["sessions"]),
        "questions_asked": int(row["questions_asked"]),
        "last_level": row["last_level"],
        "topics_seen": json.loads(row["topics_seen"]) if row["topics_seen"] else [],
        "question_history": json.loads(row["question_history"]) if row["question_history"] else [],
        "topic_question_counts": json.loads(row["topic_question_counts"]) if row["topic_question_counts"] else {},
        "weak_areas": json.loads(row["weak_areas"]) if row["weak_areas"] else [],
        "recommended_next_topics": json.loads(row["recommended_next_topics"]) if row["recommended_next_topics"] else [],
    }


def save_profile(user_id, profile):
    create_profile_if_missing(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE user_profiles
        SET sessions = ?, questions_asked = ?, last_level = ?, topics_seen = ?, question_history = ?, topic_question_counts = ?, weak_areas = ?, recommended_next_topics = ?
        WHERE user_id = ?
        """,
        (
            profile["sessions"],
            profile["questions_asked"],
            profile["last_level"],
            json.dumps(profile["topics_seen"]),
            json.dumps(profile["question_history"]),
            json.dumps(profile["topic_question_counts"]),
            json.dumps(profile["weak_areas"]),
            json.dumps(profile["recommended_next_topics"]),
            user_id,
        ),
    )
    conn.commit()
    conn.close()


def create_user(name, username, email, password_hash):
    created_at = datetime.utcnow().isoformat() + "Z"
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (name, username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, username, email, password_hash, created_at),
        )
        user_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None
    conn.close()
    create_profile_if_missing(user_id)
    return user_id


def get_user_by_identifier(identifier):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, name, username, email, password_hash, created_at
        FROM users
        WHERE email = ? OR username = ?
        """,
        (identifier, identifier),
    )
    row = cur.fetchone()
    conn.close()
    return row
