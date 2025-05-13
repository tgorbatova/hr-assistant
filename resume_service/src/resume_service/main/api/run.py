import uvicorn

from resume_service.main.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "factory:create_app",
        factory=True,
        port=settings.SERVER.PORT,
        host=settings.SERVER.HOST,
        workers=settings.SERVER.NUM_WORKERS,
    )
