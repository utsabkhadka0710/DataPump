"""Database handler for retrieving jobs in DataPump.

This module provides handler functions to execute database queries related
to job retrieval with proper error handling and custom exception mapping.
"""

from psycopg import AsyncConnection, Error, ProgrammingError

from datapump import DatabaseProgrammingError, DatabaseUnexpectedError

from uuid import UUID

async def get_jobs_handler(pool_conn: AsyncConnection) -> list[dict]:
    """Retrieves all data ingestion jobs from the database.

    Executes a SELECT query to fetch all job records from the jobs table
    using the provided asynchronous database connection.

    Args:
        pool_conn: An active asynchronous database connection instance.

    Returns:
        list[dict]: A list of record dictionaries containing job details.

    Raises:
        DatabaseProgrammingError: If there is a syntax or programming error in the SQL query.
        DatabaseUnexpectedError: If an unexpected database error occurs during execution.
    """
    async with pool_conn.cursor() as cur:
        try:
            data = await cur.execute(
                "SELECT "
                "id, job_source, destination, batch_size, status, "
                "total_records, processed_records, error_message, "
                "created_at, updated_at, completed_at "
                "FROM jobs "
                "ORDER BY created_at, id ASC;"
            )
            return await data.fetchall()
        except ProgrammingError as e:
            e_message_primary = getattr(e.diag, "message_primary", str(e))
            raise DatabaseProgrammingError(
                message=f"Syntax error in SQL! Please take a proper look at your SQL query...: {e_message_primary}"
            )
        except Error as e:
            raise DatabaseUnexpectedError(
                message=f"Unexpected error occured in database! Please try again later...: {str(e)}"
            )


async def get_job_by_id_handler(
    pool_conn: AsyncConnection, id
) -> dict | None:
    """Retrieves a specific job record by its unique UUID from the database.

    Executes a SELECT query to fetch detailed information for a single job
    matching the given identifier.

    Args:
        pool_conn: An active asynchronous database connection instance.
        id: The unique UUID of the job to retrieve.

    Returns:
        dict | None: A dictionary containing the job record if found, otherwise None.

    Raises:
        DatabaseProgrammingError: If there is a syntax or programming error in the SQL query.
        DatabaseUnexpectedError: If an unexpected database error occurs during execution.
    """
    async with pool_conn.cursor() as cur:
        try:
            data = await cur.execute(
                "SELECT "
                "id, job_source, destination, batch_size, status, "
                "total_records, processed_records, error_message, "
                "created_at, updated_at, completed_at "
                "FROM jobs "
                "WHERE id = %s;",
                (id,)
            )
            return await data.fetchone()
        except ProgrammingError as e:
            e_message_primary = getattr(e.diag, "message_primary", str(e))
            raise DatabaseProgrammingError(
                message=f"Syntax error in SQL! Please take a proper look at your SQL query...: {e_message_primary}"
            )
        except Error as e:
            raise DatabaseUnexpectedError(
                message=f"Unexpected error occured in database! Please try again later...: {str(e)}"
            )
 