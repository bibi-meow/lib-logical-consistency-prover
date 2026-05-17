# lib-logical-consistency-prover

A Python library for formally verifying that specification logic is consistent with code contracts.

## What it does

Given a specification (describing obligations like "when X, the system must Y") and code
(annotated with preconditions and invariants), this library checks whether the code contracts
satisfy the specification's logical requirements.

It uses two verification layers:

- **Layer M** (deterministic): Z3 SMT solving for formal proof of spec-code logical consistency
- **Layer L** (optional): Stub interface for LLM-based semantic evaluation

The library reports a verdict (`pass`, `fail`, `warning`) with a confidence score and evidence
string, making it suitable for automated PR gating.

## Installation

```bash
pip install lib-logical-consistency-prover

# With Z3 SMT support (recommended):
pip install "lib-logical-consistency-prover[smt]"
```

Without `z3-solver`, the library degrades gracefully to `verdict="warning", confidence=0.0`.

## Quick start

```python
from lib_logical_consistency_prover import prove
from lib_logical_consistency_prover.models import (
    SpecContent, SpecSection, SpecId,
    CodeContent, FunctionNode, ContractInfo, TraceTag,
)

# Build specification content
spec = SpecContent(
    spec_ids=[SpecId("REQ-001")],
    sections=[
        SpecSection(
            title="Authentication",
            content="When authentication succeeds, the system must return status 200.",
        )
    ],
)

# Build code content (functions with contracts)
code = CodeContent(
    functions=[
        FunctionNode(
            node_id="authenticate",
            kind="function",
            contracts=ContractInfo(preconditions=["authentication succeeds"]),
            trace_tags=[TraceTag(tag_type="spec", source_id="REQ-001")],
        )
    ]
)

# Prove consistency
result = prove(spec, code)
print(result.verdict)     # "pass" | "fail" | "warning" | "fp_candidate"
print(result.confidence)  # 0.0 – 1.0
print(result.evidence)    # Human-readable explanation
```

## Configuration

Pass a `StrategyConfig` to customize behavior:

```python
from lib_logical_consistency_prover.models import StrategyConfig

config = StrategyConfig(
    strategy_id="my_project_v1",
    params={
        "layer_m_smt_solver": "z3",         # SMT solver to use
        "layer_m_bisimulation": True,         # Enable state machine bisimulation
        "layer_m_timeout_sec": 30,            # Timeout for SMT solving (seconds)
        "advisory_only": False,               # If True, all verdicts become "warning"
        "blocking_mode": "auto",              # PR blocking policy
    }
)

result = prove(spec, code, config=config)
```

### Key parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `layer_m_smt_solver` | `str` | `"z3"` | SMT solver (`"z3"` is the only supported value) |
| `layer_m_timeout_sec` | `int` | `30` | Max seconds for SMT proof attempt |
| `layer_m_bisimulation` | `bool` | `True` | Enable Paige-Tarjan bisimulation for state machines |
| `advisory_only` | `bool` | `False` | Convert all non-fp_candidate verdicts to `"warning"` |
| `blocking_mode` | `str` | `"auto"` | PR blocking policy hint for the caller |

## Return value

`prove()` returns an `EvaluationResult`:

| Field | Type | Description |
|-------|------|-------------|
| `strategy_id` | `str` | The `strategy_id` from `StrategyConfig` |
| `verdict` | `str` | `"pass"` / `"fail"` / `"warning"` / `"fp_candidate"` |
| `confidence` | `float` | 0.95+ for proved, 0.6 for unproved pairs, 0.0 for degraded |
| `evidence` | `str` | Human-readable summary of what was proved / contradicted |
| `fp_candidates` | `list` | Potential false-positive pairs for review |

## Verdict semantics

| Verdict | Meaning | Confidence |
|---------|---------|-----------|
| `pass` | All spec-code pairs formally proved consistent | ≥ 0.95 |
| `fail` | Contradiction detected between spec and code contract | 1.0 |
| `warning` | Unproved pairs, timeout, or advisory-only mode | 0.0 – 0.6 |
| `fp_candidate` | Potential false positive — human review recommended | varies |

## Graceful degradation

If `z3-solver` is not installed, the library continues to function:

```python
from lib_logical_consistency_prover import prove
from lib_logical_consistency_prover.models import SpecContent, CodeContent

result = prove(SpecContent(), CodeContent())
# Works without z3 — returns verdict="warning", confidence=0.0
```

## Requirements

- Python 3.11+
- `networkx >= 3.3`
- `z3-solver >= 4.12` (optional, install via `[smt]` extra)

## License

MIT License — see [LICENSE](LICENSE).
