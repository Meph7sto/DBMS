"""Database exploration endpoints — databases, schemas, tables."""

from fastapi import APIRouter, HTTPException, Query
from psycopg2 import sql as psql
from database import db


router = APIRouter(tags=["explore"])


@router.get("/databases")
def list_databases():
    try:
        result = db.execute(
            "SELECT datname AS name FROM pg_database "
            "WHERE datistemplate = false ORDER BY datname"
        )
        return result["rows"]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/schemas")
def list_schemas():
    try:
        result = db.execute(
            "SELECT schema_name AS name FROM information_schema.schemata "
            "WHERE schema_name NOT IN "
            "('pg_catalog','information_schema','pg_toast') "
            "ORDER BY schema_name"
        )
        return result["rows"]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/tables")
def list_tables(schema: str = Query("public")):
    try:
        result = db.execute(
            "SELECT table_name AS name, table_type AS type "
            "FROM information_schema.tables "
            "WHERE table_schema = %s ORDER BY table_name",
            (schema,),
        )
        return result["rows"]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/tables/{schema}/{name}")
def table_detail(schema: str, name: str):
    try:
        columns = db.execute(
            "SELECT column_name, data_type, is_nullable, column_default, "
            "character_maximum_length "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY ordinal_position",
            (schema, name),
        )
        constraints = db.execute(
            "SELECT constraint_name, constraint_type "
            "FROM information_schema.table_constraints "
            "WHERE table_schema = %s AND table_name = %s",
            (schema, name),
        )
        indexes = db.execute(
            "SELECT indexname, indexdef "
            "FROM pg_indexes "
            "WHERE schemaname = %s AND tablename = %s",
            (schema, name),
        )
        row_count = db.execute(
            "SELECT reltuples::bigint AS estimate FROM pg_class "
            "WHERE oid = %s::regclass",
            (f"{schema}.{name}",),
        )
        return {
            "schema": schema,
            "name": name,
            "columns": columns["rows"],
            "constraints": constraints["rows"],
            "indexes": indexes["rows"],
            "row_estimate": (
                row_count["rows"][0]["estimate"] if row_count["rows"] else 0
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/tables/{schema}/{name}/data")
def table_data(
    schema: str,
    name: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
):
    try:
        offset = (page - 1) * size
        query = psql.SQL("SELECT * FROM {}.{} LIMIT %s OFFSET %s").format(
            psql.Identifier(schema), psql.Identifier(name)
        )
        result = db.execute(query, (size, offset))

        count_query = psql.SQL("SELECT count(*) AS total FROM {}.{}").format(
            psql.Identifier(schema), psql.Identifier(name)
        )
        count_result = db.execute(count_query)
        total = count_result["rows"][0]["total"] if count_result["rows"] else 0

        return {
            "columns": result.get("columns", []),
            "rows": result.get("rows", []),
            "page": page,
            "size": size,
            "total": total,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
