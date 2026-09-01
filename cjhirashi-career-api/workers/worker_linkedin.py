#!/usr/bin/env python3
"""
Entrypoint: worker-linkedin
Consumes from Redis Streams and publishes scheduled LinkedIn posts.
"""
import sys
import os

# Add src to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.workers.linkedin_worker import main

if __name__ == "__main__":
    main()
