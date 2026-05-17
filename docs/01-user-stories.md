# lib-logical-consistency-prover User Stories

> cicd の sys.1-userstory.md の対応 US から lib-level US を導出する。
> design doc §7 Step 2 参照。

## 対応 cicd US

| cicd US ID | タイトル | 本 lib の関連性 |
|-----------|---------|--------------|
| US-23 | PR マージ時点で spec と code の論理的一致性が証明済であること | 直接対応 — この lib が証明を実行する |

---

## US-L-01: spec と code の論理的一致性を形式的に検証する

**As a** spec-reviewer エンジン（Verification Engine）
**I want** spec の論理構造と code の contract を照合し、Z3 SMT ソルバで形式的に証明する
**So that** PR マージ時点で spec と code の論理的一致性が証明済の状態を保証できる

**Acceptance Criteria:**
- [ ] SpecContent と CodeContent を入力として受け取り EvaluationResult を返す
- [ ] Z3 SMT ソルバで spec logic ⊆ code contract を検証できる
- [ ] 証明成功時は verdict="pass", confidence≥0.95 を返す
- [ ] 矛盾検出時は verdict="fail", confidence=1.0 を返す
- [ ] 未証明ペアがある場合は verdict="warning", confidence=0.6 を返す

**cicd US 参照**: US-23
**Decision Log**: #2-1

---

## US-L-02: z3 が利用できない環境でも動作する

**As a** pip ユーザー（z3 なし環境）
**I want** z3-solver がインストールされていない環境でも lib を import・実行できる
**So that** CI 環境の制約に関わらず基本的な評価フローを継続できる

**Acceptance Criteria:**
- [ ] z3 未インストール時は graceful degrade し、verdict="warning", confidence=0.0 を返す
- [ ] ImportError が外部に漏れない
- [ ] advisory_only=True の場合は全 verdict が "warning" に変換される

**cicd US 参照**: US-23（NFR 側面）
**Decision Log**: #2-1, #5-3

---

<!-- 追加 US は ## US-L-NN の形式で追加 -->
