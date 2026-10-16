import asyncio

from datapump import db_pool


async def create_table():
    await db_pool.open()
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            print("Creating custom ENUM type...")
            await cur.execute(
                """
                DO $$ BEGIN 
                    CREATE TYPE job_status AS ENUM(
                        'pending',
                        'processing',
                        'completed',
                        'failed'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN NULL;
                END $$
                """
            )

            print("Creating 'jobs' table...")
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs(
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_source VARCHAR(100) NOT NULL,
                    destination VARCHAR(100) NOT NULL,
                    batch_size INT DEFAULT 1000 NOT NULL,
                    status job_status NOT NULL DEFAULT 'pending',
                    total_records INT DEFAULT 0 NOT NULL,
                    processed_records INT DEFAULT 0 NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,						   
                    CONSTRAINT source_validation CHECK (length(trim(job_source))>0),
                    CONSTRAINT destination_validation CHECK (length(trim(destination))>0),
                    CONSTRAINT batch_size_validation CHECK (batch_size > 0 AND batch_size <= 10000),
                    CONSTRAINT chk_total_records CHECK (total_records >= 0),
                    CONSTRAINT chk_processed_records CHECK (processed_records >= 0 AND processed_records <= total_records),
                    CONSTRAINT validate_job_status CHECK (
                        (status = 'pending' AND processed_records = 0 AND completed_at IS NULL AND error_message IS NULL)
                        OR 
                        (status = 'processing' AND processed_records < total_records AND updated_at IS NOT NULL AND completed_at IS NULL AND error_message IS NULL)
                        OR
                        (status = 'completed' AND processed_records=total_records AND updated_at IS NOT NULL AND completed_at IS NOT NULL AND error_message IS NULL)
                        OR
                        (status = 'failed' AND processed_records<total_records AND updated_at IS NOT NULL AND completed_at IS NULL AND error_message IS NOT NULL AND length(trim(error_message))>0)
                    )
                );
                """
            )

            print("Creatng indexs...")
            await cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_status_created_at
                ON jobs (status, created_at);
                """
            )

            await conn.commit()
            print("Migration completed sucessfully!")
    await db_pool.close()  

if __name__ == "__main__":
    asyncio.run(create_table())