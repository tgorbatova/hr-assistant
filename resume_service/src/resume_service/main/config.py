import os

from pydantic import BaseModel, HttpUrl, NatsDsn, RedisDsn

from resume_service.utils.load_yaml_config import load_yaml_config


class ServerSettings(BaseModel):
    HOST: str
    PORT: int
    NUM_WORKERS: int


class RedisSettings(BaseModel):
    DSN: RedisDsn


class NatsSettings(BaseModel):
    class Buckets(BaseModel):
        RAW: str = "file-raw"
        PROCESSED: str = "file-processed"
        DATA: str = "data"

    DSN: NatsDsn
    BUCKET: Buckets = Buckets()


class LLMSettings(BaseModel):
    URL: str
    TOKEN: str
    MODEL: str


class ClientSettings(BaseModel):
    class ServiceCfg(BaseModel):
        BASE_URL: HttpUrl
        DOMAIN: str

    FILES: ServiceCfg | None = None
    LLM: LLMSettings


class InfrastructureSettings(BaseModel):
    REDIS: RedisSettings
    NATS: NatsSettings
    CLIENT: ClientSettings


class Settings(BaseModel):
    SERVER: ServerSettings
    SERVICE_NAME: str = "resume_service"
    JSON_LOGGING: bool = False
    INFRA: InfrastructureSettings


class LocalSettings(Settings): ...


class TestSettings(Settings): ...


class ContainerSettings(Settings): ...


def get_config() -> Settings:
    """Получение конфигурации.

    :return: конфигурация приложения
    """
    env_type: str | None = os.environ.get("ENV_TYPE", "local")
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
