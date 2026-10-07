from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from datapump import DatabaseError

async def exceptions_response_handler(exception: DatabaseError) -> JSONResponse:
    exception_class_name = type(exception).__name__
    exception_status_code_map = {
        'DatabaseConnectionPoolTimeout': status.HTTP_408_REQUEST_TIMEOUT,
        'DatabaseConnectionPoolClosed': status.HTTP_503_SERVICE_UNAVAILABLE,
        'DatabaseDataError': status.HTTP_422_UNPROCESSABLE_CONTENT,
        'DatabaseIntegrityError': status.HTTP_409_CONFLICT,
        'DatabaseProgrammingError': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'DatabaseUnexpectedError': status.HTTP_500_INTERNAL_SERVER_ERROR
    }

    status_code = exception_status_code_map.get(exception_class_name,status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "message": exception.message
        }
    )

def register_exceptions_handler(app: FastAPI):

    @app.exception_handler(DatabaseError)
    async def pool_timeout_exeption_handler(request: Request, exception: DatabaseError):
        return await exceptions_response_handler(exception)

