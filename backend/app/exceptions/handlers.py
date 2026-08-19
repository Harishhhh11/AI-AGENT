from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.base import AppException
from app.utils.response import ApiResponse


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse.error(
                message=exc.message,
                errors=exc.errors,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content=ApiResponse.error(
                message="Validation failed.",
                errors=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def internal_exception_handler(
        request: Request,
        exc: Exception,
    ):
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(
                message="Internal Server Error",
            ),
        )