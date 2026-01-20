import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from cloudwatch.logging_config import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = round(time.time() - start_time, 3)

        logger.info(
            f"METHOD={request.method} | "
            f"PATH={request.url.path} | "
            f"STATUS={response.status_code} | "
            f"TIME={duration}s"
        )

        return response
