# mypy: disable-error-code="misc"
from collections.abc import AsyncGenerator

from aiohttp import ClientSession
from botocore.client import BaseClient
from botocore.session import get_session
from dishka import Provider, Scope, WithParents, from_context, provide, provide_all
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from file_storage.infrastructure.object_store.file import BucketName, S3ChunkSize, S3ReportRepository, S3Session
from file_storage.infrastructure.sqlalchemy.repositories.file import FileReadRepository, FileRepositoryImpl
from file_storage.main.config import DB_SCHEMA, InfraSettings, Settings


class InfrastructureProvider(Provider):
    scope = Scope.APP

    cfg = from_context(Settings)
    infra_cfg = from_context(InfraSettings)

    request_dependencies = provide_all(
        WithParents[FileRepositoryImpl],
        WithParents[S3ReportRepository],
        scope=Scope.REQUEST,
    )
    app_dependencies = provide_all(
        WithParents[FileReadRepository],
        scope=Scope.APP,
    )

    # provider factories
    @provide
    async def engine(self, settings: InfraSettings) -> AsyncEngine:
        engine = create_async_engine(
            str(settings.POSTGRES.DATABASE_URL),
            pool_size=settings.POSTGRES.POOL_SIZE,
            max_overflow=settings.POSTGRES.MAX_OVERFLOW,
        )
        async with engine.begin() as conn:
            await conn.execute(text(f'SET SEARCH_PATH TO "$user", {DB_SCHEMA}, ext, public;'))
        return engine

    @provide
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.APP)
    async def s3_session(self) -> AsyncGenerator[S3Session]:
        async with ClientSession() as session:
            yield S3Session(session)

    @provide(scope=Scope.APP)
    async def boto_client(self, settings: InfraSettings) -> BaseClient:
        cfg = settings.OBJECT_STORE
        session = get_session()
        return session.create_client(
            "s3",
            endpoint_url=str(cfg.URL),
            region_name=cfg.REGION_NAME,
            aws_access_key_id=cfg.ACCESS_KEY.get_secret_value(),
            aws_secret_access_key=cfg.SECRET_KEY.get_secret_value(),
        )

    @provide(scope=Scope.APP)
    def bucket_name(self, settings: InfraSettings) -> BucketName:
        return BucketName(settings.OBJECT_STORE.BUCKET_NAME)

    @provide(scope=Scope.APP)
    def s3_chunk_size(self, settings: InfraSettings) -> S3ChunkSize:
        return S3ChunkSize(settings.OBJECT_STORE.CHUNK_SIZE)

    @provide
    def mongo_client(self, settings: Settings) -> AsyncIOMotorClient:
        return AsyncIOMotorClient(str(settings.INFRA.MONGO.DSN))

    @provide
    def database(self, client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
        return client.get_database()

    @provide
    def collection(self, db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
        return db.get_collection("results")
