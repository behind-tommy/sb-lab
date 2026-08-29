# This file answers: "when something goes wrong in production, how do I find
# every log line that belongs to the one request that failed?"
# Answer: tag every request with a random ID the moment it arrives, and make
# every log line written during that request automatically include it.

import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure structlog to output each log line as one JSON object (not a plain
# sentence). JSON is what log tools (Railway's log viewer, Langfuse, etc.)
# can search and filter on; a plain-text sentence they can only display.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()


# "Middleware" = code that runs on the way in and the way out of every
# request, before your route handler ever sees it. This one exists purely to
# assign a request_id and log the start/end of every request, automatically.
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # A fresh random ID for this one request only.
        request_id = str(uuid.uuid4())

        # "bind_contextvars" stores request_id somewhere every logger call
        # in this request (anywhere in the codebase) can silently pick it up
        # from, without us having to pass request_id into every function.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger.info("request_started", method=request.method, path=request.url.path)
        response = await call_next(request)  # this is where the actual route handler runs
        logger.info("request_finished", status_code=response.status_code)

        # Also return it in a header, so if you're debugging in a browser you
        # can see the exact ID to go search your logs for.
        response.headers["X-Request-ID"] = request_id
        return response
