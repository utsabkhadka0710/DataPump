from fastapi import FastAPI, Depends
from psycopg import AsyncConnection
from collections.abc import AsyncGenerator

from datapump import db_pool, conn_pool_lifespan, post_job_handler
from .models import JobCreate, JobResponse



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

@app.post(
        "/jobs",
        response_model=JobResponse,
        description="endpoint to create/post job"
        )
async def post_jobs(job: JobCreate, conn: AsyncConnection=Depends(get_db_conn)):
    return await post_job_handler(conn, job)
