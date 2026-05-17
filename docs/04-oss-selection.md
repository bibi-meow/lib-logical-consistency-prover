# lib-logical-consistency-prover OSS 選定

> System Architecture に組み込む OSS を評価マトリクスで選定する。
> design doc §7 Step 5 参照。

---

## 選定対象

| 機能 | 必要理由 |
|------|---------|
| SMT ソルバ | spec logic ⊆ code contract の形式的証明（Layer M） |
| グラフ処理（bisimulation 補助） | 状態機械を含む場合の Paige-Tarjan bisimulation 実装補助 |

---

## 選定基準

| 基準 | 重み | 説明 |
|------|------|------|
| 機能性 | 0.4 | アルゴリズムの正確性・カバレッジ |
| 性能 | 0.3 | 計算量・実測処理速度 |
| 保守性 | 0.2 | 最終更新・star 数・コミュニティ |
| ライセンス | 0.1 | MIT / Apache 互換 |

---

## 評価マトリクス: SMT ソルバ

参照: SOT §params.layer_m_smt_solver = "z3"

| 候補 | 機能性 (0.4) | 性能 (0.3) | 保守性 (0.2) | ライセンス (0.1) | 合計スコア |
|------|:-----------:|:--------:|:-----------:|:-------------:|:---------:|
| z3-solver | 5 | 5 | 5 | 5 | 5.0 |
| CVC5 | 5 | 4 | 4 | 4 | 4.4 |
| custom SAT | 2 | 2 | 1 | 5 | 2.2 |

計算式: `score = 機能性×0.4 + 性能×0.3 + 保守性×0.2 + ライセンス×0.1`

### 決定

**採用**: z3-solver
**採用バージョン**: ^4.12
**理由**:
- SOT が `"layer_m_smt_solver": "z3"` と明記（一次資料）
- Python バインディング成熟（PyPI `z3-solver` パッケージ）
- Microsoft Research 開発・継続的保守（GitHub stars 10k+）
- MIT-like ライセンス（z3 License）

**Decision Log**: #5-1

---

## 評価マトリクス: グラフ処理（bisimulation 補助）

参照: SOT §Layer M アルゴリズム step 4「Paige-Tarjan bisimulation で遷移系の等価性確認」

| 候補 | 機能性 (0.4) | 性能 (0.3) | 保守性 (0.2) | ライセンス (0.1) | 合計スコア |
|------|:-----------:|:--------:|:-----------:|:-------------:|:---------:|
| networkx | 4 | 4 | 5 | 5 | 4.4 |
| igraph | 4 | 5 | 4 | 5 | 4.4 |
| 自前実装のみ | 3 | 3 | N/A | 5 | 3.2 |

### 決定

**採用**: networkx（補助）+ 自前 Paige-Tarjan 実装
**採用バージョン**: ^3.3
**理由**:
- 成熟した Python bisimulation ライブラリが存在しないため、グラフ構造管理に networkx を利用し、等価性判定は自前で実装する
- networkx は PyPI で広く使われており保守性が高い
- BSD ライセンス（MIT 互換）

**Decision Log**: #5-2

---

## Layer L（LLM）の OSS 選定

**採用**: stub のみ（LLM なし環境でも動作）
**理由**: SOT が「Layer L のインターフェースを定義するが、実際の LLM 呼び出しはオプション」と明記。LIB-NFR-01（graceful degrade）を満たすため stub 実装とする。

**Decision Log**: #5-3

---
