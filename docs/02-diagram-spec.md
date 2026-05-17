# lib-logical-consistency-prover Diagram Spec

> 本 lib が生成・参照する diagram の仕様。
> design doc §7 Step 3 参照。

---

## 適用外宣言

本 lib は diagram を扱わない。

**理由**: SOT の出力型は `EvaluationResult`（verdict, confidence, evidence: str, fp_candidates: List[FPCandidate]）であり、diagram（グラフ画像・Mermaid テキスト等）は含まない。diagram の生成・レンダリングは呼び出し元（Verification Engine）の責務である。

SMT ソルバ（Z3）は内部的に制約グラフを構築するが、それは実装の内部状態であり、外部出力として expose しない。

**Decision Log**: #3-1

---
