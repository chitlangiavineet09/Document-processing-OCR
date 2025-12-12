from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.auth import verify_supabase_token
from app.api.routes import api_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Automatic Bill Processing System",
    description="API for automatic bill processing with OCR and classification",
    version="1.0.0"
)

# CORS middleware
# Parse comma-separated string to list of origins (remove trailing slashes)
cors_origins = [origin.strip().rstrip('/') for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
logger.info(f"CORS origins configured: {cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.get("/")
async def root():
    return {"message": "Automatic Bill Processing System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Exception handler for validation errors (422) - must be before routes
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors (422)"""
    errors = exc.errors()
    logger.error(f"Validation error on {request.url.path}: {errors}")
    logger.error(f"Request body: {exc.body if hasattr(exc, 'body') else 'N/A'}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )

# Include API routes with authentication dependency
app.include_router(
    api_router,
    prefix="/api/v1",
    dependencies=[],  # Auth dependency applied per-route as needed
    tags=["api"]
)

logger.info("Application started successfully")

