from auth.password_utils import hash_password, verify_password
from db.profile_repository import create_user, get_user_by_identifier


def register_user(name, username, email, password):
    name = (name or "").strip()
    username = (username or "").strip().lower() or None
    email = (email or "").strip().lower()
    password = password or ""
    if not name or not email or len(password) < 6:
        return False, "Name, email, and password (min 6 chars) are required."

    password_hash = hash_password(password)
    user_id = create_user(name, username, email, password_hash)
    if not user_id:
        return False, "Email or username already exists."
    return True, "Signup successful. Please log in."


def authenticate_user(identifier, password):
    identifier = (identifier or "").strip().lower()
    password = password or ""
    if not identifier or not password:
        return None, "Enter email/username and password."

    row = get_user_by_identifier(identifier)
    if not row:
        return None, "Invalid credentials."
    if not verify_password(password, row["password_hash"]):
        return None, "Invalid credentials."
    user_id = row["id"] if "id" in row.keys() else row["user_id"]
    return {
        "user_id": user_id,
        "name": row["name"],
        "email": row["email"],
    }, "Login successful."


def signup_user(name, email, password, username=None):
    """
    Backward-compatible wrapper used by app.main.
    """
    return register_user(name=name, username=username, email=email, password=password)


def login_user(email, password):
    """
    Backward-compatible wrapper used by app.main.
    Returns: success(bool), message(str), user(dict|None)
    """
    user, message = authenticate_user(identifier=email, password=password)
    if not user:
        return False, message, None
    return True, message, {
        "id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
    }
