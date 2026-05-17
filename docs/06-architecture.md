# lib-logical-consistency-prover System Architecture

> lib のアーキテクチャを定義する。モジュール構成・DFD・エラー処理を明確にする。
> design doc §7 Step 6 参照。
> **lib は caller を意識しない独立設計とすること（strategy-pattern-lib-impl.md 参照）。**

---

## 目的

spec と code の論理的一致性を形式的に証明し、PR blocking の判定根拠（EvaluationResult）を提供する。
Layer M（Z3 SMT + bisimulation）による決定論的証明を主体とし、Layer L（LLM stub）をオプションとして提供する。

## 入力 / 出力

| 種別 | 型 | 説明 |
|------|-----|------|
| 入力 | `SpecContent` | spec_ids, sections, trace_tags |
| 入力 | `CodeContent` | functions（FunctionNode リスト）, call_graph |
| 入力 | `StrategyConfig` | SMT ソルバ設定・タイムアウト・advisory_only フラグ等 |
| 出力 | `EvaluationResult` | verdict, confidence, evidence, fp_candidates |

---

## モジュール構成

```
lib_logical_consistency_prover/
├── __init__.py                # prove を公開
├── models.py                  # 型定義（dataclass）
├── prover.py                  # prove(spec, code, config) → EvaluationResult（メインエントリ）
├── spec_logic_extractor.py    # SpecContent から論理構造を抽出
├── contract_matcher.py        # spec logic と code contract をマッチング
├── smt_verifier.py            # Z3 SMT 検証（z3-solver）+ Paige-Tarjan bisimulation
└── layer_l_stub.py            # Layer L の stub（LLM なし環境でも動作）

tests/
├── __init__.py
├── test_fr01_spec_logic_extractor.py
├── test_fr02_contract_matcher.py
├── test_fr03_smt_verifier.py
├── test_fr04_prover.py
└── test_nfr01_graceful_degrade.py
```

| モジュール | 責務 | 決定論性 |
|-----------|------|---------|
| models.py | 全データクラス定義（SpecContent / CodeContent / EvaluationResult 等） | D |
| prover.py | prove() エントリポイント。Layer M → Layer L の呼び出しフローを制御。advisory_only 変換 | D |
| spec_logic_extractor.py | SpecSection.content から must/shall 等のパターンを抽出し論理命題リストを生成 | D |
| contract_matcher.py | FunctionNode.contracts と trace_tags を照合し spec-code ペアを構築 | D |
| smt_verifier.py | Z3 で spec logic ⊆ code contract を検証。z3 なし → graceful degrade。State Machine → Paige-Tarjan bisimulation | D |
| layer_l_stub.py | LLM を呼ばない stub。verdict="warning", confidence=0.5 を返す | D |

---

## DFD (Data Flow Diagram)

```
[SpecContent]  ──▶ [spec_logic_extractor.extract()]  ──▶ [spec_logic: List[Dict]]
                                                                  │
[CodeContent]  ──▶ [contract_matcher.extract_contracts()]        │
                         │                                        │
                         ▼                                        │
                 [code_contracts: List[Dict]]  ◀──────────────────┘
                         │
                         ▼
              [smt_verifier.verify(spec_logic, code_contracts, timeout_sec)]
                         │
                    ┌────┴────┐
               z3 OK │        │ z3 NG / timeout
                    ▼         ▼
             [SMT 結果]  [layer_l_stub.evaluate()]
                    │         │
                    └────┬────┘
                         ▼
              [prover._assemble_result(smt_out, config)]
              （advisory_only 変換を適用）
                         │
                         ▼
              [EvaluationResult] ──▶ [呼び出し元]
```

| プロセス | 入力 DF | 出力 DF | 決定論性 |
|---------|---------|---------|---------|
| spec_logic_extractor.extract | SpecContent | spec_logic: List[Dict] | D |
| contract_matcher.extract_contracts | CodeContent | code_contracts: List[Dict] | D |
| smt_verifier.verify | spec_logic, code_contracts, timeout_sec | smt_out: Dict | D |
| layer_l_stub.evaluate | spec_logic, code_contracts | stub_out: Dict | D |
| prover._assemble_result | smt_out / stub_out, config | EvaluationResult | D |

---

## エラー処理

| エラー条件 | 発生モジュール | 処理方針 | 例外型 |
|-----------|-------------|---------|-------|
| z3 が未インストール | smt_verifier.py | ImportError を catch し graceful degrade（verdict="warning", confidence=0.0）| なし（内部処理） |
| SMT タイムアウト | smt_verifier.py | TimeoutError を catch し layer_l_stub にフォールバック | なし（内部処理） |
| SpecContent が None | prover.py | ValueError を raise | `ValueError` |
| CodeContent が None | prover.py | ValueError を raise | `ValueError` |
| StrategyConfig が None | prover.py | デフォルト StrategyConfig を使用 | なし |

---

## 依存 OSS

| OSS | バージョン | 用途 | ライセンス |
|-----|-----------|------|---------|
| z3-solver | ^4.12 | SMT ソルバ（Layer M 主体） | MIT-like (z3 License) |
| networkx | ^3.3 | Paige-Tarjan bisimulation のグラフ構造管理補助 | BSD |

**Decision Log**: #6-1（アーキテクチャ選択の判断を記録）

---
