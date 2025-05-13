# mypy: disable-error-code="misc"
from dishka import Provider, Scope, WithParents, from_context, provide_all
from faststream.nats import NatsBroker

from file_storage.application.usecase.create import CreateInteractor
from file_storage.application.usecase.delete import DeleteInteractor
from file_storage.application.usecase.get_file import GetFileByIdInteractor
from file_storage.application.usecase.get_info import GetInfoInteractor
from file_storage.application.usecase.list_files import ListFiles
from file_storage.application.usecase.save import SaveFileInteractor
from file_storage.application.usecase.save_result import SaveResultInteractor

request_dependencies: list[type] = []


class AppProvider(Provider):
    scope = Scope.REQUEST

    broker = from_context(NatsBroker, scope=Scope.APP)

    dependencies = provide_all(
        WithParents[SaveFileInteractor],
        WithParents[SaveResultInteractor],
        WithParents[CreateInteractor],
        WithParents[DeleteInteractor],
        WithParents[GetFileByIdInteractor],
        WithParents[ListFiles],
        WithParents[GetInfoInteractor],
    )
