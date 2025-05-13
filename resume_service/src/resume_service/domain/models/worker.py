from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Worker:
    max_jobs: int
    job_timeout: int
    max_tries: int
