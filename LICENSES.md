# Licensing & Attribution

OFFSIDE combines original source code with several third-party data sources and
models, **each governed by its own separate terms**. The MIT license on this
repository's code does **not** extend to any of the data or models below.

## Source code

- **This repository's code** — [MIT](LICENSE). © 2026 Hriday Vig.

## Models

- **IBM Granite** (`granite3.3:8b`, `granite-embedding:30m`) — Apache License 2.0.
  Used at build time only to generate frozen fixtures. The Apache-2.0 grant on the
  models does **not** extend to the data they are run over.
- **Docling models** (IBM) — Apache License 2.0.

## Data sources

### StatsBomb Open Data — proprietary, NOT open source

Tactical evidence for the 1986 Argentina v England match is derived from
[StatsBomb Open Data](https://github.com/statsbomb/open-data), used under the
**StatsBomb User Agreement**. This is a proprietary license, not an OSS license.

In compliance:

- **No raw StatsBomb event data is committed to this repository.** It is pulled at
  build time; only derived aggregates are persisted into fixtures. (Enforced by
  `.gitignore`.)
- **The StatsBomb attribution is displayed wherever Tactical evidence is shown** in
  the application interface.
- **Non-commercial use only.** This is a non-commercial hackathon entry.
- Redistribution of the underlying data is **not** permitted.

> "If you publish, transmit or otherwise make available any research, analysis or
> results based on StatsBomb Data, you must reference and attribute StatsBomb as the
> source of the Data."

### IFAB Laws of the Game

The *Laws of the Game* are published by the
[International Football Association Board (IFAB)](https://www.theifab.com/) and are ©
IFAB. The PDF is used here for non-commercial educational analysis. Quoted passages
are attributed to the specific Law and page of the official edition.

### Framing sources

Quotations used by the Framing lens are attributed to their specific named speaker,
publication, and date. They are reproduced under fair-use for commentary and
criticism, and are presented as *documented framings from specific sources* — never as
the views of any nation or its people.

## Build tools

- **Langflow** — open source (MIT-class). Used to author and export the orchestration
  pipeline.
- **Context Forge** (`IBM/mcp-context-forge`) — Apache License 2.0.
- **LanceDB** — Apache License 2.0.
