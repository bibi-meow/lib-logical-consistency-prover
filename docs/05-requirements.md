# lib-logical-consistency-prover Requirements

> cicd の lib-*.md から lib-level の機能要求（FR）を導出する。
> design doc §7 Step 6 参照。
> **Gherkin 形式で受入テスト（AT）を記述すること。**

---

## 対応 cicd lib 設計

| 設計ドキュメント | パス |
|---------------|------|
| lib-logical-consistency-prover.md | cicd/doc/sys/lib/verify-spec-code/lib-logical-consistency-prover.md |

---

## 機能要求一覧

| FR ID | 説明 | 決定論性 | Decision Log |
|-------|------|---------|-------------|
| LIB-FR-01 | spec の論理構造抽出 | D | #5-1 |
| LIB-FR-02 | code の contract 抽出（ContractInfo ベース） | D | #6-1 |
| LIB-FR-03 | Z3 SMT 検証（Layer M） | D | #5-1 |
| LIB-FR-04 | EvaluationResult 生成 | D | #7-1 |

## 非機能要求一覧

| NFR ID | 説明 | 決定論性 | Decision Log |
|--------|------|---------|-------------|
| LIB-NFR-01 | z3 がない環境でも動作（graceful degrade） | D | #5-3 |
| LIB-NFR-02 | advisory_only=True の場合は verdict を強制的に "warning" に変換 | D | #7-1 |

---

## LIB-FR-01: spec の論理構造抽出

**概要**: SpecContent.sections から前提→結論形式のロジック（論理命題）を識別し、構造化リストとして返す

**入力**: `SpecContent`（spec_ids, sections: List[SpecSection], trace_tags）
**出力**: `List[Dict]`（{"premise": str, "conclusion": str, "spec_id": str} のリスト）
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: spec 論理構造抽出
  SpecContent の sections から前提→結論形式のロジックを識別する

  Scenario: must/shall パターンから論理命題を抽出する
    Given SpecContent に "The system must return status 200 when authentication succeeds" を含む section がある
    When spec_logic_extractor.extract(spec_content) を呼ぶ
    Then 返り値のリストに premise="authentication succeeds", conclusion="return status 200" に相当するエントリが含まれる

  Scenario: 空の SpecContent を渡す
    Given SpecContent に sections が空リストである
    When spec_logic_extractor.extract(spec_content) を呼ぶ
    Then 空リストを返す（例外なし）
```

**AT ファイル**: `tests/test_fr01_spec_logic_extractor.py`
**Decision Log**: #5-1

---

## LIB-FR-02: code の contract 抽出（ContractInfo ベース）

**概要**: FunctionNode のリストから ContractInfo（preconditions, invariants）を抽出し、trace_tags で spec_id との対応付けを行う

**入力**: `CodeContent`（functions: List[FunctionNode], call_graph: CallGraph）
**出力**: `List[Dict]`（{"function_id": str, "spec_ids": List[str], "contracts": ContractInfo} のリスト）
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: code contract 抽出
  FunctionNode.contracts と trace_tags から contract を抽出し spec_id と対応付ける

  Scenario: precondition と trace_tag を持つ FunctionNode から contract を抽出する
    Given FunctionNode に preconditions=["x > 0"] と trace_tags に source_id="US-23" を含む ContractInfo がある
    When contract_matcher.extract_contracts(code_content) を呼ぶ
    Then 返り値に function_id, spec_ids=["US-23"], contracts.preconditions=["x > 0"] が含まれる

  Scenario: contract が空の FunctionNode を処理する
    Given FunctionNode に contracts が空の ContractInfo である
    When contract_matcher.extract_contracts(code_content) を呼ぶ
    Then 返り値に空の contracts エントリが含まれ例外を投げない
```

**AT ファイル**: `tests/test_fr02_contract_matcher.py`
**Decision Log**: #6-1

---

## LIB-FR-03: Z3 SMT 検証（Layer M）

**概要**: spec_logic と code_contract のマッチペアに対して z3 SMT ソルバで「spec の論理 ⊆ code の contract」を検証する。タイムアウト時は Layer L にフォールバック。z3 なし時は graceful degrade

