from fastapi import status, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse


class HTTPErrorHandler(BaseHTTPMiddleware):
    """
    HTTP error handler.
    """

    async def dispatch(self, request: Request, call_next) -> Response | JSONResponse:
        """
        Dispatch.
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exception:
            if isinstance(exception, HTTPException):
                return JSONResponse(
                    status_code=exception.status_code,
                    content={
                        "status": exception.status_code,
                        "message": exception.detail
                    }
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": str(exception)
                    }
                )


