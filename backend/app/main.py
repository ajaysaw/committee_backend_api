import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config.settings import settings
from app.database.connection import engine, Base
from app.middlewares.logging_middleware import RequestLoggingMiddleware
from app.middlewares.rate_limit_middleware import RateLimitMiddleware
from app.middlewares.error_handler import ErrorHandlingMiddleware
from app.routers import (
    auth_router, committee_router, member_router,
    bidding_router, luckydraw_router, payment_router,
    transaction_router, report_router, notification_router,
)

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("committee_platform")


# ── Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Committee Management Platform...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    yield
    logger.info("Shutting down...")


# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-level backend for Committee / Chit Fund Management Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS (Flutter mobile app) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom Middleware Stack ───────────────────────────────
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── Validation Error Handler ─────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "status": False,
            "message": "Validation error",
            "errors": errors,
        },
    )


# ── Register Routers ─────────────────────────────────────
app.include_router(auth_router)
app.include_router(committee_router)
app.include_router(member_router)
app.include_router(bidding_router)
app.include_router(luckydraw_router)
app.include_router(payment_router)
app.include_router(transaction_router)
app.include_router(report_router)
app.include_router(notification_router)


# ── Health Check ──────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status": True,
        "message": "Committee Management Platform API is running",
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": True, "message": "OK"}
