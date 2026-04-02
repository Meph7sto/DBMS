"""SQL query execution endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db


router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    sql: str


@router.post("/query")
def execute_query(req: QueryRequest):
    stripped = req.sql.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="Empty query")

    try:
        result = db.execute(stripped)
        return {"ok": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
