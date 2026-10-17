# a2a-tax

**Measure the token tax of Agent2Agent (A2A) endpoints. Dumb math, honest numbers, zero dependencies.**

[![Tests](https://img.shields.io/badge/tests-17%20passed-brightgreen)]() [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]()

The [A2A protocol](https://a2a-protocol.org) (Linux Foundation, backed by 150+ orgs) lets independent agents discover each other through an **AgentCard** and hand off tasks via JSON-RPC. It works — but every hop bills metadata nobody reads:

1. **The AgentCard** — re-fetched in full at the start of every session
2. **The JSON-RPC envelope** — method, id, params, context IDs, repeated on every message *and every poll*
3. **The task history** — the full message array replayed on every `tasks/get`. A 20-minute task that polls every 30s replays 40+ growing snapshots of itself.

None of it is the answer. All of it is on the bill.

## Install

```bash
pip install a2a-tax        # or: copy a2a_tax.py, it's one file
```

## Usage

```bash
$ a2a-tax scan https://travel-agent.example.com
total card tax: 391 tokens

  skills (5)                :    203 tok
  securitySchemes           :     56 tok
  description               :     43 tok
  ...

$ a2a-tax report https://travel-agent.example.com --polls 45 --history-len 50

  card fetch (per session) :     391 tok
  first message/send       :     186 tok
  each tasks/get poll      :   2,426 tok
  TOTAL per task           : 107,321 tok  (~$0.32)

  with the three-line fix:
    cache the card         : -    391 tok/task
    cap history at 10      :  23,501 tok total
    TOTAL after fix        :  23,501 tok  (~$0.07)
    savings                :  83,820 tok/task  (78%)
```

## The three-line fix

```python
CARD = fetch_agent_card()          # once per process, not per session
history = task["history"][-10:]    # cap what you replay
resp["result"] = {k: v for k, v in task.items() if k != "history"}  # trim when the caller didn't ask
```

## Honest numbers

Token counts are deterministic estimates (`chars/4`, the standard rule of thumb) — no model calls, no flaky sampling. Two runs of the same card produce identical numbers. Prices are input-token rates you supply; defaults assume $3/Mtok. The point is not decimal-perfect billing — it's seeing that the *shape* of the protocol multiplies metadata costs 10–100x per task, and that the fix is three lines.

## Commands

| Command | What it measures |
|---|---|
| `scan <url-or-file>` | Per-field + per-skill token cost of an AgentCard |
| `hop <url-or-file>` | One task lifecycle: card + first send + N polls |
| `report <url-or-file>` | Full bill, before/after the three-line fix, USD priced |

Flags: `--polls` (default 45), `--history-len` (default 50), `--cap` (apply a history cap), `--price-per-mtok`.

## Why this exists

A2A shipped in Azure AI Foundry and Amazon Bedrock. Multi-agent traffic is ramping. Every blog post about "agent cost" measures the model — none measures the **protocol tax**: the discovery, envelope, and replay overhead the spec itself generates. a2a-tax is the meter.

MIT license.
