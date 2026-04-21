import json
from datetime import datetime

from db.sqlite_store import get_db_connection
from agents.memory_agent import ensure_profile_structure


def _safe_json_load(value, default):
    """
    Safely load a JSON string.
    """
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def create_profile_if_missing(user_id: int):
    """
    Ensure a default profile exists for the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM profiles WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row is None:
        default_profile = ensure_profile_structure({
            "sessions": 0,
            "questions_asked": 0,
            "last_level": "beginner",
            "topics_seen": [],
            "level_history": [],
            "topic_counts": {},
            "weak_areas": {},
            "mastery": {},
            "used_explanations": {},
            "recommended_next_topics": []
        })

        cursor.execute(
            """
            INSERT INTO profiles (
                user_id,
                sessions,
                questions_asked,
                last_level,
                topics_seen,
                level_history,
                topic_counts,
                weak_areas,
                mastery,
                used_explanations,
                recommended_next_topics
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                default_profile["sessions"],
                default_profile["questions_asked"],
                default_profile["last_level"],
                json.dumps(default_profile["topics_seen"]),
                json.dumps(default_profile["level_history"]),
                json.dumps(default_profile["topic_counts"]),
                json.dumps(default_profile["weak_areas"]),
                json.dumps(default_profile["mastery"]),
                json.dumps(default_profile["used_explanations"]),
                json.dumps(default_profile["recommended_next_topics"]),
            )
        )

        conn.commit()

    conn.close()


def load_profile(user_id: int) -> dict:
    """
    Load a user's learner profile from SQLite.

    Returns a normalized profile dict compatible with memory_agent.py
    """
    create_profile_if_missing(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM profiles WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        # fallback safety
        profile = ensure_profile_structure({})
        return profile

    profile = {
        "sessions": row["sessions"] if row["sessions"] is not None else 0,
        "questions_asked": row["questions_asked"] if row["questions_asked"] is not None else 0,
        "last_level": row["last_level"] if row["last_level"] else "beginner",

        "topics_seen": _safe_json_load(row["topics_seen"], []),
        "level_history": _safe_json_load(row["level_history"], []),
        "topic_counts": _safe_json_load(row["topic_counts"], {}),
        "weak_areas": _safe_json_load(row["weak_areas"], {}),
        "mastery": _safe_json_load(row["mastery"], {}),
        "used_explanations": _safe_json_load(row["used_explanations"], {}),
        "recommended_next_topics": _safe_json_load(row["recommended_next_topics"], []),
    }

    profile = ensure_profile_structure(profile)
    return profile


def save_profile(user_id: int, profile: dict):
    """
    Save a user's learner profile back to SQLite.
    """
    profile = ensure_profile_structure(profile)
    create_profile_if_missing(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE profiles
        SET
            sessions = ?,
            questions_asked = ?,
            last_level = ?,
            topics_seen = ?,
            level_history = ?,
            topic_counts = ?,
            weak_areas = ?,
            mastery = ?,
            used_explanations = ?,
            recommended_next_topics = ?
        WHERE user_id = ?
        """,
        (
            profile["sessions"],
            profile["questions_asked"],
            profile["last_level"],
            json.dumps(profile["topics_seen"]),
            json.dumps(profile["level_history"]),
            json.dumps(profile["topic_counts"]),
            json.dumps(profile["weak_areas"]),
            json.dumps(profile["mastery"]),
            json.dumps(profile["used_explanations"]),
            json.dumps(profile["recommended_next_topics"]),
            user_id,
        )
    )

    conn.commit()
    conn.close()


def create_user(name: str, username: str, email: str, password_hash: str):
    """
    Create a user row in the current users schema.
    `username` is accepted for compatibility but not stored in this schema.
    """
    _ = username
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {row["name"] for row in cursor.fetchall()}
    try:
        if {"name", "email", "password_hash", "created_at"}.issubset(user_cols):
            cursor.execute(
                """
                INSERT INTO users (name, username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, username, email, password_hash, datetime.utcnow().isoformat() + "Z"),
            )
        else:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash),
            )
        user_id = cursor.lastrowid
        conn.commit()
    except Exception:
        conn.close()
        return None
    conn.close()
    create_profile_if_missing(user_id)
    return user_id


def get_user_by_identifier(identifier: str):
    """
    Fetch user by email (identifier kept generic for compatibility).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {row["name"] for row in cursor.fetchall()}
    if "user_id" in user_cols:
        cursor.execute(
            """
            SELECT user_id, name, username, email, password_hash, created_at
            FROM users
            WHERE email = ? OR username = ?
            """,
            (identifier, identifier),
        )
    else:
        cursor.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (identifier,),
        )
    row = cursor.fetchone()
    conn.close()
    return row