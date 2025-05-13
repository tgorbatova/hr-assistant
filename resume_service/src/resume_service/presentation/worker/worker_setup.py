import asyncio
import uuid
from asyncio import CancelledError
from collections.abc import AsyncGenerator, Callable
from time import time
from typing import Any, ParamSpec, Protocol, TypeVar, cast

import anyio
import structlog.stdlib
from redis.asyncio import Redis
from taskiq import (
    AsyncResultBackend,
    AsyncTaskiqDecoratedTask,
    Context,
    NoResultError,
    TaskiqMiddleware,
    TaskiqResult,
    TaskiqState,
)
from taskiq.abc.broker import AckableMessage
from taskiq.message import BrokerMessage, TaskiqMessage
from taskiq.receiver.params_parser import parse_params
from taskiq.receiver.receiver import QUEUE_DONE, Receiver, _run_sync  # noqa: PLC2701
from taskiq.utils import maybe_awaitable
from taskiq_redis import ListQueueBroker

from resume_service.domain.models.status import TaskStatus

# ruff: noqa: ANN401,BLE001,C901

CANCELLER_KEY = "__cancel_task_id__"

logger: structlog.stdlib.BoundLogger = structlog.get_logger("taskiq.cancellable_broker")

_FuncParams = ParamSpec("_FuncParams")
_ReturnType = TypeVar("_ReturnType")


class AsyncBrokerProto(Protocol):
    def find_task(self, task_name: str) -> AsyncTaskiqDecoratedTask[Any, Any] | None:
        """Find task."""

    def get_all_tasks(self) -> dict[str, AsyncTaskiqDecoratedTask[Any, Any]]:
        """Get all tasks."""

    def add_dependency_context(self, new_ctx: dict[Any, Any]) -> None:
        """Add dependency context to all tasks."""

    def add_middlewares(self, *middlewares: TaskiqMiddleware) -> None:
        """Add middlewares."""

    async def startup(self) -> None:
        """Start up the broker."""

    async def shutdown(self) -> None:
        """Shut down the broker."""

    async def kick(self, message: BrokerMessage) -> None:
        """Kick the broker."""

    def listen(self) -> AsyncGenerator[bytes | AckableMessage]:
        """Listen for incoming messages."""

    def register_task(
        self,
        func: Callable[_FuncParams, _ReturnType],
        task_name: str | None = None,
        **labels: Any,
    ) -> AsyncTaskiqDecoratedTask[_FuncParams, _ReturnType]:
        """Register a function as a taskiq task."""


class CancellableBroker(AsyncBrokerProto, Protocol):
    async def cancel_task(self, task_id: uuid.UUID) -> None:
        """Cancel task."""

    async def get_task_status(self, task_id: uuid.UUID) -> TaskStatus:
        """Get task status."""


class CancellableListQueueBroker(ListQueueBroker, CancellableBroker):
    def __init__(
        self,
        url: str,
        task_id_generator: Callable[[], str] | None = None,
        result_backend: AsyncResultBackend[Any] | None = None,
        queue_name: str = "taskiq",
        max_connection_pool_size: int | None = None,
        queue_name_cancel: str = "taskiq_cancel",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            url=url,
            task_id_generator=task_id_generator,
            result_backend=result_backend,
            queue_name=queue_name,
            max_connection_pool_size=max_connection_pool_size,
            **kwargs,
        )
        self.queue_name_cancel = queue_name_cancel

    async def get_task_status(self, task_id: uuid.UUID) -> TaskStatus:
        """Get the task status from Redis."""
        async with Redis(connection_pool=self.connection_pool) as redis_conn:
            status = await redis_conn.get(f"task_status:{task_id}")
            if status:
                return TaskStatus(status.decode("utf-8"))
            return TaskStatus.NOT_FOUND

    async def cancel_task(self, task_id: uuid.UUID) -> None:
        """Cancel a task and set its status to 'cancelled'."""
        logger.info("Attempting to cancel task %s", task_id)
        taskiq_message = self._prepare_message(task_id)
        broker_message = self.formatter.dumps(taskiq_message)
        async with Redis(connection_pool=self.connection_pool) as redis_conn:
            result = await redis_conn.publish(self.queue_name_cancel, broker_message.message)
            logger.info("Cancel message published to Redis. Receivers: %s", result)

    async def listen_canceller(self) -> AsyncGenerator[bytes]:
        """Listen to broker messages.

        :return:
        """
        async with Redis(connection_pool=self.connection_pool) as redis_conn:
            redis_pubsub_channel = redis_conn.pubsub()
            await redis_pubsub_channel.subscribe(self.queue_name_cancel)
            async for message in redis_pubsub_channel.listen():
                if not message:
                    continue
                if message["type"] != "message":
                    logger.debug("Received non-message from redis: %s", message)
                    continue
                yield message["data"]

    def _prepare_message(self, task_id: uuid.UUID) -> TaskiqMessage:
        return TaskiqMessage(
            task_id=self.id_generator(),
            task_name="canceller",
            labels={},
            labels_types={},
            args=[],
            kwargs={CANCELLER_KEY: str(task_id)},
        )


