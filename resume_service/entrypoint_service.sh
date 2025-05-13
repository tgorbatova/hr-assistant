#!/bin/bash
echo "--------Running Resume Service--------"
source .venv/bin/activate
uvicorn src.resume_service.main.api.factory:create_app --factory --host 0.0.0.0 --port 5000