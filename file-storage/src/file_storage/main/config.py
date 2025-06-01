import os

import structlog
from pydantic import BaseModel, HttpUrl, MongoDsn, NatsDsn, PostgresDsn, SecretStr

from file_storage.utils.load_yaml_config import load_yaml_config

_logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class InfraSettings(BaseModel):
    class Postgres(BaseModel):
        DATABASE_URL: PostgresDsn
        SCHEMA: str
        # если создали или обновили какой-либо enum, перед генерацией миграции ставьте True
        USE_ENUM_IN_MIGRATIONS: bool = False
        POOL_SIZE: int = 30
        MAX_OVERFLOW: int = 60
        ENGINE_ECHO: bool = False

    class S3(BaseModel):
        URL: HttpUrl
        REGION_NAME: str = "ru-1"
        BUCKET_NAME: str = "hr-data"
        ACCESS_KEY: SecretStr
        SECRET_KEY: SecretStr
        CHUNK_SIZE: int = 1024 * 1024

        ROOT_PATH: str = "files"
        RESULT_PATH: str = "results"

    class Nats(BaseModel):
        DSN: NatsDsn

    class Mongo(BaseModel):
        DSN: MongoDsn

    POSTGRES: Postgres
    OBJECT_STORE: S3
    NATS: Nats
    MONGO: Mongo


class APISettings(BaseModel):
    HOST: str = "localhost"
    PORT: int = 5050
    NUM_WORKERS: int = 4


class LoggingSettings(BaseModel):
    JSON_LOGGING: bool = True
    LEVEL: str = "DEBUG"


class Settings(BaseModel):
    APP_NAME: str = "file_storage"
    LOGGING: LoggingSettings = LoggingSettings()
    API: APISettings = APISettings()
    INFRA: InfraSettings


class LocalSettings(Settings):
    pass


class TestSettings(Settings):
    ALEMBIC_CFG_PATH: str


class ContainerSettings(Settings):
    pass


def get_config() -> Settings:
    """Получение конфига.

    :return:
    """
    env_type: str | None = os.environ.get("ENV_TYPE")
    cfg_path: str | None = os.environ.get("CFG_PATH")
    match env_type:
        case "local":  # pragma: no cover
            if not cfg_path:
                cfg_path = "local.yaml"
            return LocalSettings.model_validate(load_yaml_config(cfg_path))
        case "test":
            if not cfg_path:  # pragma: no cover
                cfg_path = "test.yaml"
            return TestSettings.model_validate(load_yaml_config(cfg_path))
        case "docker":  # pragma: no cover
            if not cfg_path:
                cfg_path = "docker.yaml"
            return ContainerSettings.model_validate(load_yaml_config(cfg_path))
        case _:  # pragma: no cover
            err = f"{env_type} is not supported"
            raise ValueError(err) from None


settings = get_config()
DB_SCHEMA = settings.INFRA.POSTGRES.SCHEMA

ALEMBIC_SCAN_MODE = False
if os.getenv("ALEMBIC_SCAN_MODE"):  # pragma: no cover
    _logger.warning("ALEMBIC_SCAN_MODE is set!")
    ALEMBIC_SCAN_MODE = True
