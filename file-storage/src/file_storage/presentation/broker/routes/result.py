import io

from dishka import FromDishka
from faststream.nats import NatsRouter
from starlette import status

from file_storage.application.interfaces.usecase.file import (
    GetFileByIdUseCase,
    SaveResultUseCase,
)
from file_storage.application.models.result import SaveResultDto
from file_storage.domain.exceptions.file import SaveFileError
from file_storage.domain.models.file import FileId
from file_storage.domain.models.result import ResultId
from file_storage.domain.repositories.js import stream
from file_storage.infrastructure.sqlalchemy.models.results import ResultType
from file_storage.presentation.broker.models.result import ConvertedMsgSchema, FormattedMsgSchema
from file_storage.presentation.fastapi.response_model import DetailedHttpException
from file_storage.utils.logging import logger

results_router = NatsRouter()


@results_router.subscriber("inference.converted", stream=stream)
@results_router.publisher("inference.converted.saved", stream=stream)
async def save_converted_result(
    msg: ConvertedMsgSchema, usecase: FromDishka[SaveResultUseCase], file_usecase: FromDishka[GetFileByIdUseCase]
) -> ResultId:
    """Сохранение результата.

    \f
    :param msg:
    :param usecase:
    :param file_usecase:
    :return:
    """
    try:
        logger.debug("Got message %s in inference.converted, starting saving process", msg)
        msg_schema = ConvertedMsgSchema.model_validate(msg)
        file = await file_usecase.get_file_info_by_id(file_id=FileId(msg_schema.file_id))

        byte_content = msg_schema.text.encode("utf-8")
        result = io.BytesIO(byte_content)
        size = len(byte_content)

        dto = SaveResultDto(
            id=SaveResultDto.new_id(),
            file_name=file.metadata.name,
            folder_name=file.metadata.folder_name,
            file_id=FileId(msg_schema.file_id),
            path=file.metadata.path,
            type=ResultType.CONVERT,
            size=size or 0,
        )
        return await usecase.save(result_info=dto, result=result)
    except SaveFileError as exc:
        logger.error(str(exc))
        raise DetailedHttpException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@results_router.subscriber("inference.formatted", stream=stream)
@results_router.publisher("inference.formatted.saved", stream=stream)
async def save_formatted_result(
    msg: FormattedMsgSchema, usecase: FromDishka[SaveResultUseCase], file_usecase: FromDishka[GetFileByIdUseCase]
) -> ResultId:
    """Сохранение результата.

    \f
    :param msg:
    :param usecase:
    :param file_usecase:
    :return:
    """
    try:
        logger.debug("Got message %s in inference.formatted, starting saving process", msg)
        msg_schema = FormattedMsgSchema.model_validate(msg)
        file = await file_usecase.get_file_info_by_id(file_id=FileId(msg_schema.file_id))

        json_content = msg_schema.resume.model_dump_json(indent=2).encode("utf-8")
        logger.debug("got json content %s", json_content)
        result = io.BytesIO(json_content)
        logger.debug("Dumped JSON string: %s", result)
        size = result.getbuffer().nbytes
        logger.debug("Dumped JSON size: %s", size)

        dto = SaveResultDto(
            id=SaveResultDto.new_id(),
            file_name=file.metadata.name,
            folder_name=file.metadata.folder_name,
            file_id=FileId(msg_schema.file_id),
            path=file.metadata.path,
            type=ResultType.FORMAT,
            size=size or 0,
        )
        return await usecase.save(result_info=dto, result=result)
    except SaveFileError as exc:
        logger.error(str(exc))
        raise DetailedHttpException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
