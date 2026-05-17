# lib-logical-consistency-prover Decision Log

> 全工程の意思決定を時系列で記録する。第三者がトレース可能にする目的。
> design doc §7 Step 0 参照。

---

## 決定 #0-1（工程 0 の 1 番目）

- **What**: lib-logical-consistency-prover の実装開始
- **Options considered**: (a) 既存 lib パターンをそのまま流用 / (b) SOT (lib-logical-consistency-prover.md) から導出
- **Decision**: (b) SOT から導出
- **Rationale**: libcreator フィロソフィー §9「新規手法構築: 既存テンプレートのコピーでなく cicd 設計から導出」に従う
- **Determinism**: D
- **Reviewable by**: docs/00-07 の各ドキュメントが cicd SOT の記述と一致しているかをレビューアが照合
- **Traces from**: libcreator サブエージェント指示（SOT: lib-logical-consistency-prover spec）
- **Traces to**: 全 Step 1-15

---

## 決定 #2-1（工程 2: User Story）

- **What**: US-23 を lib-level US に変換する
- **Options considered**: (a) cicd US-23 をそのまま記載 / (b) lib-level に re-phrase して受入条件を具体化
- **Decision**: (b) lib-level に re-phrase
- **Rationale**: lib は caller を意識しない独立設計（strategy-pattern-lib-impl.md 参照）。caller 依存の表現を避ける
- **Determinism**: N（US 表現は非決定論的）
- **Reviewable by**: US-L-01 が cicd US-23 の意図と一致しているかをレビューア確認
- **Traces from**: cicd SOT §対応 US: US-23
- **Traces to**: docs/05-requirements.md LIB-FR-01〜04

---

## 決定 #3-1（工程 3: Diagram Spec）

- **What**: 本 lib が diagram を扱うかの判断
- **Options considered**: (a) 扱う（SMT 証明グラフを生成）/ (b) 扱わない（EvaluationResult のみ返す）
- **Decision**: (b) 扱わない
- **Rationale**: SOT に「diagram 出力」の記述なし。出力は EvaluationResult (evidence: str)。diagram 生成は呼び出し元の責務
- **Determinism**: D
- **Reviewable by**: SOT の出力定義を参照（EvaluationResult のみ）
- **Traces from**: SOT §出力（EvaluationResult）
- **Traces to**: docs/02-diagram-spec.md、docs/03-diagram-generation.md（N/A 明記）

---

## 決定 #5-1（工程 5: OSS 選定 — SMT ソルバ）

- **What**: SMT ソルバの選定
- **Options considered**: (a) z3-solver (Microsoft) / (b) CVC5 / (c) custom SAT solver
- **Decision**: (a) z3-solver
- **Rationale**: SOT が `"layer_m_smt_solver": "z3"` と明記。Pythonバインディングが成熟（z3-solver PyPI）。MIT-like ライセンス。stars 10k+
- **Determinism**: D
- **Reviewable by**: pyproject.toml の dependencies に z3-solver が記載されているか確認
- **Traces from**: SOT §params.layer_m_smt_solver
- **Traces to**: docs/06-architecture.md, smt_verifier.py

---

## 決定 #5-2（工程 5: OSS 選定 — bisimulation）

- **What**: bisimulation 検証の実装方式
- **Options considered**: (a) Paige-Tarjan アルゴリズムを自前実装 / (b) networkx ベースのグラフ比較 / (c) bisimulation 専用ライブラリ
- **Decision**: (a) Paige-Tarjan を自前実装（networkx 補助利用）
- **Rationale**: 成熟した Python bisimulation ライブラリが存在しない。networkx はグラフ構造管理に利用し、等価性判定ロジックは自前で実装する。SOT §Layer M アルゴリズム step 4 が「Paige-Tarjan bisimulation」と明記
- **Determinism**: D
- **Reviewable by**: smt_verifier.py の bisimulation 関数が Paige-Tarjan の手順を実装しているか確認
- **Traces from**: SOT §Layer M アルゴリズム step 4
- **Traces to**: docs/06-architecture.md, smt_verifier.py