class CancellableReceiver(Receiver):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.broker: CancellableBroker
        super().__init__(*args, **kwargs)
        self.tasks: set[asyncio.Task[Any]] = set()

    def parse_message(self, message: bytes | AckableMessage) -> TaskiqMessage | None:
        """Parse broker message.

        :param message:
        :return:
        """
        message_data = message.data if isinstance(message, AckableMessage) else message
        try:
            taskiq_msg = self.broker.formatter.loads(message=message_data)
            taskiq_msg.parse_labels()
        except Exception as exc:
            logger.warning(
                "Cannot parse message: %s. Skipping execution.\n %s",
                message_data,
                exc,
                exc_info=True,
            )
            return None
        return taskiq_msg

    async def listen(self, finish_event: asyncio.Event) -> None:  # pragma: no cover
        """Iterate over tasks asynchronously.

        It uses listen() method of an AsyncBroker
        to get new messages from queues.

        Also, it has a finish_event, that indicates that
        we need to stop listening for new tasks and shutdown.
        """
        if self.run_startup:
            await self.broker.startup()
        logger.info("Listening started.")
        queue: asyncio.Queue[bytes | AckableMessage] = asyncio.Queue()

        async with anyio.create_task_group() as gr:
            gr.start_soon(self.prefetcher, queue, finish_event)
            gr.start_soon(self.runner, queue)
            gr.start_soon(self.runner_canceller)

        if self.on_exit is not None:
            self.on_exit(self)

    async def runner_canceller(self) -> None:
        """Cancel runner."""
        logger.info("Starting cancellation listener")

        def cancel_task(task_id: str) -> None:
            """Cancel function."""
            for task in self.tasks:
                if task.get_name() == task_id:
                    try:
                        cancelled = task.cancel()
                        logger.info("Cancelling task %s: ", "succeeded" if cancelled else "failed")
                        if not cancelled:
                            logger.warning("Could not find task %s to cancel or cancellation failed", task_id)
                    except Exception as e:
                        logger.error("Error while cancelling task %s: %s", task_id, e)

        iterator = cast("CancellableListQueueBroker", self.broker).listen_canceller()
        while True:
            try:
                message = await anext(iterator)
                taskiq_msg = self.parse_message(message)

                if not taskiq_msg:
                    logger.warning("Could not parse cancel message")
                    continue

                if CANCELLER_KEY in taskiq_msg.kwargs:
                    task_id = taskiq_msg.kwargs[CANCELLER_KEY]
                    if any(task.get_name() == task_id for task in self.tasks):
                        logger.info("Processing cancellation for task %s", task_id)
                        cancel_task(task_id)
            except asyncio.CancelledError:
                logger.info("Cancellation listener was cancelled")
                break
            except StopAsyncIteration:
                logger.info("Cancellation listener stopped")
                break
            except Exception as e:
                logger.error("Error in cancellation listener: %s", e)

    async def runner(self, queue: asyncio.Queue[bytes | AckableMessage]) -> None:
        """Runner function."""

        def task_cb(task: asyncio.Task[Any]) -> None:
            """Tasks' callback.

            This function used to remove task
            from the list of active tasks and release
            the semaphore, so other tasks can use it.

            :param task: finished task
            """
            logger.debug("Task %s completed and removed from tracking.", task.get_name())
            self.tasks.discard(task)
            if self.sem is not None:
                self.sem.release()

        while True:
            if self.sem is not None:
                await self.sem.acquire()

            self.sem_prefetch.release()
            message = await queue.get()
            if message is QUEUE_DONE:
                break

            taskiq_msg = self.parse_message(message)
            if not taskiq_msg:
                continue

            task = asyncio.create_task(
                self.callback(message=message, raise_err=False),
                name=str(taskiq_msg.task_id),
            )
            logger.debug("Created task %s, current tasks: %s", taskiq_msg.task_id, len(self.tasks))
            self.tasks.add(task)
            task.add_done_callback(task_cb)

    async def run_task(  # noqa: PLR0915, PLR0912
        self,
        target: Callable[..., Any],
        message: TaskiqMessage,
    ) -> TaskiqResult[Any]:
        """Actually executes functions.

        It has all needed parameters in
        message.

        If the target function is async
        it awaits it, if it's sync
        it wraps it in run_sync and executes in
        threadpool executor.

        Also, it uses LogsCollector to
        collect logs.

        :param target: function to execute.
        :param message: received message.
        :return: result of execution.
        """
        loop = asyncio.get_running_loop()
        returned = None
        found_exception: BaseException | None = None
        signature = None
        if message.task_name not in self.known_tasks:
            self._prepare_task(message.task_name, target)
        if self.validate_params:
            signature = self.task_signatures.get(message.task_name)
        dependency_graph = self.dependency_graphs.get(message.task_name)
        parse_params(signature, self.task_hints.get(message.task_name) or {}, message)

        dep_ctx = None
        # Kwargs are defined in another variable,
        # because we want to update them with
        # kwargs resolved by dependency injector.
        kwargs = {}
        if dependency_graph:
            # Create a context for dependency resolving.
            broker_ctx = self.broker.custom_dependency_context
            broker_ctx.update(
                {
                    Context: Context(message, self.broker),
                    TaskiqState: self.broker.state,
                },
            )
            dep_ctx = dependency_graph.async_ctx(
                broker_ctx,
                self.broker.dependency_overrides or None,
            )
            # Resolve all function's dependencies.

        # Start a timer.
        start_time = time()

        try:
            # We put kwargs resolving here,
            # to be able to catch any exception (for example ),
            # that happen while resolving dependencies.
            if dep_ctx:
                kwargs = await dep_ctx.resolve_kwargs()
            # We update kwargs with kwargs from network.
            kwargs.update(message.kwargs)
            is_coroutine = True
            # If the function is a coroutine, we await it.
            if asyncio.iscoroutinefunction(target):
                target_future = target(*message.args, **kwargs)
            else:
                is_coroutine = False
                # If this is a synchronous function, we
                # run it in executor.
                target_future = loop.run_in_executor(
                    self.executor,
                    _run_sync,
                    target,
                    message.args,
                    kwargs,
                )
            timeout = message.labels.get("timeout")
            if timeout is not None:
                if not is_coroutine:
                    logger.warning("Timeouts for sync tasks don't work in python well.")
                target_future = asyncio.wait_for(target_future, float(timeout))
            returned = await target_future
        except NoResultError as no_res_exc:
            found_exception = no_res_exc
            logger.warning(
                "Task %s with id %s skipped setting result.",
                message.task_name,
                message.task_id,
            )
        except CancelledError:
            logger.debug(
                "Task %s with id %s cancelled.",
                message.task_name,
                message.task_id,
            )

        except BaseException as exc:
            found_exception = exc
            logger.error(  # noqa: G201
                "Exception found while executing function: %s",
                exc,
                exc_info=True,
            )
        # Stop the timer.
        execution_time = time() - start_time
        if dep_ctx:
            args = (None, None, None)
            if found_exception and self.propagate_exceptions:
                args = (
                    type(found_exception),
                    found_exception,
                    found_exception.__traceback__,
                )
            await dep_ctx.close(*args)

        # Assemble result.
        result: TaskiqResult[Any] = TaskiqResult(
            is_err=found_exception is not None,
            log=None,
            return_value=returned,
            execution_time=round(execution_time, 2),
            error=found_exception,
            labels=message.labels,
        )
        # If exception is found we execute middlewares.
        if found_exception is not None:
            for middleware in self.broker.middlewares:
                if middleware.__class__.on_error != TaskiqMiddleware.on_error:
                    await maybe_awaitable(
                        middleware.on_error(
                            message,
                            result,
                            found_exception,
                        ),
                    )

        return result
