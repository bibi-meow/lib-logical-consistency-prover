# lib-logical-consistency-prover API Spec

> lib の公開 API を定義する。dataclass / TypedDict で型を明示し、pseudocode でアルゴリズムを示す。
> design doc §7 Step 7 参照。
> **API signature は 06-architecture.md の DFD と一致させること。**

---

## 公開 API 一覧

| 関数 / クラス | 入力型 | 出力型 | 決定論性 |
|-------------|-------|-------|---------|
| `prove(spec, code, config)` | `SpecContent, CodeContent, StrategyConfig \| None` | `EvaluationResult` | D |
| `spec_logic_extractor.extract(spec)` | `SpecContent` | `List[Dict[str, str]]` | D |
| `contract_matcher.extract_contracts(code)` | `CodeContent` | `List[Dict]` | D |
| `smt_verifier.verify(spec_logic, code_contracts, timeout_sec)` | `List[Dict], List[Dict], int` | `Dict` | D |
| `layer_l_stub.evaluate(spec_logic, code_contracts)` | `List[Dict], List[Dict]` | `Dict` | D |

---

## 型定義

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

# ---- 入力型 ----
@dataclass
class SpecId:
    id_str: str

@dataclass
class SpecSection:
    title: str
    content: str
    level: int = 1

@dataclass
class TraceTag:
    tag_type: str
    source_id: str
    target_id: str = ""

@dataclass
class ContractInfo:
    preconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)

@dataclass
class FunctionNode:
    node_id: str
    kind: str
    contracts: ContractInfo = field(default_factory=ContractInfo)
    docstring: Optional[str] = None
    trace_tags: List[Any] = field(default_factory=list)

@dataclass
class CallGraph:
    nodes: List[str] = field(default_factory=list)
    edges: List[tuple] = field(default_factory=list)

@dataclass
class SpecContent:
    spec_ids: List[SpecId] = field(default_factory=list)
    sections: List[SpecSection] = field(default_factory=list)
    trace_tags: List[TraceTag] = field(default_factory=list)

@dataclass
class CodeContent:
    functions: List[FunctionNode] = field(default_factory=list)
    call_graph: CallGraph = field(default_factory=CallGraph)

# ---- 出力型 ----
@dataclass
class FPCandidate:
    spec_id: str
    function_id: str
    reason: str
    confidence: float = 0.5

@dataclass
class EvaluationResult:
    strategy_id: str
    verdict: str          # "pass" | "fail" | "warning" | "fp_candidate"
    confidence: float
    evidence: str
    fp_candidates: List[FPCandidate] = field(default_factory=list)

@dataclass
class StrategyConfig:
    strategy_id: str = "logical_consistency_v1"
    input_types: List[str] = field(default_factory=lambda: ["spec", "code"])
    executor_lib: str = "lib_logical_consistency_prover.prover"
    params: Dict[str, Any] = field(default_factory=lambda: {
        "layer_m_smt_solver": "z3",
        "layer_m_bisimulation": True,
        "layer_l_model": "claude-sonnet-4-6",
        "layer_l_confidence_threshold": 0.75,
        "layer_m_timeout_sec": 30,
        "blocking_mode": "auto",
        "advisory_only": False,
    })
    enabled: bool = True
```

---

## API signature

```python
def prove(
    spec: SpecContent,
    code: CodeContent,
    config: StrategyConfig | None = None,
) -> EvaluationResult:
    """
    spec と code の論理的一致性を形式的に証明する。

    Layer M（Z3 SMT + bisimulation）で証明を試み、失敗時は Layer L（stub）にフォールバックする。
    advisory_only=True の場合は最終 verdict を "warning" に変換する。

    Args:
        spec: 仕様コンテンツ（SpecContent）
        code: コードコンテンツ（CodeContent）
        config: StrategyConfig。None の場合はデフォルト設定を使用

    Returns:
        EvaluationResult: verdict, confidence, evidence, fp_candidates を含む結果

    Raises:
        ValueError: spec または code が None の場合

    Traces: LIB-FR-01, LIB-FR-02, LIB-FR-03, LIB-FR-04, LIB-NFR-01, LIB-NFR-02
    Decision Log: #7-1
    """
    ...
```

---

## Pseudocode

```
function prove(spec: SpecContent, code: CodeContent, config: StrategyConfig) -> EvaluationResult:
  1. [入力検証]: spec と code が None でないことを確認 → ValueError
  2. config が None なら StrategyConfig() を使用
  3. params = config.params を取得

  4. [spec_logic 抽出（LIB-FR-01）]:
     spec_logic = spec_logic_extractor.extract(spec)
     # SpecSection.content から must/shall/shall not パターンを識別
     # 各マッチに {"premise": str, "conclusion": str, "spec_id": str} を生成

  5. [code_contracts 抽出（LIB-FR-02）]:
     code_contracts = contract_matcher.extract_contracts(code)
     # FunctionNode.contracts.preconditions / invariants を収集
     # FunctionNode.trace_tags から spec_ids を対応付け

  6. [Layer M: SMT 検証（LIB-FR-03）]:
     timeout_sec = params.get("layer_m_timeout_sec", 30)
     TRY:
       smt_out = smt_verifier.verify(spec_logic, code_contracts, timeout_sec)
       # z3 で spec logic ⊆ code contract を証明
       # State Machine を含む場合は Paige-Tarjan bisimulation も実行
     EXCEPT (z3 not available | timeout):
       smt_out = layer_l_stub.evaluate(spec_logic, code_contracts)
       # stub: verdict="warning", confidence=0.5

  7. [EvaluationResult 組み立て（LIB-FR-04）]:
     result = _assemble_result(smt_out, config)
     # 全ペア証明済み → verdict="pass", confidence=0.95
     # 未証明ペアあり → verdict="warning", confidence=0.6
     # 矛盾検出 → verdict="fail", confidence=1.0
     # 証明不可 → verdict="warning", confidence=0.0

  8. [advisory_only 変換（LIB-NFR-02）]:
     IF params.get("advisory_only", False):
       result.verdict = "warning"

  9. return result
```

**Decision Log**: #7-1（API 設計の判断を記録）

---
