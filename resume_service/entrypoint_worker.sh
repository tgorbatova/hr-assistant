#!/bin/bash
echo "--------Running Resume Service Worker--------" &&
python -m uv run taskiq worker resume_service.main.worker.worker:taskiq_broker -fsd --receiver resume_service.main.worker.worker:Receiver
