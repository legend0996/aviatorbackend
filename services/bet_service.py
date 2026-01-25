from sqlalchemy import text
from database import engine
from services.wallet_service import debit_wallet
from services.aviator_service import get_current_round


MAX_BET = 50000


def place_bet(user_id: int, amount: float, auto_cashout: float | None):
    if amount <= 0:
        raise ValueError("Invalid bet amount")

    if amount > MAX_BET:
        raise ValueError("Bet exceeds max limit")

    round_data = get_current_round()
    if not round_data:
        raise ValueError("No active round")

    round_id, _, status, betting_close_at = round_data

    if status != "open":
        raise ValueError("Betting closed")

    # debit wallet immediately
    debit_wallet(
        user_id=user_id,
        amount=amount,
        tx_type="bet",
        reference=f"bet_round_{round_id}"
    )

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO bets
                (user_id, round_id, amount, auto_cashout, status)
                VALUES (:u, :r, :a, :ac, 'active')
            """),
            {
                "u": user_id,
                "r": round_id,
                "a": amount,
                "ac": auto_cashout
            }
        )
