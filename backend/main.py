"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import API_PREFIX, CORS_ORIGINS
from routers import connection, explore, query


app = FastAPI(
    title="DBMS Visual Manager",
    description="Visual database management interface",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router, prefix=API_PREFIX)
app.include_router(explore.router, prefix=API_PREFIX)
app.include_router(query.router, prefix=API_PREFIX)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
