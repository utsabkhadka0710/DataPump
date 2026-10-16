import asyncio
import psycopg

from datapump import db_pool, DatabaseUnexpectedError


async def plant_seeds_data():
    seed_rows = int(input("Enter the no. of rows to plant the seed data: "))
    await db_pool.open()
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            print("Planting seed data into database...")
            try:
                await cur.execute(
                    f"""
                    INSERT INTO jobs(
                        id,
                        job_source,
                        destination,
                        batch_size,
                        status,
                        total_records,
                        processed_records,
                        error_message,
                        created_at,
                        updated_at,
                        completed_at
                    )
                    -- Outer select
                    SELECT
                        -- Generates random UUID
                        gen_random_uuid() AS id,
                        -- Valid sources and destinations
                        (ARRAY[
                                'postgres://db/source1',
                                'api://src_endpoint-1',
                                'postgres://db/source2',
                                'api://src_endpoint2'
                            ])[floor(random()*4+1)] AS job_source,
                        (ARRAY[
                                'postgres://db/destination1',
                                'api://dest_endpoint-1',
                                'postgres://db/destination2',
                                'api://dest_endpoint2'
                            ])[floor(random()*4+1)] AS destination,
                        -- Valid batch_size 
                        floor(random()*9999+1)::int AS batch_size,
                        -- Valid status & total_records which comes from inner select
                        status,
                        total_records,
                        -- Valid processed_records
                        CASE status
                            WHEN 'pending' THEN 0
                            WHEN 'processing' THEN floor(random()*total_records)::int
                            WHEN 'completed' THEN total_records
                            WHEN 'failed' THEN floor(random()*total_records)::int
                        END AS processed_records,
                        -- Valid error_message
                        CASE
                            WHEN status='failed' THEN error_message
                            ELSE NULL
                        END AS error_message,
                        -- Valid created_at which comes from inner select
                        created_at,
                        -- Valid updated_at
                        CASE
                            WHEN status != 'pending' THEN (created_at+(random()*INTERVAL '50 days'))
                            ELSE NULL
                        END AS updated_at,
                        -- Valid completed_at
                        CASE
                            WHEN status = 'completed' THEN (created_at+(random()*INTERVAL '45 days'))
                            ELSE NULL
                        END	AS completed_at
                    FROM (
                        -- Inner select
                        SELECT
                            (ARRAY['pending','processing','completed','failed']::job_status[])[(floor(random()*4+1))] AS status,
                            floor(random()*100001) AS total_records,
                            (ARRAY[
                                    'worker crashed unexpectedly',
                                    'server crashed unexpectedly',
                                    'app crashed unexpectedly',
                                    'error occured during processing',
                                    'invalid records provided cannot process it',
                                    'could not process the records',
                                    'job corrupted'
                                ])[floor(random()*7+1)] AS error_message,
                            (CURRENT_TIMESTAMP+(random()*INTERVAL '40 days')) AS created_at
                        FROM generate_series(1,{seed_rows})
                    ) steps;
                    """
                )
            except psycopg.Error as e:
                raise DatabaseUnexpectedError(
                    message=f"Could not plant seed data. Unexpected error occured in database! Please try again...: {str(e)}"
                )
            await conn.commit()
            print(f"Sucessfully planted {seed_rows} no. of seed data into database!")
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(plant_seeds_data())