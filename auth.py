from argon2 import PasswordHasher
from sqlalchemy import text
from database import engine

ph = PasswordHasher()

def authenticate_admin(username: str, password: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT password_hash FROM admins "
                "WHERE username = :username AND status = 'active'"
            ),
            {"username": username}
        ).fetchone()

        if not result:
            return False

        stored_hash = result[0]

        try:
            ph.verify(stored_hash, password)
            return True
        except Exception:
            return False
