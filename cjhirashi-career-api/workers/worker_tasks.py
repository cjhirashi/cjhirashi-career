#!/usr/bin/env python3
"""
Entrypoint: worker-tasks
Consumes from Redis Streams and executes scheduled Bedrock agent tasks.
"""
import sys
import os

# Add src to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.workers.task_worker import main

if __name__ == "__main__":
    main()
