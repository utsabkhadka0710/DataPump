"""Database handler for creating new jobs in DataPump.

This module provides handler functions to execute database insertion queries
for new data ingestion jobs, with robust error mapping for data validation,
integrity violations, and query syntax issues.
"""

from psycopg import AsyncConnection, Error
from psycopg import DataError, IntegrityError, ProgrammingError

from api import JobCreate
from datapump import (
    DatabaseDataError,
    DatabaseIntegrityError,
    DatabaseProgrammingError,
    DatabaseUnexpectedError,
)


async def post_jobs_handler(
    pool_conn: AsyncConnection, job: JobCreate
) -> dict:
    """Inserts a new data ingestion job into the database.

    Executes an INSERT query with the provided job configuration parameters
    and returns the newly created job record including system-generated fields
    like id, status, and timestamps.

    Args:
        pool_conn: An active asynchronous database connection instance.
        job: The Pydantic model containing job creation payload data.

    Returns:
        dict: A dictionary representing the inserted job record.

    Raises:
        DatabaseDataError: If invalid data format is provided for a column.
        DatabaseIntegrityError: If the insert violates database integrity constraints.
        DatabaseProgrammingError: If there is a syntax or programming error in the SQL query.
        DatabaseUnexpectedError: If an unexpected database error occurs during execution.
    """
    job_source = job.job_source
    destination = job.destination
    batch_size = job.batch_size
    try:
        async with pool_conn.cursor() as cur:
            data = await cur.execute(
                "INSERT INTO jobs (job_source, destination, batch_size) "
                "VALUES"
                "(%s, %s, %s)"
                "RETURNING id, job_source, destination, "
                "batch_size, status, total_records, processed_records, "
                "error_message, created_at,updated_at,completed_at;",
                (job_source, destination, batch_size),
            )
            return await data.fetchone()
    except DataError as e:
        e_column = getattr(e.diag, "column_name", "unknown")
        e_message_primary = getattr(e.diag, "message_primary", str(e))
        raise DatabaseDataError(
            message=f"Data error in column '{e_column}': {e_message_primary}"
        )
    except IntegrityError as e:
        e_constraint = getattr(e.diag, "constraint_name", "unknown")
        e_message_primary = getattr(e.diag, "message_primary", str(e))
        raise DatabaseIntegrityError(
            message=f"Integrity violation on constraint '{e_constraint}': {e_message_primary}"
        )
    except ProgrammingError as e:
        e_message_primary = getattr(e.diag, "message_primary", str(e))
        raise DatabaseProgrammingError(
            message=f"Syntax error in SQL! Please take a proper look at your SQL query...: {e_message_primary}"
        )
    except Error as e:  # here Error -> psycopg.Error
        raise DatabaseUnexpectedError(
            message=f"Unexpected error occured in database! Please try again later...: {str(e)}"
        )