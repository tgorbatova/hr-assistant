from dishka import Provider, Scope, alias, provide, provide_all, from_context

from resume_service.app.interfaces.inference import Inference
from resume_service.domain.services.convert import ConverterService
from resume_service.domain.services.inference import InferenceService
from faststream.nats import NatsBroker


class WorkerProvider(Provider):
    scope = Scope.APP

    broker  = from_context(NatsBroker)

    request = provide_all(ConverterService, InferenceService, scope=Scope.REQUEST)
    inference = alias(InferenceService, provides=Inference)
