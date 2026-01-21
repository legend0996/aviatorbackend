from services.settings_service import get_settings, update_settings

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.openapi.utils import get_openapi

from auth import authenticate_admin
from jwt_utils import create_access_token
from dependencies import require_admin_token


# -------------------
# APP SETUP
# -------------------
app = FastAPI(
    title="Aviator Backend API",
    version="1.0.0",
    description="Backend API with JWT authentication"
)


# -------------------
# MODELS
# -------------------
class LoginRequest(BaseModel):
    username: str
    password: str
class SettingsUpdate(BaseModel):
    min_deposit: float
    min_withdraw: float
    deposit_enabled: bool
    withdraw_enabled: bool


# -------------------
# PUBLIC ROUTES
# -------------------
@app.get("/")
def root():
    return {"status": "Backend running"}


@app.post("/admin/login")
def admin_login(data: LoginRequest):
    if not authenticate_admin(data.username, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": data.username})
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer"
    }


# -------------------
# PROTECTED ROUTES
# -------------------
@app.get("/admin/protected")
def admin_protected(payload: dict = Depends(require_admin_token)):
    return {
        "message": "You are authorized",
        "admin": payload["sub"]
    }
from services.settings_service import get_settings, update_settings


class SettingsUpdate(BaseModel):
    min_deposit: float
    min_withdraw: float
    deposit_enabled: bool
    withdraw_enabled: bool


@app.get("/admin/settings")
def read_settings(payload: dict = Depends(require_admin_token)):
    return get_settings()


@app.put("/admin/settings")
def edit_settings(
    data: SettingsUpdate,
    payload: dict = Depends(require_admin_token)
):
    update_settings(
        data.min_deposit,
        data.min_withdraw,
        data.deposit_enabled,
        data.withdraw_enabled,
    )
    return {"success": True}

@app.get("/admin/settings")
def read_settings(payload: dict = Depends(require_admin_token)):
    settings = get_settings()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@app.put("/admin/settings")
def edit_settings(
    data: SettingsUpdate,
    payload: dict = Depends(require_admin_token)
):
    update_settings(
        data.min_deposit,
        data.min_withdraw,
        data.deposit_enabled,
        data.withdraw_enabled,
    )
    return {"success": True, "message": "Settings updated"}


# -------------------
# SWAGGER JWT SUPPORT
# -------------------
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
            "bearerFormat": "JWT"
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

