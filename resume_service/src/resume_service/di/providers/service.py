from dishka import Provider, Scope, provide

from resume_service.infrastructure.adapters.task import TaskAdapter


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    converter = provide(TaskAdapter, scope=Scope.APP)
