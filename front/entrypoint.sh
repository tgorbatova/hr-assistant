#!/bin/bash
echo "--------Running Front Service--------"
source .venv/bin/activate
uvicorn src.front.main.fastapi.factory:create_app --factory --host 0.0.0.0 --port 5000