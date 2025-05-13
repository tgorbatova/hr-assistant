import typing

from sqlalchemy import UUID, Index
from sqlalchemy.orm import Mapped, mapped_column

from file_storage.domain.models.file import FolderId
from file_storage.infrastructure.sqlalchemy.base import Base


class Folders(Base):
    """Папки."""

    type_annotation_map: typing.ClassVar = {
        FolderId: UUID,
    }

    __tablename__ = "folders"

    id: Mapped[FolderId] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    description: Mapped[str] = mapped_column()

    __table_args__ = (Index("idx_folders_id_hash", "id", postgresql_using="hash"),)
