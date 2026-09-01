"""Pytest configuration - add src/ to path and load test environment."""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load test environment variables
env_file = Path(__file__).parent / ".env.test"
if env_file.exists():
    load_dotenv(env_file)

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))
