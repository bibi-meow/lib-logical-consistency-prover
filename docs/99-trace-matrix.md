# lib-logical-consistency-prover Trace Matrix

> FR（機能要求）→ AT（受入テスト）→ Code（実装）→ Test（単体テスト）のトレーサビリティを管理する。
> design doc §7 Step 15 参照。
> **実装完了後に全 FR が網羅されていることを確認してから push すること。**

---

## Trace Matrix

| FR ID | FR 概要 | Gherkin シナリオ | 受入テストファイル | 実装ファイル | 単体テストファイル | 完了 |
|-------|---------|----------------|-----------------|------------|-----------------|------|
| LIB-FR-01 | spec の論理構造抽出 | Feature: spec 論理構造抽出 | tests/test_fr01_spec_logic_extractor.py | lib_logical_consistency_prover/spec_logic_extractor.py | tests/test_fr01_spec_logic_extractor.py (8 tests) | [x] |
| LIB-FR-02 | code の contract 抽出 | Feature: code contract 抽出 | tests/test_fr02_contract_matcher.py | lib_logical_consistency_prover/contract_matcher.py | tests/test_fr02_contract_matcher.py (9 tests) | [x] |
| LIB-FR-03 | Z3 SMT 検証（Layer M） | Feature: Z3 SMT 検証 | tests/test_fr03_smt_verifier.py | lib_logical_consistency_prover/smt_verifier.py | tests/test_fr03_smt_verifier.py (10 tests) | [x] |
| LIB-FR-04 | EvaluationResult 生成 | Feature: EvaluationResult 生成 | tests/test_fr04_prover.py | lib_logical_consistency_prover/prover.py | tests/test_fr04_prover.py (15 tests) | [x] |
| LIB-NFR-01 | z3 なし環境でも動作 | Feature: z3 なし環境での graceful degrade | tests/test_nfr01_graceful_degrade.py | lib_logical_consistency_prover/smt_verifier.py + layer_l_stub.py | tests/test_nfr01_graceful_degrade.py (5 tests) | [x] |
| LIB-NFR-02 | advisory_only モード | (LIB-FR-04 Gherkin 内に含む) | tests/test_fr04_prover.py::TestAdvisoryOnlyConversion | lib_logical_consistency_prover/prover.py | tests/test_fr04_prover.py (3 tests) | [x] |

---

## カバレッジサマリ

| 指標 | 件数 |
|------|------|
| FR 総数 | 4 |
| NFR 総数 | 2 |
| AT（Gherkin シナリオ）総数 | 5 ファイル / 47 テスト |
| 実装ファイル総数 | 6 (models.py, prover.py, spec_logic_extractor.py, contract_matcher.py, smt_verifier.py, layer_l_stub.py) |
| 単体テスト総数 | 47 |
| 全 FR 網羅済み | YES |

---

## トレーサビリティ確認チェックリスト

- [x] 全 FR ID が Trace Matrix に記載されている
- [x] 各 FR に少なくとも 1 件の Gherkin シナリオが対応している
- [x] 各 Gherkin シナリオに受入テストファイルのパスが記載されている
- [x] 各 FR に対応する実装ファイルが記載されている
- [x] 各 FR に対応する単体テストが記載されている
- [x] pytest で全テスト PASS が確認されている（47 passed in 0.37s）
- [x] カバレッジサマリの「全 FR 網羅済み」が YES になっている

**Decision Log**: #15-1（Trace Matrix 完成の確認を記録）

---

## 機械検証コマンド

```bash
# テスト収集確認
pytest tests/ --collect-only -q

# FR ID の grep 確認（全 LIB-FR-NN が実装・テストに存在するか）
grep -rn "LIB-FR-" lib_logical_consistency_prover/ tests/ docs/

# カバレッジ確認
pytest --cov=lib_logical_consistency_prover --cov-report=term-missing tests/
```
