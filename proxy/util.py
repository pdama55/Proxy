import hashlib
import json
import math
import os
import random
from typing import Any


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256(canonical_json(obj))


def derive_seed(*parts: Any) -> int:
    """Stable sub-seed from arbitrary parts. Python's hash() is salted per process, so never use it."""
    return int(sha256(canonical_json([str(p) for p in parts]))[:12], 16)


def rng_for(*parts: Any) -> random.Random:
    return random.Random(derive_seed(*parts))


def json_clean(obj: Any) -> Any:
    """Make analysis output strict-JSON: NaN/inf become null, numpy scalars become Python numbers."""
    if isinstance(obj, float):
        return None if math.isnan(obj) or math.isinf(obj) else obj
    if isinstance(obj, dict):
        return {str(k): json_clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_clean(v) for v in obj]
    if hasattr(obj, "item"):
        return json_clean(obj.item())
    return obj


def load_dotenv(path) -> list[str]:
    """Minimal KEY=VALUE loader for the project's gitignored .env. Existing environment variables win.
    Returns the names it set, never the values."""
    set_names = []
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return set_names
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip().removeprefix("export ").strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            set_names.append(key)
    return set_names
