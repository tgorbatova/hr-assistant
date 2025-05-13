import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from file_storage.infrastructure.sqlalchemy.base import Base
from file_storage.infrastructure.sqlalchemy.models.files import Files
from file_storage.infrastructure.sqlalchemy.models.folders import Folders
from file_storage.infrastructure.sqlalchemy.models.results import Results
from file_storage.main.config import DB_SCHEMA, settings

if settings.INFRA.POSTGRES.USE_ENUM_IN_MIGRATIONS:  # pragma: no cover
    import alembic_postgresql_enum  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", str(settings.INFRA.POSTGRES.DATABASE_URL))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support

target_metadata = Base.metadata

_autogenerate_models = (
    Files,
)


def run_migrations_offline() -> None:  # pragma: no cover
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Инициализация миграции для конкретной схемы.

    :param connection:
    :return:
    """
    current_tenant = DB_SCHEMA

    connection.execute(text("set search_path to %s, ext, public" % current_tenant))
    connection.commit()

    connection.dialect.default_schema_name = "public"

    def include_object(object_, _name, type_, _reflected, _compare_to) -> bool:  # type: ignore[no-untyped-def]  # noqa: ANN001
        if type_ == "table":  # pragma: no cover
            return bool(object_.schema == DB_SCHEMA)
        return True  # pragma: no cover

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        type=True,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=DB_SCHEMA,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine and associate a connection with the context."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():  # pragma: no cover
    run_migrations_offline()
else:
    run_migrations_online()
