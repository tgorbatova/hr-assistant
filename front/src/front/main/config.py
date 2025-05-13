import os

import structlog
from pydantic import BaseModel, HttpUrl, NatsDsn

from front.utils.load_yaml_config import load_yaml_config

logger = structlog.get_logger("config")


class ServiceInfoSettings(BaseModel):
    class ServiceUrlSettings(BaseModel):
        NAME: str
        URL: str

    FILES: ServiceUrlSettings | None = None


class AppSettings(BaseModel):
    STATICFILES_DIRECTORY: str
    TEMPLATES_DIRECTORY: str

    # запросы от клиента (браузера) должны быть зашифрованы (https/wss/etc.)
    CLIENT_SECURE_REQUESTS: bool = False
    USER_INFO_REFRESH_INTERVAL: int = 60 * 5
    USER_INFO_COOKIE_MAX_AGE: int = 60 * 60 * 24 * 30


class ClientSettings(BaseModel):
    class ServiceCfg(BaseModel):
        BASE_URL: HttpUrl
        DOMAIN: str

    FILES: ServiceCfg | None = None


class NatsSettings(BaseModel):
    DSN: NatsDsn


class InfrastructureSettings(BaseModel):
    CLIENT: ClientSettings
    NATS: NatsSettings


class LoggingSettings(BaseModel):
    JSON_LOGGING: bool = True
    LEVEL: bool | None = "DEBUG"


class APISettings(BaseModel):
    HOST: str = "localhost"
    PORT: int = 5008
    NUM_WORKERS: int = 4


class Settings(BaseModel):
    APP: AppSettings
    API: APISettings
    INFRA: InfrastructureSettings
    LOGGING: LoggingSettings

    APP_NAME: str = "front"

    HOST: str = "localhost"
    PORT: int = 5008


class LocalSettings(Settings):
    pass


class TestSettings(Settings):
    pass


class ContainerSettings(Settings):
    pass


def get_config() -> Settings:
    """Получение конфигурации.

    :return: конфигурация приложения
    """
    env_type: str | None = os.environ.get("ENV_TYPE")
    match env_type:
        case "local":
            return LocalSettings.model_validate(load_yaml_config("local.yaml"))
        case "test":
            return TestSettings.model_validate(load_yaml_config("test.yaml"))
        case "docker":
            return ContainerSettings.model_validate(load_yaml_config("docker.yaml"))
        case _:
            msg = f"{env_type} is not supported"
            raise ValueError(msg)


settings = get_config()
