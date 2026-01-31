import random
import threading
from datetime import datetime
from sqlalchemy import text
from database import engine
from services.multiplier_service import run_multiplier


# -------------------
# CRASH RNG
# -------------------
def generate_crash_point():
    r = random.random()
    if r < 0.7:
        return round(random.uniform(1.0, 2.0), 2)
    elif r < 0.9:
        return round(random.uniform(2.0, 4.0), 2)
    elif r < 0.98:
        return round(random.uniform(4.0, 10.0), 2)
    else:
        crash = round(random.uniform(10.0, 20.0), 2)
        return min(crash, 20.0)  # Hard cap at 20x


# -------------------
# ROUND CONTROL
# -------------------
def create_new_round():
    crash = generate_crash_point()
    now = datetime.utcnow()

    with engine.begin() as conn:
        active = conn.execute(
            text("""
                SELECT id FROM game_rounds
                WHERE status IN ('open','running')
                LIMIT 1
            """)
        ).fetchone()

        if active:
            return None

        conn.execute(
            text("""
                INSERT INTO game_rounds
                (crash_point, status, betting_close_at, created_at)
                VALUES (:c, 'open', :n + INTERVAL '5 seconds', :n)
            """),
            {"c": crash, "n": now}
        )

    return crash


def start_round(round_id):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE game_rounds
                SET status='running', started_at=:n
                WHERE id=:r
            """),
            {"r": round_id, "n": datetime.utcnow()}
        )


def crash_round(round_id):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE game_rounds
                SET status='crashed', ended_at=:n
                WHERE id=:r
            """),
            {"r": round_id, "n": datetime.utcnow()}
        )


def close_round(round_id):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE game_rounds
                SET status='closed'
                WHERE id=:r
            """),
            {"r": round_id}
        )


def get_current_round():
    with engine.connect() as conn:
        return conn.execute(
            text("""
                SELECT id, crash_point, status, betting_close_at
                FROM game_rounds
                WHERE status IN ('open','running')
                ORDER BY id DESC
                LIMIT 1
            """)
        ).fetchone()

def get_recent_rounds(limit=20):
    """Get recent completed rounds with their crash points"""
    with engine.connect() as conn:
        results = conn.execute(
            text("""
                SELECT crash_point, ended_at
                FROM game_rounds
                WHERE ended_at IS NOT NULL
                AND status IN ('crashed', 'closed')
                ORDER BY id DESC
                LIMIT :limit
            """),
            {"limit": limit}
        ).fetchall()
        
        return [{"crash_point": float(row[0]), "ended_at": row[1]} for row in results]

# -------------------
# GAME LOOP (THREAD)
# -------------------
def game_loop():
    import time

    while True:
        result = create_new_round()
        if not result:
            time.sleep(1)
            continue

        with engine.connect() as conn:
            round_id, crash, *_ = conn.execute(
                text("""
                    SELECT id, crash_point
                    FROM game_rounds
                    WHERE status='open'
                    ORDER BY id DESC LIMIT 1
                """)
            ).fetchone()

        time.sleep(5)  # betting window
        start_round(round_id)

        t = threading.Thread(
            target=run_multiplier,
            args=(round_id, crash),
            daemon=False
        )
        t.start()

        # Wait for the round to complete before starting next one
        t.join()
        time.sleep(2)  # buffer before next round
