"""IBM Granite Guardian — the second model that audits the first.

OFFSIDE's groundedness guarantee does not rest on trusting Granite. After Granite
produces a grounded reading, **a separate IBM model — Granite Guardian — checks that
reading against the exact source passages it claimed to use.** Guardian emits a single
token: ``No`` (the response is grounded in the context) or ``Yes`` (the groundedness
*risk* fired — the response makes a claim the context does not support).

Any reading Guardian flags is *demoted by our code*, never shown as if it were sound:

* a lens flagged ungrounded collapses to ``INSUFFICIENT_EVIDENCE``;
* a SPLIT cell flagged ungrounded collapses to ``NOT_DOCUMENTED``.

This is the build-time groundedness gate: a claim survives into a fixture only if the
first model asserted it *and* the second model could not refute it against the cited
page. The verdict is recorded as a :class:`TrustSeal`, frozen with temperature 0 — a
reviewer re-running the bake gets the identical seal. The seal records *that an IBM
safety model flagged the rationale as grounded against its cited context*; it is never
a claim that the rationale is true.

Reference: Granite Guardian emits one ``Yes``/``No`` token for the selected risk; the
``groundedness`` risk checks faithfulness of a response to its provided context.
"""

from __future__ import annotations

import ollama

from offside_engine.analyze.split_schema import GuardianVerdict
from offside_engine.config import (
    DEFAULT_GUARDIAN_MODEL,
    DEFAULT_HOST,
    DEFAULT_NUM_CTX,
    DEFAULT_SEED,
)

# Granite Guardian's risk selector for "is this response faithful to the context?".
GROUNDEDNESS_RISK = "groundedness"

# The single-token contract: Guardian answers Yes (risk present) or No (grounded).
_RISK_PRESENT = "yes"
_RISK_ABSENT = "no"

GUARDIAN_SYSTEM = "groundedness"
"""Granite Guardian selects its risk via the system prompt; ``groundedness`` asks
whether the assistant response is faithful to the provided context."""


def _verdict_from_token(token: str) -> GuardianVerdict:
    """Map Guardian's single output token to our verdict.

    ``No`` (groundedness risk absent) -> GROUNDED. ``Yes`` (risk present) -> UNGROUNDED.
    Anything we cannot read as a clean No is treated as UNGROUNDED — the gate fails
    *closed*, so an unparseable verdict can never wave an unverified claim through.
    """
    first = token.strip().split()[0].lower().strip(".:,") if token.strip() else ""
    if first == _RISK_ABSENT:
        return "GROUNDED"
    if first == _RISK_PRESENT:
        return "UNGROUNDED"
    return "UNGROUNDED"


def _format_context(citations_text: list[str]) -> str:
    """Join the cited passages into the single context block Guardian audits against."""
    return "\n\n".join(citations_text)


class GuardianClient:
    """A deterministic wrapper over the Ollama-hosted Granite Guardian model.

    One instance is built per bake and reused for every lens and cell. It holds no
    state beyond its config; ``check_groundedness`` is the only entry point.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_GUARDIAN_MODEL,
        host: str = DEFAULT_HOST,
        seed: int = DEFAULT_SEED,
        num_ctx: int = DEFAULT_NUM_CTX,
    ) -> None:
        self.model = model
        self._seed = seed
        self._num_ctx = num_ctx
        self._client = ollama.Client(host=host)

    @property
    def _options(self) -> dict[str, int | float]:
        return {"temperature": 0.0, "seed": self._seed, "num_ctx": self._num_ctx}

    def check_groundedness(
        self, *, query: str, context_passages: list[str], response: str
    ) -> GuardianVerdict:
        """Ask Guardian whether ``response`` is grounded in ``context_passages``.

        ``query`` is the task the response was answering (Guardian's ``user`` turn);
        ``context_passages`` are the cited source passages (its ``context`` turn);
        ``response`` is the reading under audit (its ``assistant`` turn). The risk is
        selected by the ``system`` turn carrying just ``"groundedness"`` — the IBM
        Granite Guardian Ollama convention.

        With no context passages there is nothing to be grounded against, so the gate
        fails closed and returns ``UNGROUNDED`` without a model call — a grounded claim
        must always have at least one cited passage behind it.
        """
        if not context_passages:
            return "UNGROUNDED"

        context = _format_context(context_passages)
        result = self._client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": GUARDIAN_SYSTEM},
                {"role": "user", "content": query},
                {"role": "context", "content": context},
                {"role": "assistant", "content": response},
            ],
            options=self._options,
        )
        return _verdict_from_token(result["message"]["content"])
