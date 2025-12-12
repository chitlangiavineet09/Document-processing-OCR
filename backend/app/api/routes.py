from fastapi import APIRouter
from app.api.v1.endpoints import jobs, drafts, users, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(drafts.router, prefix="/drafts", tags=["drafts"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

