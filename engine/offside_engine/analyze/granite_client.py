"""The one correct way to call IBM Granite in OFFSIDE.

Every Granite call in the bake goes through :func:`generate_structured`. It pins the
deterministic regime (temperature 0, fixed seed, fixed context window) and constrains
generation to a Pydantic schema via Ollama's ``format=`` grammar, so the model can
only emit a value the schema allows. For the Granite-facing models that means it is
*structurally incapable of emitting a number* — there is no number-shaped hole to
fill.

This module never relaxes those settings. Determinism across machines is best-effort
(which is precisely why fixtures are frozen to disk), but on a single build host two
consecutive runs with these settings are stable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar

import ollama
from pydantic import BaseModel

from offside_engine.config import GraniteConfig, load_granite_config

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class GenerationRecord:
    """What produced a piece of output — frozen alongside the fixture for provenance."""

    model: str
    options: dict[str, int | float] = field(default_factory=dict)


class GraniteClient:
    """A thin, deterministic wrapper over an Ollama-hosted Granite model.

    The client holds no mutable state beyond its config; it is safe to construct once
    per bake and reuse for every lens and every cell.
    """

    def __init__(self, config: GraniteConfig | None = None) -> None:
        self.config = config or load_granite_config()
        self._client = ollama.Client(host=self.config.host)

    @property
    def options(self) -> dict[str, int | float]:
        """The deterministic option block sent with every call."""
        return {
            "temperature": self.config.temperature,
            "seed": self.config.seed,
            "num_ctx": self.config.num_ctx,
            "num_predict": self.config.num_predict,
        }

    @property
    def record(self) -> GenerationRecord:
        """A provenance record to freeze next to whatever this client generates."""
        return GenerationRecord(model=self.config.model, options=dict(self.options))

    def generate_structured(
        self,
        *,
        schema: type[T],
        system: str,
        user: str,
    ) -> T:
        """Generate one schema-valid instance of ``schema`` from Granite.

        The model is constrained to ``schema.model_json_schema()`` by Ollama's grammar,
        then the raw content is re-validated through Pydantic — which both parses the
        result and re-applies the schema's own validators (cite-or-die, axis order,
        and the rest). A second validation guards against a silently-dropped ``format``.
        """
        response = self._client.chat(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            format=schema.model_json_schema(),
            options=self.options,
        )
        content = response["message"]["content"]
        return schema.model_validate_json(content)
