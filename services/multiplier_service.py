import time
from datetime import datetime
from sqlalchemy import text
from database import engine
from services.wallet_service import credit_wallet


MULTIPLIER_GROWTH_RATE = 0.35  # speed of plane (increased for faster rounds)


def run_multiplier(round_id: int, crash_point: float):
    """
    Simulates multiplier growth until crash point
    """
    multiplier = 1.00

    while multiplier < crash_point:
        time.sleep(0.05)  # reduced from 0.1 for smoother/faster gameplay
        multiplier = round(multiplier + MULTIPLIER_GROWTH_RATE, 2)

        # auto cashout
        with engine.begin() as conn:
            bets = conn.execute(
                text("""
                    SELECT id, user_id, amount, auto_cashout
                    FROM bets
                    WHERE round_id = :r
                    AND status = 'active'
                    AND auto_cashout IS NOT NULL
                    AND auto_cashout <= :m
                """),
                {"r": round_id, "m": multiplier}
            ).fetchall()

            for bet_id, user_id, amount, auto in bets:
                win_amount = round(amount * auto, 2)

                conn.execute(
                    text("""
                        UPDATE bets
                        SET status='won', cashout_multiplier=:m
                        WHERE id=:b
                    """),
                    {"b": bet_id, "m": auto}
                )

                credit_wallet(
                    user_id=user_id,
                    amount=win_amount,
                    tx_type="win",
                    reference=f"auto_cashout_{bet_id}"
                )

    # CRASH - Update round status directly
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE game_rounds
                SET status='crashed', ended_at=:n
                WHERE id=:r
            """),
            {"r": round_id, "n": datetime.utcnow()}
        )

    # lose remaining bets
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE bets
                SET status='lost'
                WHERE round_id=:r AND status='active'
            """),
            {"r": round_id}
        )

    time.sleep(2)
    
    # CLOSE - Close the round directly
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE game_rounds
                SET status='closed'
                WHERE id=:r
            """),
            {"r": round_id}
        )
