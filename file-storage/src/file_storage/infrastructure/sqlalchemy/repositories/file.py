import json
from typing import BinaryIO

import structlog
from adaptix.conversion import get_converter
from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from file_storage.domain.exceptions.file import DeleteFromDbError, FileNotFoundError, SaveToDbError
from file_storage.domain.models.adaptix import retort
from file_storage.domain.models.file import File, FileId, Folder, FolderId, SaveFile, SaveFolder
from file_storage.domain.models.result import Result, ResultId, ResultType, SaveResult
from file_storage.domain.mongo_filter.model import Paginated
from file_storage.domain.repositories.file import FileReader, FileRepository
from file_storage.infrastructure.sqlalchemy.models.files import Files
from file_storage.infrastructure.sqlalchemy.models.folders import Folders
from file_storage.infrastructure.sqlalchemy.models.results import Results
from file_storage.presentation.filters.model import MongoResume
from file_storage.presentation.filters.results import ResumeResultsFilter

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("files.repository")

convert_folder = get_converter(Folders, Folder)


def convert_file_to_domain(model: Files) -> File:
    """Конвертация файла в доменную модель.

    :param model:
    :return:
    """
    return File.create(
        file_id=model.id,
        name=model.name,
        file_name=model.file_name,
        folder_name=model.folder_name,
        size=model.size,
        file_created_at=model.created_at,
        path=model.path,
    )


def convert_result_to_domain(model: Results) -> Result:
    """Конвертация результата в доменную модель.

    :param model:
    :return:
    """
    return Result.create(
        result_id=model.id,
        file_id=model.file_id,
        type=model.type,
        file_name=model.file_name,
        folder_name=model.folder_name,
        file_created_at=model.created_at,
        path=model.path,
        size=model.size,
    )


class FileRepositoryImpl(FileRepository):
    def __init__(self, session: AsyncSession, mongo_client: AsyncIOMotorCollection) -> None:
        self._session = session
        self._mongo_client = mongo_client

    async def save(self, file_info: SaveFile) -> FileId:
        """Сохранение отчета в БД.
        save_formatted_result
                :param file_info:
                :return:
        """
        model = Files(
            id=file_info.id,
            file_name=file_info.file_name,
            name=file_info.name,
            folder_name=file_info.folder_name,
            size=file_info.size,
            path=file_info.file_path,
        )
        try:
            _logger.debug("Saving file_info %s to bd", file_info)
            self._session.add(model)
            await self._session.commit()
        except IntegrityError as exc:
            _logger.error("Error saving file_info %s to bd: %s", file_info, str(exc))
            await self._session.rollback()
            raise SaveToDbError from exc

        return model.id

    async def save_result(self, result_info: SaveResult) -> ResultId:
        """Сохранение результата в БД.

        :param result_info:
        :return:
        """
        model = Results(
            id=result_info.id,
            file_id=result_info.file_id,
            file_name=result_info.file_name,
            type=result_info.type,
            folder_name=result_info.folder_name,
            path=result_info.path,
            size=result_info.size,
        )
        try:
            _logger.debug("Saving result_info %s to bd", result_info)
            self._session.add(model)
            await self._session.commit()
        except IntegrityError as exc:
            _logger.error("Error saving result_info %s to bd: %s", result_info, str(exc))
            await self._session.rollback()
            raise SaveToDbError from exc

        return model.id

    async def save_formatted_result(self, result_id: ResultId, file_id: FileId, result: BinaryIO) -> None:
        """Сохранение результата в mongo БД.

        :param result_id:
        :param file_id:
        :param result:
        :return:
        """
        try:
            _logger.debug("Saving result_info %s to mongo bd", result_id)
            # Читаем и декодируем содержимое из BinaryIO
            result_data = result.read()
            result_json = json.loads(result_data.decode("utf-8"))

            # Создаём документ
            document = {
                "result_id": str(result_id),
                "file_id": str(file_id),
                "result": result_json,
            }

            # Сохраняем в коллекцию
            await self._mongo_client.insert_one(document)
        except Exception as exc:
            _logger.error("Error saving result_info %s to mongo bd: %s", result_id, str(exc))

    async def get_filtered(self, filters: ResumeResultsFilter) -> Paginated[MongoResume]:
        data = await filters.execute(self._mongo_client, loader=retort.load)

        return data

    async def create_folder(self, folder_info: SaveFolder) -> FolderId:
        """Сохранение папки в бд.

        :param folder_info:
        :return:
        """
        model = Folders(id=folder_info.id, name=folder_info.name, description=folder_info.description)
        try:
            _logger.debug("Saving file_info %s to bd", folder_info)
            self._session.add(model)
            await self._session.commit()
        except IntegrityError as exc:
            _logger.error("Error saving file_info %s to bd", folder_info)
            await self._session.rollback()
            raise SaveToDbError from exc

        return model.id

    async def delete_folder(self, folder_info: Folder) -> None:
        """Удаление папки и всех файлов в ней из БД.

        :param folder_info: информация о папке
        """
        try:
            _logger.debug("Deleting folder %s and its files", folder_info)

            # First, delete files in the folder
            stmt_delete_files = delete(Files).where(Files.folder_name == folder_info.name)
            await self._session.execute(stmt_delete_files)

            # Then, delete the folder itself
            stmt_delete_folder = delete(Folders).where(Folders.name == folder_info.name)
            await self._session.execute(stmt_delete_folder)

            await self._session.commit()
        except SQLAlchemyError as exc:
            _logger.error("Error deleting folder %s from db: %s", folder_info.name, str(exc))
            await self._session.rollback()
            raise DeleteFromDbError from exc

    async def delete(self, folder_name: str, file_name: str) -> None:
        """Удаление файла из базы данных.

        :param folder_name
        :param file_name
        """
        try:
            _logger.debug("Deleting file %s", file_name)

            stmt = delete(Files).where(Files.name == file_name, Files.folder_name == folder_name)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as exc:
            _logger.error("Error deleting file %s from db: %s", file_name, str(exc))
            await self._session.rollback()
            raise DeleteFromDbError from exc


