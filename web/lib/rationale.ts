// Display helper: strip raw citation-id parentheticals from a rationale before it is shown.
//
// The engine grounds every rationale sentence to a citation id and writes that id inline
// (e.g. "...does not stand (ifab-law12-handball-offence-p110).") so the Guardian audit and
// the cite-or-die guard can verify it. Those ids are internal provenance — the UI already
// surfaces the real sources via the "click to see N sources" trace and the citation panel,
// so the inline ids are redundant noise to a reader. This removes them from the DISPLAY text
// only; the fixture data (the exact string the second model audited) is never mutated.
//
// A citation id is a lowercase, hyphen-joined token with no spaces (e.g. "pg-hist-visible",
// "ifab-law12-handball-offence-p110", "sb-hand-of-god-body-part"). We strip it whether it is
// wrapped as "(id)", "([id])", or appears in a comma-separated list "(id-a, id-b)".

const ID_TOKEN = "[a-z0-9]+(?:-[a-z0-9]+)+"; // at least one hyphen — never matches a plain word
const ID_LIST = `${ID_TOKEN}(?:\\s*,\\s*${ID_TOKEN})*`;
// Match an optional leading space, then "(" or "([", the id list, then "])" or ")".
const PARENTHETICAL = new RegExp(`\\s*\\(\\[?(?:${ID_LIST})\\]?\\)`, "g");

export function cleanRationale(text: string): string {
  if (!text) return text;
  return (
    text
      .replace(PARENTHETICAL, "")
      // tidy any space left before sentence punctuation after a removal
      .replace(/\s+([.;,])/g, "$1")
      .replace(/\s{2,}/g, " ")
      .trim()
  );
}
