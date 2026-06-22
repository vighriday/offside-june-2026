"""Build-time configuration for the OFFSIDE engine.

All values have deterministic defaults and may be overridden by environment variables
(see ``.env.example``). Nothing here is read at web runtime — these settings only
govern the offline bake.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Defaults, kept in one place so the bake and any test reference the same constants.
DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "granite3.3:8b"
DEFAULT_EMBED_MODEL = "granite-embedding:30m"
DEFAULT_GUARDIAN_MODEL = "granite-guardian3:2b"
DEFAULT_SEED = 42
DEFAULT_NUM_CTX = 8192
DEFAULT_NUM_PREDICT = 1024


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw not in (None, "") else default


@dataclass(frozen=True)
class GraniteConfig:
    """Everything needed to call Granite deterministically."""

    host: str = DEFAULT_HOST
    model: str = DEFAULT_MODEL
    temperature: float = 0.0
    seed: int = DEFAULT_SEED
    num_ctx: int = DEFAULT_NUM_CTX
    num_predict: int = DEFAULT_NUM_PREDICT


def load_granite_config() -> GraniteConfig:
    """Build a :class:`GraniteConfig` from the environment, falling back to defaults.

    Temperature is intentionally **not** configurable away from 0 — the deterministic
    regime is a property of the engine, not a tunable.
    """
    return GraniteConfig(
        host=os.environ.get("OLLAMA_HOST", DEFAULT_HOST),
        model=os.environ.get("GRANITE_MODEL", DEFAULT_MODEL),
        temperature=0.0,
        seed=_env_int("GRANITE_SEED", DEFAULT_SEED),
        num_ctx=_env_int("GRANITE_NUM_CTX", DEFAULT_NUM_CTX),
        num_predict=_env_int("GRANITE_NUM_PREDICT", DEFAULT_NUM_PREDICT),
    )
