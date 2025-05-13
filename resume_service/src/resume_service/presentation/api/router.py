from fastapi import APIRouter

from resume_service.presentation.api.routes import task

router = APIRouter()

router.include_router(task.router, tags=["tasks"])
