import datetime
from typing import Annotated

from sqlalchemy import MetaData, Numeric, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from file_storage.main.config import DB_SCHEMA


class Base(DeclarativeBase):
    """Базовый класс модели."""

    metadata = MetaData(
        schema=DB_SCHEMA,
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )

    created_at: Mapped[datetime.datetime] = mapped_column(server_default=text("TIMEZONE('Europe/Moscow', now())"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE('Europe/Moscow', now())"),
        onupdate=text("TIMEZONE('Europe/Moscow', now())"),
    )


int_pk = Annotated[int, mapped_column(primary_key=True)]
Numeric_11_4 = Numeric(precision=11, scale=4)