---

## 決定 #5-3（工程 5: OSS 選定 — Layer L）

- **What**: Layer L (LLM) の実装方式
- **Options considered**: (a) anthropic SDK を直接使う / (b) stub のみ（optional）/ (c) openai 互換インターフェース
- **Decision**: (b) stub のみ（layer_l_stub.py）
- **Rationale**: SOT が「Layer L のインターフェースを定義するが、実際の LLM 呼び出しはオプション」と明記。pip ユーザーが LLM なし環境でも動作できること（LIB-NFR-01）
- **Determinism**: D（stub は決定論的）
- **Reviewable by**: layer_l_stub.py が LLM を呼び出さず固定応答を返すことを確認
- **Traces from**: SOT §Layer L アルゴリズム
- **Traces to**: layer_l_stub.py

---

## 決定 #6-1（工程 6/7: Architecture）

- **What**: モジュール分割の方針
- **Options considered**: (a) 単一ファイル実装 / (b) SOT のモジュール構成通りに分割
- **Decision**: (b) SOT のモジュール構成通りに分割（6 モジュール）
- **Rationale**: SOT が `prover.py / spec_logic_extractor.py / contract_matcher.py / smt_verifier.py / layer_l_stub.py / models.py` を明示。トレーサビリティのため変更しない
- **Determinism**: D
- **Reviewable by**: lib_logical_consistency_prover/ のファイル構成と SOT のモジュール構成を照合
- **Traces from**: SOT §実装モジュール構成
- **Traces to**: docs/07-spec.py, 実装コード

---

## 決定 #7-1（工程 8: Spec — advisory_only 変換）

- **What**: advisory_only=True 時の verdict 変換タイミング
- **Options considered**: (a) 各モジュールで個別に変換 / (b) prover.py の最終出力で一括変換
- **Decision**: (b) prover.py の最終出力で一括変換
- **Rationale**: 単一変換点を持つことで副作用を最小化。SOT §LIB-NFR-02 が「advisory_only=True の場合は verdict を強制的に "warning" に変換」と定義
- **Determinism**: D
- **Reviewable by**: prover.py の prove() 最終行に advisory_only チェックがあるか確認
- **Traces from**: SOT §LIB-NFR-02
- **Traces to**: prover.py prove()

---

## 決定 #9-1（工程 9: scaffold）

- **What**: init-lib-repo.sh の実行タイミング
- **Options considered**: (a) docs/01-07 完成前に実行 / (b) docs/01-07 完成後に実行
- **Decision**: (b) docs/01-07 完成後に実行
- **Rationale**: lib-impl-process.md §Step 9 が「docs/01〜07 が揃った後に実行する」と明記
- **Determinism**: D
- **Reviewable by**: スクリプト実行前にドキュメント完備を確認
- **Traces from**: lib-impl-process.md §Step 9
- **Traces to**: pyproject.toml, lib_logical_consistency_prover/, tests/

---

## 決定 #15-1（工程 15: Trace Matrix）

- **What**: Trace Matrix の完了判定
- **Options considered**: (a) 手動チェックのみ / (b) pytest collect + grep で機械検証
- **Decision**: (b) pytest collect + grep で機械検証
- **Rationale**: lib-impl-process.md §Step 15 が「grep / pytest collect で機械検証可能」を必須とする
- **Determinism**: D
- **Reviewable by**: docs/99-trace-matrix.md のトレーサビリティ確認チェックリストが全チェック済み
- **Traces from**: lib-impl-process.md §Step 15
- **Traces to**: docs/99-trace-matrix.md

---

<!-- 各工程で判断が生じるたびに ## 決定 #N-M エントリを追記する -->
<!-- N = 工程番号（0-15）、M = その工程内の連番 -->
