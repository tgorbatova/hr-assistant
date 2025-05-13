from dishka import Provider, Scope, provide

from front.infrastructure.repositories.files import FilesRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    files_repo = provide(FilesRepository)
