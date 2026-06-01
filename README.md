# Agent Factory Orchestrator

A meta-AI system that receives a requirement for a new AI capability and produces
a complete **Agent Development Pack** by driving an opinionated, 11-phase factory
pipeline powered by Claude (`claude-opus-4-8`).

## What it does

Given a raw requirement string, the orchestrator runs 11 sequential phases — each
building on the outputs of the prior ones — and emits a structured development
pack covering everything from requirement intake to a go/no-go readiness verdict.

| # | Phase | Output |
|---|-------|--------|
| 1 | Requirement Intake | Normalized Requirement Brief, scope, assumptions |
| 2 | Architecture Decision | Single vs multi-agent, components, trade-offs |
| 3 | Agent Characterization | Per-agent profiles & I/O contracts |
| 4 | Multi-Agent Orchestration | Coordination pattern, handoffs, shared state |
| 5 | Agent Development Plan | Stack, models, tools, build milestones |
| 6 | Workflow & Execution | Runtime flow, retries, human-in-the-loop |
| 7 | Prompt Engineering | Copy-pasteable system prompts per agent |
| 8 | Evaluation Design | Metrics, harness, concrete eval cases |
| 9 | Testing Strategy | Test pyramid + CI gating |
| 10 | Risks & Guardrails | Risk register + concrete mitigations |
| 11 | Readiness Assessment | Scorecard, rollout plan, go/no-go |

## Install

```bash
pip install -r requirements.txt
```

Set your API key (or run without one for mock mode):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or put it in a .env file
```

## CLI usage

```bash
# Full pipeline → markdown to stdout
python main.py "Build an AI customer support agent for an e-commerce platform"

# JSON to a file
python main.py "..." --output-format json --output-file pack.json

# Run a single phase
python main.py "..." --phase 2

# Stream output as it generates
python main.py "..." --stream
```

Flags: `--output-format {markdown,json}`, `--output-file PATH`, `--phase N`,
`--stream`, `--model ID`, `--mock`.

## Programmatic usage

```python
from agent_factory import AgentFactoryOrchestrator

orch = AgentFactoryOrchestrator()
pack = orch.run_full("Build a multi-agent research assistant ...")

print(pack.to_markdown())          # full report
print(pack.to_json())              # JSON serialization
pack.save_report("pack.md")        # write to disk

# Run one phase at a time, threading context forward:
out, pack = orch.run_phase(1, "...")
out, pack = orch.run_phase(2, "...", pack)

# Stream a phase:
for chunk in orch.stream_phase(3, "...", pack):
    print(chunk, end="")
```

## Example

```bash
python examples/run_example.py
```

Runs the full pipeline on a sample e-commerce support request and writes
`examples/example_pack.md`. Works in mock mode without an API key.

## How it works

- **Prompt caching.** The large, stable Agent Factory Orchestrator role lives in
  a single system prompt sent with `cache_control: {"type": "ephemeral", "ttl":
  "1h"}`. Every phase call reuses that cached prefix, so phases 2–11 read it at
  ~0.1× cost. See `agent_factory/utils/claude_client.py`.
- **Context threading.** Each phase's user message contains only the specific
  phase instruction plus the requirement and the outputs of all prior phases, so
  later phases build directly on earlier decisions.
- **Streaming.** Long generations stream under the hood (and via the public
  `stream_phase` / `--stream` API), using the SDK's `get_final_message()` for
  robustness against timeouts.
- **Adaptive thinking** (`thinking={"type": "adaptive"}`) and `effort: "high"`
  are used for this complex meta-reasoning task.
- **Graceful degradation.** With no `ANTHROPIC_API_KEY` (or the SDK uninstalled),
  the client runs in **mock mode**, returning deterministic placeholder text so
  the whole pipeline stays runnable for demos and tests.

## Project layout

```
agent_factory/
  orchestrator.py          # AgentFactoryOrchestrator
  prompts.py               # the full 11-phase system prompt (cached)
  phases/                  # phase1_intake.py ... phase11_readiness.py
  models/                  # AgentDevelopmentPack, AgentProfile, AgentContract, EvaluationCase
  utils/                   # claude_client.py (caching/streaming/mock), formatters.py
main.py                    # CLI
examples/                  # run_example.py, sample_requests.py
```

## Models

`AgentDevelopmentPack` aggregates all phase outputs plus extracted structured
artifacts (`AgentProfile`, `AgentContract`, `EvaluationCase`). It exposes
`to_markdown()`, `to_json()`, and `save_report(path, fmt)`.
```
```
