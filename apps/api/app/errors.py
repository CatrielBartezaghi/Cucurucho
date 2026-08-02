from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field_errors = field_errors or {}


def error_body(
    code: str, message: str, field_errors: dict[str, str] | None = None
) -> dict[str, Any]:
    return {"code": code, "message": message, "field_errors": field_errors or {}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.field_errors),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for item in exc.errors():
            location = item.get("loc", ())
            field = str(location[-1]) if location else "request"
            fields[field] = "El valor ingresado no es válido."
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", "Revisá los datos ingresados.", fields),
        )
