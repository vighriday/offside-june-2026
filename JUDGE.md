# A judge's 90-second guide to OFFSIDE

**[► Open the live app](https://offside-june-2026.vercel.app/)** and try these five things —
each maps to one judging criterion.

### 1. Read THE SPLIT (Innovation)
The four cells under the title are the whole idea: *why* the Hand of God stays contested,
decomposed across four fixed dimensions. Two are **RULED OUT** (the Law is clear; the act
is admitted) and two are **PRESENT** (what the referee could see; which nation is watching).
No percentages — the model **cannot** emit a number.

### 2. Click any PRESENT cell (Trust / Responsible AI)
A cell with a live tension traces straight to its source — the exact IFAB Law passage with
its page number, the StatsBomb data note, or a named quote. Every claim has a receipt.
Where there is no evidence, the cell says `NOT_DOCUMENTED` rather than guessing.

### 3. Switch to a *live* dispute (Challenge fit — this is the key one)

The chain at the top marks three incidents **`live`** — drawn from the current Laws and
season, not the archive. Click **The modern handball call**: THE SPLIT now lights **Rule
ambiguity = PRESENT** — the first incident where the *rulebook itself* is the problem (the
2024/25 Law keeps three competing handball tests). Then **The millimetre offside line** lights
**Indeterminacy = PRESENT** — the truth at the margin is physically unmeasurable, which is
why the authorities draw a deliberately thick line. These two axes *never fire* on the famous
goals; the current disputes are what prove the four-axis framework is load-bearing.

### 3b. Walk the Divergence Lineage (Innovation + Technical depth)

Click across all six. THE SPLIT changes each time and a callout names the axis that flipped.
Across the set **all four dimensions fire** — same engine, six different diagnoses, the proof
it's computed from evidence, not pre-written.

### 4. Toggle Rule Evolution on Lampard (Technical depth)
Select **Lampard's ghost goal** and switch the era toggle (2010 → 2026). The Decision-time
cell flips from PRESENT to **RESOLVED** — goal-line technology now makes the fact automatic.
Verdict-free: the call isn't re-judged, only what was knowable in the moment.

### 5. Read the lens panels + the Granite Guardian seal (IBM tools)
Each of the four lenses reads only its own evidence. The **"Granite Guardian: grounded"**
seal is the novel move — a *second* IBM model audits the first's reading against its cited
page before it's shown. On Lampard, the Tactical lens says **insufficient evidence** on
purpose: there's no data anomaly to cite, and the system refuses to speculate.

### 6. (Optional) Watch the real engine run live (Technical execution)

The site reads frozen fixtures — static hosting has no GPU. To see it is a *system*, not six
hand-written answers, one command runs the actual four-model pipeline and narrates each step:

```bash
python engine/scripts/analyze_live.py --incident offside-margin
```

It retrieves each lens's evidence, has Granite read it, has Granite Guardian audit each
reading, routes the survivors onto THE SPLIT, and prints the diagnosis live. (Shown running
in the demo video.)

---

**Reproducibility:** the footer shows the IBM models and the corpus git SHA each analysis
was baked from. The bake is deterministic (temperature 0) — re-running it on the same
corpus produces a byte-identical result. See [README.md](README.md) for the architecture
and [`engine/bake.ipynb`](engine/bake.ipynb) for the build.
