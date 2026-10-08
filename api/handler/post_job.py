from psycopg import AsyncConnection, Error
from psycopg import DataError, IntegrityError, ProgrammingError


from api import JobCreate
from datapump import (
    DatabaseDataError,
    DatabaseIntegrityError,
    DatabaseProgrammingError,
    DatabaseUnexpectedError
)


async def post_job_handler(pool_conn: AsyncConnection, job: JobCreate):
    job_source = job.source
    destinaion = job.destination
    batch_size = job.batch_size
    try:
        async with pool_conn.cursor() as cur:
            data = await cur.execute(
                "INSERT INTO jobs (job_source, destination, batch_size)"
                "VALUES"
                "(%s, %s, %s)"
                "RETURNING id, job_source as source, destination, " 
                "batch_size, status, total_records, processed_records, "
                "error_message, created_at,updated_at,completed_at;",
                (job_source, destinaion, batch_size)
            )
            return await data.fetchone()
    except DataError as e:
        e_column = getattr(e.diag, "column_name",'unknown')
        e_message_primary = getattr(e.diag, "message_primary", str(e))
        raise DatabaseDataError(
            message=f"Data error in column '{e_column}': {e_message_primary}"
        )
    except IntegrityError as e:
        e_constraint = getattr(e.diag, "constraint_name", "unknown")
        e_detail = getattr(e.diag, "message_detail", str(e))
        raise DatabaseIntegrityError(
            message=f"Integrity violation on constraint '{e_constraint}': {e_detail}"
        )
    except ProgrammingError as e:
        e_message_primary = getattr(e.diag, "message_primary", str(e))
        raise DatabaseProgrammingError(
            message=f"Syntax error in SQL! Please take a proper look at your SQL query...: {e_message_primary}"
        )
    except Error as e: # here Error -> psycopg.Error
        raise DatabaseUnexpectedError(
            message=f"Unexpected error occured in database! Please try again later...: {str(e)}"
        )