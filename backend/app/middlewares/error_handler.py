import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("committee_platform")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(f"[{request_id}] Unhandled error: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "status": False,
                    "message": "An internal server error occurred.",
                },
            )
