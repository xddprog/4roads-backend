import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from app.infrastructure.logging.logger import get_logger
from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.errors.base import InternalServerError



logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            log_data = {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params) if request.query_params else None,
                "status_code": response.status_code,
                "process_time": round(process_time, 3),
            }
            
            if process_time > APP_CONFIG.SLOW_REQUEST_THRESHOLD:
                logger.warning("slow_request", **log_data)
            else:
                logger.info("request_completed", **log_data)
            
            return response
        
        except Exception as exc:
            print(f"Error: {exc}")
            process_time = time.time() - start_time
            logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                query_params=str(request.query_params) if request.query_params else None,
                process_time=round(process_time, 3),
                error=str(exc),
                exc_info=True,
            )
            return JSONResponse(
                status_code=InternalServerError.status_code, 
                content={"detail": InternalServerError.detail}
            )
