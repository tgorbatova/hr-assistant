import uvicorn

from front.main.config import settings

if __name__ == "__main__":
    cfg = settings.API
    uvicorn.run("factory:create_app", host=cfg.HOST, port=cfg.PORT, factory=True, workers=cfg.NUM_WORKERS)
