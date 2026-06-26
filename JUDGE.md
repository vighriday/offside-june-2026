# A judge's 90-second guide to OFFSIDE

**[► Open the live app](https://offside-june-2026.vercel.app/)** and try these five things —
each maps to one judging criterion.

### 1. Start on a *current* dispute — read THE SPLIT (Innovation + Challenge fit)
Click **The millimetre offside line** (marked `live`). A schematic shows the moment, then THE
SPLIT — four plain questions, with the real reason lit. Here **"Is the truth unknowable?" is
PRESENT**: semi-automated technology can see the moment, yet at a millimetre margin the exact
position is physically unrecoverable — which is why the authorities draw a deliberately thick
line. This is *this season*, not a famous old goal — and no percentages anywhere, because the
model **cannot** emit a number.

### 2. Click any PRESENT cell (Trust / Responsible AI)
A cell with a live tension traces straight to its source — the exact IFAB Law passage with
its page number, the StatsBomb data note, or a named quote. Every claim has a receipt.
Where there is no evidence, the cell says `NOT_DOCUMENTED` rather than guessing.

### 3. Switch to a *live* dispute (Challenge fit — this is the key one)

The chain at the top marks three incidents **`live`** — drawn from the current Laws and
season, not the archive. Click **The millimetre offside line**: THE SPLIT lights
**Indeterminacy = PRESENT** — the truth at the margin is physically unmeasurable, which is
why the authorities draw a deliberately thick line. This axis *never fires* on the famous
goals (their facts were always knowable); it is the current disputes that prove the four-axis
framework is load-bearing. Note what the live engine does on **The modern handball call**: it
reads the retrieved Law as *clear* and rules **Rule ambiguity = OUT**, attributing the fight
to opposed **Cultural framing** instead. On **The "subjective" VAR call** it goes further and
reports **Rule ambiguity = `NOT_DOCUMENTED`** — the written Law simply doesn't define the
threshold, so it refuses to invent a conflict. Either way the diagnostic resolves a dimension
from real retrieval, not by lighting it on cue.

### 3b. Walk the Divergence Lineage (Innovation + Technical depth)

Click across all six. THE SPLIT changes each time and a callout names the axis that flipped.
Across the set the dimensions **light up or rule themselves out from the evidence** — three
of the four fire (Decision-time, Indeterminacy, Cultural) and the fourth (Rule ambiguity)
either rules itself out (the engine reads the Law text as clear) or reports no governing
clause at all. Same engine, six different diagnoses, computed from evidence, not pre-written.

### 4. Toggle Rule Evolution on Lampard (Technical depth)
Select **Lampard's ghost goal** and switch the era toggle (2010 → 2026). The Decision-time
cell flips from **Present** to **Resolved** — goal-line technology now makes the fact
automatic, so the gap that was present in 2010 is ruled out today. Verdict-free: the call
isn't re-judged, only what was knowable in the moment.

### 5. Read the lens panels + the Granite Guardian seal (IBM tools)
Each of the four lenses reads only its own evidence. The **"Granite Guardian: grounded"**
seal is the novel move — a *second* IBM model audits the first's reading against its cited
page before it's shown. On Lampard, the Tactical lens says **insufficient evidence** on
purpose: there's no data anomaly to cite, and the system refuses to speculate.

### 6. (Optional) Watch the real engine run live (Technical execution)

The site reads frozen fixtures — static hosting has no GPU. To see it is a *system*, not six
hand-written answers, one command runs the actual Granite pipeline (three IBM models across
four lenses) and narrates each step:

```bash
python engine/scripts/analyze_live.py --incident offside-margin
```

It retrieves each lens's evidence, has Granite read it, has Granite Guardian audit each
reading, routes the survivors onto THE SPLIT, and prints the diagnosis live. This is what the
demo recording screen-captures end to end.

---

**Reproducibility:** the footer shows the IBM models and the corpus git SHA each analysis
was baked from. The live bake runs at temperature 0 with a fixed seed, so re-running it
reproduces the same SPLIT, the same citations, and the same Guardian verdicts; the offline
deterministic baker reproduces a fixture byte-for-byte. See [README.md](README.md) for the
architecture and [`engine/bake.ipynb`](engine/bake.ipynb) for the build.
