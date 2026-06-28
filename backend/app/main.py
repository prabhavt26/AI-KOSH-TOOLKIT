import uuid
import redis
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.api.v1 import assess, reports, health, auth, admin, datasets

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Exempt health check endpoints from rate limiting
        if "/health" in path:
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        if "/auth/register" in path:
            redis_key = f"rate_limit:register:{client_ip}"
            limit = 10
        elif "/auth/login" in path:
            redis_key = f"rate_limit:auth:{client_ip}"
            limit = 20
        else:
            redis_key = f"rate_limit:general:{client_ip}"
            limit = 100

        try:
            current = redis_client.incr(redis_key)
            if current == 1:
                redis_client.expire(redis_key, 60)
            if current > limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": f"API rate limit exceeded for this endpoint. Max {limit} requests per minute."}
                )
        except redis.RedisError:
            pass
        return await call_next(request)

docs_enabled = settings.ENVIRONMENT != "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs_enabled else None
)

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json_root():
    if not docs_enabled:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})
    return JSONResponse(content=app.openapi())

# Set up CORS (Enforces credential-aware origin restrictions)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin")
app.include_router(assess.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(datasets.router, prefix=settings.API_V1_STR)

