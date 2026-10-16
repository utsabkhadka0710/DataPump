"""Main FastAPI application module for DataPump.

This module initializes the FastAPI application, configures global exception
handlers and application lifespan events, defines database dependency injection
providers, and sets up API routing for health checks, system status, and job management.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from psycopg import AsyncConnection
from psycopg_pool import PoolClosed, PoolTimeout

from datapump import (
    DatabaseConnectionPoolClosed,
    DatabaseConnectionPoolTimeout,
    conn_pool_lifespan,
    db_pool,
)

from .exceptions import register_exceptions_handler
from .handler.get_jobs import get_jobs_handler
from .handler.post_jobs import post_jobs_handler
from .models import JobCreate, JobResponse

app: FastAPI = FastAPI(lifespan=conn_pool_lifespan)
register_exceptions_handler(app=app)


async def get_db_conn() -> AsyncGenerator[AsyncConnection, None]:
    """Provides an asynchronous database connection from the connection pool.

    Yields:
        AsyncConnection: An active asynchronous database connection instance.

    Raises:
        DatabaseConnectionPoolTimeout: If acquiring a connection exceeds the timeout limit.
        DatabaseConnectionPoolClosed: If attempting to acquire a connection from a closed pool.
    """
    try:
        async with db_pool.connection() as conn:
            yield conn
    except PoolTimeout:
        raise DatabaseConnectionPoolTimeout
    except PoolClosed:
        raise DatabaseConnectionPoolClosed


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint to verify service availability.

    Returns:
        dict[str, str]: A status message confirming the API is running smoothly.
    """
    return {"response": "API is up and running healthy..."}


@app.get("/")
async def home() -> dict[str, str]:
    """Root endpoint providing a brief description of the DataPump service.

    Returns:
        dict[str, str]: Project description and technology stack overview.
    """
    return {
        "response": "DataPump is an data ingestion pipeline with FastAPI+PostgreSQL."
    }


@app.get("/check-db-conn")
async def check_db_conn() -> dict[str, str] | None:
    """Verifies active connectivity to the PostgreSQL database.

    Returns:
        dict[str, str] | None: A query result dictionary confirming database connection status.
    """
    async with db_pool.connection() as conn:
        data = await conn.execute("SELECT 'DB connection okay!' as response")
        return await data.fetchone()


@app.post(
    "/jobs",
    response_model=JobResponse,
    description="Endpoint to create/post job",
)
async def post_jobs(
    job_payload: JobCreate,
    conn: AsyncConnection = Depends(get_db_conn),
) -> JobResponse:
    """Creates a new data ingestion job and stores it in the database.

    Args:
        job_payload: The data payload containing job configuration parameters.
        conn: The active asynchronous database connection dependency.

    Returns:
        JobResponse: The newly created job details including assigned UUID and timestamps.
    """
    data: dict = await post_jobs_handler(conn, job_payload)
    return JobResponse(**data)


@app.get(
    "/jobs",
    response_model=list[JobResponse],
    description="Endpoint to retrieve all the jobs",
)
async def get_jobs(
    conn: AsyncConnection = Depends(get_db_conn),
) -> list[JobResponse]:
    """Retrieves a list of all registered data ingestion jobs.

    Args:
        conn: The active asynchronous database connection dependency.

    Returns:
        list[JobResponse]: A collection of job details and current execution statuses.
    """
    return await get_jobs_handler(conn)