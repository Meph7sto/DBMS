"""Connection management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db
from config import get_default_connection


router = APIRouter(tags=["connection"])

defaults = get_default_connection()

class ConnectRequest(BaseModel):
    host: str = defaults["host"]
    port: int = defaults["port"]
    user: str = defaults["user"]
    password: str = defaults["password"]
    database: str = defaults["database"]


@router.get("/connect/defaults")
def connection_defaults():
    return get_default_connection()


@router.post("/connect")
def connect(req: ConnectRequest):
    try:
        info = db.connect(
            host=req.host,
            port=req.port,
            user=req.user,
            password=req.password,
            database=req.database,
        )
        return {"ok": True, "connection": info}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/connect")
def disconnect():
    db.disconnect()
    return {"ok": True}


@router.get("/connect")
def connection_status():
    if db.is_connected:
        return {"connected": True, "connection": db.connection_info}
    return {"connected": False}
