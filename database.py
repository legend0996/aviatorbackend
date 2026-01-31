import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load .env locally (Render ignores this safely)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def init_db_schema():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admins (
                id BIGSERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'support',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_settings (
                setting_key VARCHAR(50) PRIMARY KEY,
                setting_value VARCHAR(255),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                phone VARCHAR(20) UNIQUE NOT NULL,
                username VARCHAR(50),
                password_hash VARCHAR(255) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS wallets (
                user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                balance NUMERIC(12,2) DEFAULT 0.00,
                bonus_balance NUMERIC(12,2) DEFAULT 0.00,
                locked_balance NUMERIC(12,2) DEFAULT 0.00,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS game_rounds (
                id BIGSERIAL PRIMARY KEY,
                crash_point NUMERIC(6,2) NOT NULL,
                current_multiplier NUMERIC(6,2) DEFAULT 1.00,
                status VARCHAR(20) DEFAULT 'open',
                server_seed VARCHAR(128),
                client_seed VARCHAR(64),
                nonce INT,
                server_hash VARCHAR(128),
                betting_close_at TIMESTAMPTZ,
                started_at TIMESTAMPTZ,
                ended_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            ALTER TABLE game_rounds
            ADD COLUMN IF NOT EXISTS current_multiplier NUMERIC(6,2) DEFAULT 1.00
        """))

        conn.execute(text("""
            ALTER TABLE game_rounds
            ADD COLUMN IF NOT EXISTS server_seed VARCHAR(128),
            ADD COLUMN IF NOT EXISTS client_seed VARCHAR(64),
            ADD COLUMN IF NOT EXISTS nonce INT,
            ADD COLUMN IF NOT EXISTS server_hash VARCHAR(128)
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bets (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id),
                round_id BIGINT NOT NULL REFERENCES game_rounds(id),
                bet_amount NUMERIC(10,2) NOT NULL,
                cashout_multiplier NUMERIC(6,2),
                auto_cashout NUMERIC(6,2),
                payout NUMERIC(12,2) DEFAULT 0.00,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            ALTER TABLE bets
            ADD COLUMN IF NOT EXISTS auto_cashout NUMERIC(6,2)
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mpesa_transactions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id),
                phone VARCHAR(20) NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                mpesa_code VARCHAR(20),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id),
                type VARCHAR(20) NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                balance_before NUMERIC(12,2) DEFAULT 0.00,
                balance_after NUMERIC(12,2) DEFAULT 0.00,
                status VARCHAR(20) DEFAULT 'completed',
                reference VARCHAR(100),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS bets_user_id_idx ON bets(user_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS bets_round_id_idx ON bets(round_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS transactions_user_id_idx ON transactions(user_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS mpesa_transactions_user_id_idx ON mpesa_transactions(user_id)
        """))

        conn.execute(text("""
            INSERT INTO admin_settings (setting_key, setting_value)
            VALUES
                ('min_deposit', '100'),
                ('min_withdraw', '100'),
                ('deposit_enabled', 'true'),
                ('withdraw_enabled', 'true')
            ON CONFLICT (setting_key) DO NOTHING
        """))


def ensure_admin_user():
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    if not username or not password:
        return

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM admins WHERE username = :u"),
            {"u": username}
        ).fetchone()

        if existing:
            return

        hashed = pwd_context.hash(password)
        conn.execute(
            text("""
                INSERT INTO admins (username, password_hash, role, status)
                VALUES (:u, :p, 'super', 'active')
            """),
            {"u": username, "p": hashed}
        )