class FileReadRepository(FileReader):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker

    async def get_file_by_id(self, file_id: FileId) -> File:
        """Получение файла по идентификатору.

        :param file_id:
        """
        _logger.debug("Getting file by id %s", file_id)
        query = select(Files).where(Files.id == file_id)
        async with self._session_maker() as session:
            result = await session.execute(query)
            if model := result.unique().scalar_one_or_none():
                return convert_file_to_domain(model)
            await _logger.awarning("File %s not found in DB", file_id)
            raise FileNotFoundError(file_id)

    async def get_result_by_file_id(self, file_id: FileId, type: ResultType) -> Result:
        """Получение результата по идентификатору файла.

        :param file_id:
        :param type:
        """
        _logger.debug("Getting result by file id %s", file_id)
        query = select(Results).where(Results.file_id == file_id, Results.type == type)
        async with self._session_maker() as session:
            result = await session.execute(query)
            if model := result.unique().scalar_one_or_none():
                return convert_result_to_domain(model)
            await _logger.awarning("Result %s not found in DB", file_id)
            raise FileNotFoundError(file_id)

    async def get_file_info_by_path(self, path: str) -> File:
        """Получение информации о файле по пути.

        :param path:
        """
        _logger.debug("Getting file info by path %s", path)
        query = select(Files).where(Files.path == path)
        async with self._session_maker() as session:
            result = await session.execute(query)
            if model := result.unique().scalar_one_or_none():
                return convert_file_to_domain(model)
            await _logger.awarning("File %s not found in DB", path)
            raise FileNotFoundError(path)

    async def get_folder_info(self, folder_name: str) -> Folder:
        """Get folder info."""
        try:
            _logger.debug("Getting folder_info %s from DB", folder_name)
            stmt = select(Folders).where(Folders.name == folder_name)
            async with self._session_maker() as session:
                result = await session.execute(stmt)
                folder = result.scalar_one_or_none()

                if folder is None:
                    _logger.warning("Folder '%s' not found", folder_name)
                    raise ValueError("Folder %s not found", folder_name)

                return convert_folder(folder)

        except IntegrityError as exc:
            _logger.error("Error getting folder_info %s from DB", folder_name)
            raise SaveToDbError from exc
