from sqlalchemy import text
from database import engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def register_user(phone_number: str, password: str):
    hashed = pwd_context.hash(password)

    with engine.begin() as conn:
        # create user and get id (Postgres needs RETURNING instead of lastrowid)
        result = conn.execute(
            text("""
                INSERT INTO users (phone, password_hash)
                VALUES (:p, :h)
                RETURNING id
            """),
            {"p": phone_number, "h": hashed}
        )

        user_id = result.scalar_one()

        # create wallet
        conn.execute(
            text("""
                INSERT INTO wallets (user_id, balance)
                VALUES (:u, 0)
            """),
            {"u": user_id}
        )


def authenticate_user(phone_number: str, password: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, password_hash
                FROM users
                WHERE phone = :p
            """),
            {"p": phone_number}
        ).fetchone()

        if not row:
            return None

        if not pwd_context.verify(password, row[1]):
            return None

        return int(row[0])

