from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text

from database import engine, init_db_schema, ensure_admin_user

from auth import authenticate_admin
from jwt_utils import create_access_token
from dependencies import require_admin_token

from services.settings_service import get_settings, update_settings
from services.wallet_service import (
    get_wallet,
    credit_wallet,
    debit_wallet,
    create_pending_deposit,
)
from services.user_service import get_user_id
from services.auth_service import register_user, authenticate_user
from services.mpesa_service_mock import stk_push, b2c_withdraw  # Use mock by default

from services.aviator_service import get_current_round, get_recent_rounds
from services.bet_service import place_bet

from database import Base

Base.metadata.create_all(bind=engine)


# -------------------
# APP SETUP
# -------------------
app = FastAPI(
    title="Aviator Backend API",
    version="1.0.0",
    description="Backend API with JWT authentication"
)

# -------------------
# CORS CONFIGURATION
# -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "https://aviatorfrontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------
# REQUEST MODELS
# -------------------
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class UserAuthRequest(BaseModel):
    phone: str
    password: str


class SettingsUpdate(BaseModel):
    min_deposit: float
    min_withdraw: float
    deposit_enabled: bool
    withdraw_enabled: bool


class WalletAmountRequest(BaseModel):
    amount: float


class BetRequest(BaseModel):
    amount: float
    auto_cashout: float | None = None


# -------------------
# PUBLIC ROUTES
# -------------------
@app.get("/")
def root():
    return {"status": "Backend running"}


# -------------------
# AVIATOR ROUND INFO
# -------------------
@app.get("/aviator/round")
def aviator_round():
    round_data = get_current_round()
    if not round_data:
        return {"round": None}

    return {
        "round_id": round_data[0],
        "crash_point": float(round_data[1]) if round_data[1] is not None else None,
        "status": round_data[2],
        "betting_close_at": round_data[3],
    }


@app.get("/aviator/recent")
def aviator_recent():
    """Get recent completed rounds"""
    rounds = get_recent_rounds(limit=20)
    return {"recent_rounds": rounds}


# -------------------
# AVIATOR BET
# -------------------
@app.post("/aviator/bet")
def aviator_bet(
    data: BetRequest,
    payload: dict = Depends(require_admin_token),
):
    user_id = get_user_id(payload["sub"])
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    place_bet(
        user_id=user_id,
        amount=data.amount,
        auto_cashout=data.auto_cashout,
    )

    return {"success": True}


# -------------------
# ADMIN AUTH
# -------------------
@app.post("/admin/login")
def admin_login(data: AdminLoginRequest):
    if not authenticate_admin(data.username, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": data.username})
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
    }


# -------------------
# USER AUTH (PHONE)
# -------------------
@app.post("/auth/register")
def user_register(data: UserAuthRequest):
    try:
        register_user(data.phone, data.password)
        return {"success": True, "message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@app.post("/auth/login")
def user_login(data: UserAuthRequest):
    user_id = authenticate_user(data.phone, data.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": data.phone})
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "phone_number": data.phone
        }
    }


# -------------------
# ADMIN PROTECTED ROUTES
# -------------------
@app.get("/admin/protected")
def admin_protected(payload: dict = Depends(require_admin_token)):
    return {
        "message": "You are authorized",
        "admin": payload["sub"],
    }


@app.get("/admin/settings")
def read_settings(payload: dict = Depends(require_admin_token)):
    settings = get_settings()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@app.put("/admin/settings")
def edit_settings(
    data: SettingsUpdate,
    payload: dict = Depends(require_admin_token),
):
    update_settings(
        data.min_deposit,
        data.min_withdraw,
        data.deposit_enabled,
        data.withdraw_enabled,
    )
    return {"success": True, "message": "Settings updated"}


# -------------------
# WALLET ROUTES
# -------------------
@app.get("/wallet/balance")
def wallet_balance(payload: dict = Depends(require_admin_token)):
    user_id = get_user_id(payload["sub"])
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    return {"balance": get_wallet(user_id)}


@app.post("/wallet/deposit/stk")
def wallet_stk_deposit(
    data: WalletAmountRequest,
    payload: dict = Depends(require_admin_token),
):
    phone = payload["sub"]
    user_id = get_user_id(phone)

    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    reference = f"stk_{user_id}_{int(data.amount)}"

    create_pending_deposit(
        user_id=user_id,
        amount=data.amount,
        reference=reference,
    )

    response = stk_push(
        phone=phone,
        amount=data.amount,
        reference=reference,
    )

    return {"success": True, "mpesa": response}


@app.post("/wallet/withdraw/mpesa")
def wallet_withdraw_mpesa(
    data: WalletAmountRequest,
    payload: dict = Depends(require_admin_token),
):
    phone = payload["sub"]
    user_id = get_user_id(phone)

    debit_wallet(
        user_id=user_id,
        amount=data.amount,
        tx_type="withdraw",
        reference="mpesa_withdraw",
    )

    response = b2c_withdraw(phone, data.amount)
    return {"success": True, "mpesa": response}


# -------------------
# M-PESA STK CALLBACK
# -------------------
@app.post("/mpesa/stk/callback")
def stk_callback(payload: dict):
    callback = payload["Body"]["stkCallback"]
    result_code = callback["ResultCode"]

    if result_code != 0:
        return {"ResultCode": 0}

    metadata = callback["CallbackMetadata"]["Item"]
    amount = next(i["Value"] for i in metadata if i["Name"] == "Amount")
    reference = next(i["Value"] for i in metadata if i["Name"] == "AccountReference")

    with engine.begin() as conn:
        tx = conn.execute(
            text("""
                SELECT user_id
                FROM transactions
                WHERE reference = :r AND status = 'pending'
            """),
            {"r": reference},
        ).fetchone()

        if not tx:
            return {"ResultCode": 0}

        conn.execute(
            text("""
                UPDATE transactions
                SET status = 'completed'
                WHERE reference = :r
            """),
            {"r": reference},
        )

    credit_wallet(
        user_id=tx[0],
        amount=amount,
        tx_type="deposit",
        reference=reference,
    )

    return {"ResultCode": 0}


# -------------------
# SWAGGER JWT SUPPORT
# -------------------
from services.aviator_service import game_loop
import threading


@app.on_event("startup")
def start_aviator_engine():
    init_db_schema()
    ensure_admin_user()
    t = threading.Thread(target=game_loop, daemon=True)
    t.start()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
