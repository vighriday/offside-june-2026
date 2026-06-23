# OFFSIDE behind IBM Context Forge (MCP gateway)

OFFSIDE exposes its engine as an **MCP server**
([`engine/offside_engine/mcp_server.py`](../engine/offside_engine/mcp_server.py)) so any
agent — or the **IBM Context Forge** MCP gateway/registry — can call it as a tool. This is
what turns OFFSIDE from a website into a reusable capability: an agent that needs to explain
*why* a refereeing decision stays contested can call `decompose_disagreement` and get the
structured, page-cited SPLIT back, with the no-numbers contract intact (states, never scores).

## Tools

| Tool | Returns |
|------|---------|
| `list_incidents()` | the contested decisions OFFSIDE can decompose |
| `decompose_disagreement(incident_id)` | THE SPLIT for one incident — per-axis state + rationale + the source pages grounding each live axis |

## Run the server

```bash
python -m offside_engine.mcp_server      # stdio transport (what MCP clients / Context Forge speak)
```

## Register it in Context Forge

IBM Context Forge ([`ibm.github.io/mcp-context-forge`](https://ibm.github.io/mcp-context-forge/))
is a gateway and registry for MCP servers. Register OFFSIDE as a stdio MCP server — for
example, in the gateway's server config:

```json
{
  "servers": {
    "offside": {
      "command": "python",
      "args": ["-m", "offside_engine.mcp_server"],
      "cwd": "engine",
      "description": "Decompose why a contested football decision stays disputed (THE SPLIT), grounded to the IFAB Laws.",
      "tools": ["list_incidents", "decompose_disagreement"]
    }
  }
}
```

Once registered, Context Forge proxies the two tools to any connected MCP client behind a
single gateway endpoint — the same engine the site reads, now agent-callable.
