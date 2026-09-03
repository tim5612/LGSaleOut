"""Load machine-local LGSale settings without putting secrets in Git."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOCAL_ENV_PATH = BASE_DIR / ".env.local"


def load_local_env(path: Path = LOCAL_ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"缺少本機設定 {name}；請依 .env.example 建立 .env.local")
    return value


load_local_env()

if not os.getenv("LGSALEOUT_SESSION_SECRET"):
    secret_file = os.getenv("LGSALEOUT_SESSION_SECRET_FILE", ".lgsale-session-secret")
    secret_path = Path(secret_file)
    if not secret_path.is_absolute():
        secret_path = BASE_DIR / secret_path
    if secret_path.exists():
        os.environ["LGSALEOUT_SESSION_SECRET"] = secret_path.read_text(encoding="utf-8").strip()
