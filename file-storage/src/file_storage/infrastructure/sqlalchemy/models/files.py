import typing

from sqlalchemy import UUID, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from file_storage.domain.models.file import FileId
from file_storage.infrastructure.sqlalchemy.base import Base
from file_storage.infrastructure.sqlalchemy.models.folders import Folders


class Files(Base):
    """Файлы."""

    type_annotation_map: typing.ClassVar = {
        FileId: UUID,
    }

    __tablename__ = "files"

    id: Mapped[FileId] = mapped_column(primary_key=True, index=True, unique=True)
    name: Mapped[str] = mapped_column(index=True)
    file_name: Mapped[str]

    folder_name: Mapped[str] = mapped_column(ForeignKey("folders.name", ondelete="SET NULL"), nullable=True)

    folder: Mapped["Folders"] = relationship(
        "Folders", backref="files", primaryjoin="Files.folder_name == Folders.name"
    )

    size: Mapped[int]
    path: Mapped[str] = mapped_column(unique=True)

    __table_args__ = (
        Index("idx_files_id_hash", "id", postgresql_using="hash"),
        UniqueConstraint("name", "folder_name", name="uq_files_name_folder"),
        {"schema": "files_schema"},
    )
