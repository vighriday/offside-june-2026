"""The validated Studio form — the user-supplied evidence for one contested decision."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Quote(BaseModel):
    """One named-source quote. Every quote needs a speaker and where it was said — no
    anonymous evidence, same receipt standard as the curated incidents."""
    model_config = ConfigDict(extra="forbid")
    speaker: str = Field(min_length=1)
    source: str = Field(min_length=1)  # where it was said, e.g. "post-match press conference"
    text: str = Field(min_length=1)


class FormPayload(BaseModel):
    """The Studio form. The user brings the human evidence; the engine brings the rulebook."""
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    settled_statement: str = Field(min_length=1)  # what everyone agrees happened
    historical_note: str = Field(default="")       # what could/couldn't be seen, tech, review
    quotes: list[Quote] = Field(default_factory=list)
    tactical_note: str | None = None
