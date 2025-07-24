#!/bin/bash

# Activate virtual environment

# Set environment variables for CUDA
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Start Celery worker
# celery -A Backend worker  --pool=solo --loglevel=info
# celery -A Backend worker --pool=eventlet --concurrency=4
celery -A Backend worker --pool=gevent --concurrency=16
