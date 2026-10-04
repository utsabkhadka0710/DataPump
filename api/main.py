from fastapi import FastAPI
from psycopg import AsyncConnection
from collections.abc import AsyncGenerator

from datapump import db_pool, conn_pool_lifespan



app = FastAPI(lifespan=conn_pool_lifespan)

async def get_db_conn() -> AsyncGenerator[AsyncConnection]:
    async with db_pool.connection() as conn:
        yield conn


@app.get("/health")
async def health():
    return{
        "response": "API is up and running healthy..."
    }

@app.get("/")
async def home():
    return{
        "response": "DataPump is an data ingestion pipeline with FastAPI+PostgreSQL."
    }

@app.get("/check-db-conn")
async def check_db_conn():
    async with db_pool.connection() as conn:
        data = await conn.execute("SELECT 'DB connection okay!' as response")
        return await data.fetchone()
