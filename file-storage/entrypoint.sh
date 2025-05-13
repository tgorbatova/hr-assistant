#!/bin/bash
echo "-------Starting File Storage Service--------" &&
source /app/.venv/bin/activate &&
python -m alembic upgrade head &&
echo "--------Running File Storage Service--------"
source .venv/bin/activate
uvicorn src.file_storage.main.fastapi.factory:create_app --factory --host 0.0.0.0 --port 5030