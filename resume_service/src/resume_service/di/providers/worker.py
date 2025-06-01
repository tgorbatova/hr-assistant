from dishka import Provider, Scope, alias, from_context, provide_all
from faststream.nats import NatsBroker

from resume_service.app.interfaces.inference import Inference
from resume_service.domain.services.convert import ConverterService
from resume_service.domain.services.inference import InferenceService


class WorkerProvider(Provider):
    scope = Scope.APP

    broker = from_context(NatsBroker)

    request = provide_all(ConverterService, InferenceService, scope=Scope.REQUEST)
    inference = alias(InferenceService, provides=Inference)
