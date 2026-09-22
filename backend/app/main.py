from collections import defaultdict, deque
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from app.api.orchestrator import router as orchestrator_router
from app.api.cloud_control import router as cloud_control_router
from app.api.platform import router as platform_router
from app.api.auth import router as auth_router
from app.api.integrations import router as integrations_router
from app.api.persistence import router as persistence_router
from app.api.modules import router as modules_router
from app.api.status import router as status_router
from app.core.config import get_settings

settings = get_settings()


class RateLimitMiddleware:
    def __init__(self, app, limit: int, window_seconds: int = 60):
        self.application = app
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.application(scope, receive, send)
            return
        client = scope.get("client")
        key = client[0] if client else "unknown"
        now = time.monotonic()
        bucket = self.requests[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            response = JSONResponse({"detail": "Rate limit exceeded"}, status_code=429, headers={"Retry-After": str(self.window_seconds)})
            await response(scope, receive, send)
            return
        bucket.append(now)
        await self.application(scope, receive, send)


app = FastAPI(title="DevOrbit AI Backend", version="1.0", docs_url=None if settings.app_env == "production" else "/docs", redoc_url=None if settings.app_env == "production" else "/redoc")
app.add_middleware(RateLimitMiddleware, limit=settings.rate_limit_per_minute)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orchestrator_router, prefix="/api/v1/orchestrator", tags=["Orchestrator"])
app.include_router(cloud_control_router)
app.include_router(platform_router)
app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(persistence_router)
app.include_router(modules_router)
app.include_router(status_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to DevOrbit AI Cloud & DevOps Engine API!"}

@app.get("/api/cloud-status")
def get_cloud_status():
    return {
        "status": "Active",
        "environment": "AWS-Cloud-Us-East-1",
        "active_containers": 3,
        "infrastructure": {
            "vpc": "vpc-0abc123456789xyz",
            "subnet": "public-subnet-1a",
            "ec2_instances": ["i-0123456789abcdef0", "i-0987654321fedcba0"],
            "terraform_state": "Synced"
        },
        "ai_auditor": "Monitoring Enabled"
    }

from fastapi.middleware.cors import CORSMiddleware

# Added explicit CORS handling for frontend ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
