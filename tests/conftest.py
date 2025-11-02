import sys
import os
from pathlib import Path

# Ensure the project root is on sys.path so tests can import the `app` package
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Optionally load .env for tests
env_path = ROOT / ".env"
if env_path.exists():
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=str(env_path))
