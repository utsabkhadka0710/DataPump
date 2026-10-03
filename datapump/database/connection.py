import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

load_dotenv()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

# postgresql://username:password@host:port/db_name
conn_info = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
db_pool = AsyncConnectionPool(
    conninfo=conn_info,
    min_size=1,
    max_size=10,
    open=False,
    kwargs={"row_factory":dict_row}
)

@asynccontextmanager
async def conn_pool_lifespan(app: FastAPI):
    await db_pool.open()
    await db_pool.wait()
    print("Database connection pool established sucessfully")
    yield
    print("Database connection pool closing...")
    await db_pool.close()
    print("Database connection pool closed sucessfully")