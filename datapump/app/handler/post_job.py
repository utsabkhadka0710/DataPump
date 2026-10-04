from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from api import JobCreate, JobResponse

async def post_job_handler(pool_conn: AsyncConnection, job: JobCreate):
    async with pool_conn.cursor() as cur:
        data = await cur.execute("SELECT 'POST-/jobs is connected with the connection pool' as response")
        return await data.fetchone()