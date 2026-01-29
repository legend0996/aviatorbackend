from sqlalchemy import text
from database import engine


# -------------------
# ADMIN SETTINGS
# -------------------
def get_admin_settings(conn):
    # Get individual settings from key-value store
    rows = conn.execute(
        text("""
            SELECT setting_key, setting_value
            FROM admin_settings
        """)
    ).fetchall()

    if not rows:
        # Return defaults if no settings
        return {
            "min_deposit": 100,
            "min_withdraw": 100,
            "deposit_enabled": True,
            "withdraw_enabled": True,
        }

    settings = {}
    for row in rows:
        settings[row[0]] = row[1]

    return {
        "min_deposit": float(settings.get("min_deposit", "100")),
        "min_withdraw": float(settings.get("min_withdraw", "100")),
        "deposit_enabled": settings.get("deposit_enabled", "true").lower() == "true",
        "withdraw_enabled": settings.get("withdraw_enabled", "true").lower() == "true",
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

        # Get current balance
        wallet = conn.execute(
            text("SELECT balance FROM wallets WHERE user_id = :u FOR UPDATE"),
            {"u": user_id}
        ).fetchone()
        
        if not wallet:
            raise ValueError("Wallet not found")
        
        balance_before = float(wallet[0])
        balance_after = balance_before + amount

        # Insert transaction with balance info
        conn.execute(
            text("""
                INSERT INTO transactions (user_id, amount, type, balance_before, balance_after, status, reference)
                VALUES (:u, :a, :t, :bb, :ba, 'completed', :r)
            """),
            {"u": user_id, "a": amount, "t": tx_type, "bb": balance_before, "ba": balance_after, "r": reference}
        )

        # Update wallet
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

        balance_before = float(wallet[0])
        if balance_before < amount:
            raise ValueError("Insufficient balance")

        balance_after = balance_before - amount

        # Insert transaction with balance info
        conn.execute(
            text("""
                INSERT INTO transactions (user_id, amount, type, balance_before, balance_after, status, reference)
                VALUES (:u, :a, :t, :bb, :ba, 'completed', :r)
            """),
            {"u": user_id, "a": amount, "t": tx_type, "bb": balance_before, "ba": balance_after, "r": reference}
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

        # Get current balance
        wallet = conn.execute(
            text("SELECT balance FROM wallets WHERE user_id = :u FOR UPDATE"),
            {"u": user_id}
        ).fetchone()
        
        if not wallet:
            raise ValueError("Wallet not found")
        
        balance_before = float(wallet[0])

        conn.execute(
            text("""
                INSERT INTO transactions (user_id, amount, type, balance_before, balance_after, status, reference)
                VALUES (:u, :a, 'deposit', :bb, :bb, 'pending', :r)
            """),
            {"u": user_id, "a": amount, "bb": balance_before, "r": reference}
        )
