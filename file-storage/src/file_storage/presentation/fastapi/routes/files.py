from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Form, Query, UploadFile
from starlette import status
from starlette.responses import StreamingResponse

from file_storage.application.interfaces.usecase.file import (
    CreateFolderUseCase,
    DeleteFileUseCase,
    DeleteFolderUseCase,
    GetFileByIdUseCase,
    GetInfoUseCase,
    ListFilesUseCase,
    ListFoldersUseCase,
    SaveFileUseCase,
)
from file_storage.application.models.file import SaveFileDto, SaveFolderDto
from file_storage.domain.exceptions.file import DeleteFolderError, FileNotFoundError, SaveFileError
from file_storage.domain.models.file import File, FileId, Folder, FolderId
from file_storage.presentation.fastapi.response_model import DetailedHttpException, EntityNotFoundModel
from file_storage.presentation.fastapi.schemas.file import (
    CreateFolderQuery,
    GetFileQuery,
    GetFilesQuery,
    GetFolderQuery,
    SaveFileQuery,
)
from file_storage.utils.logging import logger

file_router = APIRouter(prefix="/files", route_class=DishkaRoute)


@file_router.post("", status_code=status.HTTP_201_CREATED)
async def save_file(
    file: UploadFile, usecase: FromDishka[SaveFileUseCase], queries: Annotated[SaveFileQuery, Query(...)]
) -> FileId:
    """Сохранение файла.

    \f
    :param file:
    :param usecase:
    :param queries:
    :return:
    """
    try:
        dto = SaveFileDto(
            id=queries.file_id,
            file_name=file.filename or "",
            name=queries.name or file.filename,
            folder=queries.folder or None,
            size=file.size or 0,
        )
        return await usecase.save(file_info=dto, file=file.file)
    except SaveFileError as exc:
        logger.error(str(exc))
        raise DetailedHttpException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@file_router.post("/create/folder", status_code=status.HTTP_201_CREATED)
async def create_folder(
    usecase: FromDishka[CreateFolderUseCase],
    queries: Annotated[CreateFolderQuery, Query(...)],
    name: str = Form(...),
    description: str = Form(...),
) -> FolderId:
    """Сохранение файла.

    \f
    :param usecase:
    :param queries:
    :param name:
    :param description:
    :return:
    """
    try:
        dto = SaveFolderDto(id=queries.folder_id, name=name, description=description)
        return await usecase.create_folder(folder_info=dto)
    except SaveFileError as exc:
        logger.error(str(exc))
        raise DetailedHttpException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@file_router.delete("/delete/folder/{folder_name}", status_code=status.HTTP_201_CREATED)
async def delete_folder(
    folder_name: str,
    usecase: FromDishka[DeleteFolderUseCase],
):
    """Сохранение файла.

    \f
    :param folder_name:
    :param usecase:
    :return:
    """
    try:
        return await usecase.delete_folder(folder_name=folder_name)
    except DeleteFolderError as exc:
        logger.error(str(exc))
        raise DetailedHttpException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@file_router.delete("/delete/file/{folder_name}/{file_name}", status_code=status.HTTP_201_CREATED)
async def delete_file(
    folder_name: str,
    file_name: str,
    usecase: FromDishka[DeleteFileUseCase],
):
    """Сохранение файла.

    \f
    :param folder_name:
    :param file_name:
    :param usecase:
    :return:
    """
    try:
        return await usecase.delete(folder_name=folder_name, file_name=file_name)
    except DeleteFolderError as exc:
        logger.error(str(exc))
        raise DetailedHttpException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@file_router.get(
    "/{file_id}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": EntityNotFoundModel}},
)
async def get_report_file_by_id(file_id: FileId, usecase: FromDishka[GetFileByIdUseCase]) -> StreamingResponse:
    """Получение файла по идентификатору.

    \f
    :param file_id:
    :param usecase:
    :return:
    """
    try:
        return StreamingResponse(await usecase.get_file_by_id(file_id=file_id))
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@file_router.get(
    "/info/file/{file_id}",
    status_code=status.HTTP_200_OK,
)
async def get_file_info_by_id(file_id: FileId, usecase: FromDishka[GetFileByIdUseCase]) -> File:
    """Получение файла по идентификатору.

    \f
    :param file_id:
    :param usecase:
    :return:
    """
    try:
        return await usecase.get_file_info_by_id(file_id=file_id)
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@file_router.get(
    "/info/file",
    status_code=status.HTTP_200_OK,
)
async def get_file_info_by_path(
    usecase: FromDishka[GetFileByIdUseCase], queries: Annotated[GetFileQuery, Query()]
) -> File:
    """Получение файла по идентификатору.

    \f
    :param file_id:
    :param usecase:
    :return:
    """
    try:
        return await usecase.get_file_info_by_path(path=queries.path)
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@file_router.get(
    "/list/files",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": EntityNotFoundModel}},
)
async def get_files_in_folder(
    usecase: FromDishka[ListFilesUseCase], queries: Annotated[GetFilesQuery, Query()]
) -> list[str]:
    """Получение файлов в папке.

    \f
    :param usecase:
    :param queries:
    :return:
    """
    try:
        return await usecase.list_files_in_folder(folder_name=queries.folder)
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@file_router.get(
    "/info/folder",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": EntityNotFoundModel}},
)
async def get_folder_info(usecase: FromDishka[GetInfoUseCase], queries: Annotated[GetFolderQuery, Query()]) -> Folder:
    """Получение файлов в папке.

    \f
    :param usecase:
    :param queries:
    :return:
    """
    try:
        return await usecase.get_folder_info(folder_name=queries.name)
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@file_router.get(
    "/list/folders",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": EntityNotFoundModel}},
)
async def get_folders_in_root(usecase: FromDishka[ListFoldersUseCase]) -> list[str]:
    """Получение папок в руте.

    \f
    :param usecase:
    :return:
    """
    try:
        return await usecase.list_folders_in_root()
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
