from sqlalchemy import text
from database import engine


# -------------------
# ADMIN SETTINGS
# -------------------
def get_admin_settings(conn):
    row = conn.execute(
        text("""
            SELECT min_deposit, min_withdraw, deposit_enabled, withdraw_enabled
            FROM admin_settings
            LIMIT 1
        """)
    ).fetchone()

    if not row:
        raise ValueError("Admin settings not configured")

    return {
        "min_deposit": float(row[0]),
        "min_withdraw": float(row[1]),
        "deposit_enabled": bool(row[2]),
        "withdraw_enabled": bool(row[3]),
    }


# -------------------
# WALLET QUERIES
# -------------------
def get_wallet(user_id: int):
    with engine.connect() as conn:
        wallet = conn.execute(
            text("SELECT balance FROM wallets WHERE user_id = :u"),
            {"u": user_id}
        ).fetchone()

        if not wallet:
            return None

        return float(wallet[0])


# -------------------
# CREDIT (DEPOSIT / WIN)
# -------------------
def credit_wallet(user_id: int, amount: float, tx_type: str, reference: str):
    if amount <= 0:
        raise ValueError("Amount must be positive")

    with engine.begin() as conn:
        settings = get_admin_settings(conn)

        if not settings["deposit_enabled"]:
            raise ValueError("Deposits are disabled")

        if amount < settings["min_deposit"]:
            raise ValueError("Deposit below minimum limit")

        conn.execute(
            text("""
                INSERT INTO transactions (user_id, amount, type, status, reference)
                VALUES (:u, :a, :t, 'completed', :r)
            """),
            {"u": user_id, "a": amount, "t": tx_type, "r": reference}
        )

        conn.execute(
            text("""
                UPDATE wallets
                SET balance = balance + :a
                WHERE user_id = :u
            """),
            {"a": amount, "u": user_id}
        )


# -------------------
# DEBIT (WITHDRAW / BET)
# -------------------
def debit_wallet(user_id: int, amount: float, tx_type: str, reference: str):
    if amount <= 0:
        raise ValueError("Amount must be positive")

    with engine.begin() as conn:
        settings = get_admin_settings(conn)

        if not settings["withdraw_enabled"]:
            raise ValueError("Withdrawals are disabled")

        if amount < settings["min_withdraw"]:
            raise ValueError("Withdraw below minimum limit")

        wallet = conn.execute(
            text("""
                SELECT balance FROM wallets
                WHERE user_id = :u
                FOR UPDATE
            """),
            {"u": user_id}
        ).fetchone()

        if not wallet:
            raise ValueError("Wallet not found")

        balance = float(wallet[0])
        if balance < amount:
            raise ValueError("Insufficient balance")

        conn.execute(
            text("""
                INSERT INTO transactions (user_id, amount, type, status, reference)
                VALUES (:u, :a, :t, 'completed', :r)
            """),
            {"u": user_id, "a": -amount, "t": tx_type, "r": reference}
        )

        conn.execute(
            text("""
                UPDATE wallets
                SET balance = balance - :a
                WHERE user_id = :u
            """),
            {"a": amount, "u": user_id}
        )


# -------------------
# PENDING DEPOSIT (M-PESA)
# -------------------
def create_pending_deposit(user_id: int, amount: float, reference: str):
    with engine.begin() as conn:
        settings = get_admin_settings(conn)

        if not settings["deposit_enabled"]:
            raise ValueError("Deposits are disabled")

        if amount < settings["min_deposit"]:
            raise ValueError("Deposit below minimum")

        conn.execute(
            text("""
                INSERT INTO transactions (user_id, amount, type, status, reference)
                VALUES (:u, :a, 'deposit', 'pending', :r)
            """),
            {"u": user_id, "a": amount, "r": reference}
        )
