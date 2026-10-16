"""Global exception handlers for database errors in DataPump.

This module maps custom database exception classes to appropriate HTTP status codes
and registers global exception handlers on the FastAPI application instance to ensure
consistent error reporting across the API.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from datapump import DatabaseError


async def exceptions_response_handler(exception: DatabaseError) -> JSONResponse:
    """Formats custom database exceptions into structured JSON error responses.

    Maps the specific database exception class to its corresponding HTTP status code
    and constructs a JSON payload containing the error message.

    Args:
        exception: The custom DatabaseError instance raised during execution.

    Returns:
        JSONResponse: A FastAPI JSON response with the mapped HTTP status code and error message.
    """
    exception_class_name = type(exception).__name__
    exception_status_code_map = {
        "DatabaseConnectionPoolTimeout": status.HTTP_408_REQUEST_TIMEOUT,
        "DatabaseConnectionPoolClosed": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DatabaseDataError": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "DatabaseIntegrityError": status.HTTP_409_CONFLICT,
        "DatabaseProgrammingError": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DatabaseUnexpectedError": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    status_code = exception_status_code_map.get(
        exception_class_name, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=status_code, content={"message": exception.message}
    )


def register_exceptions_handler(app: FastAPI) -> None:
    """Registers global exception handlers for database-related errors on the FastAPI app.

    Args:
        app: The FastAPI application instance to register the exception handlers on.
    """

    @app.exception_handler(DatabaseError)
    async def pool_timeout_exeption_handler(
        request: Request, exception: DatabaseError
    ) -> JSONResponse:
        """Catches global DatabaseErrors and forwards them to the response handler.

        Args:
            request: The incoming FastAPI request instance.
            exception: The caught DatabaseError instance.

        Returns:
            JSONResponse: The formatted error response.
        """
        return await exceptions_response_handler(exception)