**入力**: `List[Dict]`（spec_logic）, `List[Dict]`（code_contracts）, `int`（timeout_sec）
**出力**: `Dict`（{"verdict": str, "confidence": float, "evidence": str, "fp_candidates": list}）
**決定論性**: D（z3 証明結果）

### Gherkin 受入テスト

```gherkin
Feature: Z3 SMT 検証
  spec の論理と code の contract をマッチングし SMT ソルバで検証する

  Scenario: 全ペアが証明可能な場合
    Given spec_logic に {"premise": "x > 0", "conclusion": "y > 0", "spec_id": "US-23"} がある
    And code_contracts に {"spec_ids": ["US-23"], "contracts": ContractInfo(preconditions=["x > 0"])} がある
    When smt_verifier.verify(spec_logic, code_contracts, timeout_sec=30) を呼ぶ
    Then verdict が "pass" または "warning" であり confidence が 0.0 以上 1.0 以下である

  Scenario: z3 がインストールされていない環境
    Given z3 モジュールが利用できない（ImportError を模擬）
    When smt_verifier.verify(spec_logic, code_contracts, timeout_sec=30) を呼ぶ
    Then verdict="warning", confidence=0.0 を返し例外を投げない

  Scenario: 空の spec_logic と code_contracts
    Given spec_logic と code_contracts がともに空リスト
    When smt_verifier.verify([], [], timeout_sec=30) を呼ぶ
    Then verdict="pass", confidence=0.95 を返す（証明対象なし = 矛盾なし）
```

**AT ファイル**: `tests/test_fr03_smt_verifier.py`
**Decision Log**: #5-1

---

## LIB-FR-04: EvaluationResult 生成

**概要**: SMT 検証結果（および Layer L 結果）から EvaluationResult を組み立てる。advisory_only=True の場合は verdict を "warning" に変換する

**入力**: `SpecContent`, `CodeContent`, `StrategyConfig`
**出力**: `EvaluationResult`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: EvaluationResult 生成
  prove() 関数が StrategyConfig に従って EvaluationResult を返す

  Scenario: 通常モード（advisory_only=False）で全ペア証明済み
    Given SpecContent と CodeContent が一致している（空で証明対象なし）
    And StrategyConfig.params.advisory_only が False
    When prover.prove(spec, code, config) を呼ぶ
    Then EvaluationResult.verdict が "pass" または "warning" であり strategy_id が "logical_consistency_v1" である

  Scenario: advisory_only=True モードで fail が warning に変換される
    Given SMT 検証が矛盾を検出し verdict="fail" になるケース
    And StrategyConfig.params.advisory_only が True
    When prover.prove(spec, code, config) を呼ぶ
    Then EvaluationResult.verdict が "warning" に変換されている

  Scenario: EvaluationResult の全フィールドが揃っている
    Given 任意の SpecContent と CodeContent
    When prover.prove(spec, code, config) を呼ぶ
    Then strategy_id, verdict, confidence, evidence フィールドが全て存在する
```

**AT ファイル**: `tests/test_fr04_prover.py`
**Decision Log**: #7-1

---

## LIB-NFR-01: z3 がない環境でも動作（graceful degrade）

**概要**: z3-solver が pip install されていない環境でも ImportError を出さず動作する

**入力**: N/A（環境条件）
**出力**: verdict="warning", confidence=0.0
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: z3 なし環境での graceful degrade
  z3 がインストールされていない場合でも lib が正常に動作する

  Scenario: z3 import が失敗する環境
    Given z3 モジュールが sys.modules から除外されている
    When prover.prove(spec_content, code_content, config) を呼ぶ
    Then 例外を投げずに EvaluationResult を返す
    And verdict が "warning" または "pass" であり "fail" でも例外でもない
```

**AT ファイル**: `tests/test_nfr01_graceful_degrade.py`
**Decision Log**: #5-3

---

## LIB-NFR-02: advisory_only モード

**概要**: advisory_only=True の場合、EvaluationResult.verdict を強制的に "warning" に変換する

**入力**: `StrategyConfig.params.advisory_only = True`
**出力**: `EvaluationResult.verdict = "warning"`（元の verdict に関わらず）
**決定論性**: D

---
