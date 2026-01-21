from sqlalchemy import text
from database import engine


def get_settings():
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT 
                    min_deposit,
                    min_withdraw,
                    deposit_enabled,
                    withdraw_enabled
                FROM admin_settings
                LIMIT 1
            """)
        ).fetchone()

        if not result:
            return None

        return {
            "min_deposit": float(result[0]),
            "min_withdraw": float(result[1]),
            "deposit_enabled": bool(result[2]),
            "withdraw_enabled": bool(result[3]),
        }


def update_settings(
    min_deposit: float,
    min_withdraw: float,
    deposit_enabled: bool,
    withdraw_enabled: bool,
):
    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE admin_settings
                SET 
                    min_deposit = :min_deposit,
                    min_withdraw = :min_withdraw,
                    deposit_enabled = :deposit_enabled,
                    withdraw_enabled = :withdraw_enabled
            """),
            {
                "min_deposit": min_deposit,
                "min_withdraw": min_withdraw,
                "deposit_enabled": deposit_enabled,
                "withdraw_enabled": withdraw_enabled,
            }
        )
        conn.commit()
