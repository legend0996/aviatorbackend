from sqlalchemy import text
from database import engine


def get_user_id(phone_number: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM users WHERE phone_number = :p"),
            {"p": phone_number}
        ).fetchone()

        if not row:
            return None

        return int(row[0])
