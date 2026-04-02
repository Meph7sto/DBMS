"""Connection management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db


router = APIRouter(tags=["connection"])


class ConnectRequest(BaseModel):
    host: str = "localhost"
    port: int = 5438
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"


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
