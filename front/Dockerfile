FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY ./uv.lock /app/uv.lock
WORKDIR /app

RUN pip install uv
RUN python -m uv sync --frozen --no-group dev


COPY ./docker.yaml /app/docker.yaml
COPY ./src /app/src
COPY ./entrypoint.sh /app/entrypoint.sh

ENV PYTHONPATH=/app/src
ENV ENV_TYPE=docker

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
