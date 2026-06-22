"""Prompt content guards — the load-bearing instructions must be present in every prompt.

These are not model tests; they assert the red-teamed safety rules survive any future
edit to the prompt text (a prompt that loses its anti-stereotyping or no-numbers rule
is a regression).
"""

from __future__ import annotations

from offside_engine.analyze.prompts import LENS_SYSTEM, SPLIT_SYSTEM


def test_every_lens_prompt_forbids_numbers():
    for lens, text in LENS_SYSTEM.items():
        assert "NEVER output a number" in text, f"{lens} lost the no-numbers rule"


def test_every_lens_prompt_has_the_insufficient_evidence_escape():
    for lens, text in LENS_SYSTEM.items():
        assert "INSUFFICIENT_EVIDENCE" in text, f"{lens} lost the cite-or-die escape"


def test_framing_prompt_carries_the_anti_stereotyping_rule():
    framing = LENS_SYSTEM["FRAMING"]
    assert "STEREOTYPING RULE" in framing
    assert "A nationality is NOT a source" in framing


def test_referee_prompt_carries_the_intent_test_disambiguation():
    referee = LENS_SYSTEM["REFEREE"]
    # the fix that stops "is the intent test" being misread as rule-ambiguity
    assert "intent test is NOT rule-ambiguity" in referee
    assert 'states the SANCTION' in referee  # do not claim a sanction clause voids a goal


def test_synthesis_carries_admission_precedence_and_feed_purity():
    # the two rules that produce the thesis-correct Hand of God SPLIT without hard-coding
    assert "HARD PRECONDITION" in SPLIT_SYSTEM
    assert "ADMITTING the act" in SPLIT_SYSTEM
    assert "FEED PURITY" in SPLIT_SYSTEM


def test_synthesis_names_no_player_or_expected_answer():
    # derived, not hard-coded: the prompt must not name the incident's answer
    lowered = SPLIT_SYSTEM.lower()
    for forbidden in ("maradona", "hand of god", "argentina", "england"):
        assert forbidden not in lowered, f"synthesis prompt leaks the answer: {forbidden}"
