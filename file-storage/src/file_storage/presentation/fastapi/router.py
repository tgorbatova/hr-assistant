from fastapi import APIRouter

from file_storage.presentation.fastapi.routes.files import file_router

router = APIRouter()

router.include_router(file_router, tags=["файлы"])
