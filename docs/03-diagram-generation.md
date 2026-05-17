# lib-logical-consistency-prover Diagram Generation

> 本 lib が diagram を生成するアルゴリズムを定義する。
> design doc §7 Step 4 参照。

---

## 適用外宣言

本 lib は diagram を生成しない。

**理由**: `02-diagram-spec.md` に記載の通り、本 lib は diagram を扱わない。出力は `EvaluationResult` データクラスのみである。フィードバックループ（Step 3→4）で仕様のズレは確認されていない。

**Decision Log**: #3-1

---
