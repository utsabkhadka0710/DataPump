"""Database connection management and FastAPI lifespan configuration for DataPump.

This module initializes environment variables, configures the asynchronous
PostgreSQL connection pool using psycopg, and provides a FastAPI lifespan context
manager for managing the connection pool's lifecycle during application startup
and shutdown.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

load_dotenv()

db_user: str | None = os.getenv("DB_USER")
db_password: str | None = os.getenv("DB_PASSWORD")
db_host: str | None = os.getenv("DB_HOST")
db_port: str | None = os.getenv("DB_PORT")
db_name: str | None = os.getenv("DB_NAME")

# postgresql://username:password@host:port/db_name
conn_info: str = (
    f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)

db_pool: AsyncConnectionPool = AsyncConnectionPool(
    conninfo=conn_info,
    min_size=1,
    max_size=10,
    timeout=5,
    open=False,
    kwargs={"row_factory": dict_row},
)


@asynccontextmanager
async def conn_pool_lifespan(app: FastAPI):
    """Manages the database connection pool lifecycle for the FastAPI application.

    Opens and waits for the asynchronous connection pool to be ready upon
    application startup, and gracefully closes the pool upon application
    shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control is yielded back to the FastAPI runtime during application
        execution.
    """
    await db_pool.open()
    await db_pool.wait()
    print("Database connection pool established sucessfully")
    yield
    print("Database connection pool closing...")
    await db_pool.close()
    print("Database connection pool closed sucessfully")