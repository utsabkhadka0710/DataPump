from psycopg import ProgrammingError, Error
from psycopg import AsyncConnection

from datapump import DatabaseProgrammingError, DatabaseUnexpectedError

async def get_jobs_handler(pool_conn: AsyncConnection):
    async with pool_conn.cursor() as cur:
        try:
            data = await cur.execute(
                "SELECT * FROM jobs;"
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