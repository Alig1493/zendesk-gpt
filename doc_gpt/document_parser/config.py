import os
from typing import Any


def get_env(env_var: str, default: Any = None) -> str:
    return os.getenv(env_var, default=default)
