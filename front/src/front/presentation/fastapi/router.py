from fastapi import APIRouter

from front.presentation.fastapi.routes.common import main_router
from front.presentation.fastapi.routes.files import files_router

router = APIRouter()

router.include_router(main_router, tags=["Main pages"])
router.include_router(files_router, tags=["Files pages"])
