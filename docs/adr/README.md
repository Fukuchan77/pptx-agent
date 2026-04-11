# Architecture Decision Records (ADR)

## 概要

このディレクトリには、AI PowerPoint Presentation Generatorプロジェクトにおける重要なアーキテクチャ決定の記録（Architecture Decision Records、ADR）が含まれています。

ADRは、プロジェクトの技術的な決定、その背景、理由、影響を文書化するための軽量な手法です。各ADRは、特定の決定に関する完全な情報を提供し、将来の開発者や関係者が過去の決定の背景を理解できるようにします。

## ADRとは？

Architecture Decision Records（アーキテクチャ決定記録）は、ソフトウェアアーキテクチャに関する重要な決定を記録する文書です。各ADRには以下が含まれます：

- **タイトル**: 決定内容の簡潔な説明
- **ステータス**: 提案中、承認済み、却下、非推奨など
- **コンテキスト**: 決定が必要となった背景と状況
- **決定事項**: 採用した解決策の詳細
- **影響**: 決定がもたらす結果（ポジティブ、ネガティブ、対策）
- **代替案**: 検討したが採用しなかった選択肢とその理由

## フォーマット

このプロジェクトのADRは、[Michael Nygard's ADR template](https://github.com/joelparkerhenderson/architecture-decision-record)に基づいています。

## ADRリスト

| 番号                                       | タイトル                                        | ステータス | 採用日     |
| ------------------------------------------ | ----------------------------------------------- | ---------- | ---------- |
| [0001](0001-template-generation-plan-b.md) | テンプレート生成戦略 - Plan B（手動作成）の採用 | Accepted   | 2026-04-05 |

## ADRの作成ガイドライン

新しいADRを作成する場合は、以下のガイドラインに従ってください：

### 1. ファイル命名規則

```
XXXX-brief-title.md
```

- `XXXX`: 4桁の連番（例：0001、0002）
- `brief-title`: 決定内容を簡潔に表す英語のタイトル（ケバブケース）
- 例：`0002-llm-provider-selection.md`

### 2. 必須セクション

各ADRには以下のセクションを含める必要があります：

```markdown
# ADR XXXX: タイトル

## ステータス

[Proposed | Accepted | Rejected | Deprecated | Superseded]

## コンテキスト

決定が必要となった背景、問題、制約条件

## 決定事項

採用した解決策の詳細

## 影響（Consequences）

### ポジティブな影響

### ネガティブな影響

### 対策（Mitigations）

## 検討した代替案

### 代替案1: ...

### 代替案2: ...

## 参照（References）

関連ドキュメント、コード、外部リソースへのリンク
```

### 3. 作成タイミング

ADRは以下の状況で作成します：

- **技術スタックの選択**: ライブラリ、フレームワーク、プラットフォームの選定
- **アーキテクチャパターンの採用**: マイクロサービス、モノリス、レイヤードアーキテクチャなど
- **重要な設計決定**: データモデル、API設計、セキュリティ戦略など
- **トレードオフのある決定**: パフォーマンス vs. 保守性など
- **方針変更**: 既存の決定を覆す、または修正する場合

### 4. 作成プロセス

1. **連番の決定**: 最新のADR番号を確認し、次の番号を使用
2. **ドラフト作成**: テンプレートに従ってドラフトを作成
3. **レビュー**: チームメンバーによるレビュー
4. **承認**: ステータスを "Accepted" に変更
5. **README更新**: このREADMEのADRリストに新しいADRを追加

### 5. ベストプラクティス

- **簡潔性**: 各セクションは明確かつ簡潔に記述
- **客観性**: 感情や主観的な意見ではなく、技術的な事実とトレードオフに基づく
- **完全性**: 将来の読者が決定の背景を理解できるよう、十分な情報を提供
- **タイムリー性**: 決定が行われた直後に記録（記憶が新鮮なうちに）
- **不変性**: 承認後のADRは変更しない（新しいADRで supersede する）

## ADRのステータス遷移

```
Proposed → Accepted → [Deprecated | Superseded]
         ↓
       Rejected
```

- **Proposed**: 提案中、議論中
- **Accepted**: 承認され、実装に使用される
- **Rejected**: 却下された（理由を明記）
- **Deprecated**: 非推奨（より良い方法が見つかったが、まだ使用中）
- **Superseded**: 新しいADRに置き換えられた（置き換え先のADRを明記）

## よくある質問（FAQ）

### Q: すべての技術決定をADRにする必要がありますか？

A: いいえ。ADRは**重要な**アーキテクチャ決定のためのものです。以下は記録する価値があります：

- プロジェクトの方向性に影響を与える決定
- 変更が困難な決定
- トレードオフを伴う決定
- チーム全体で理解が必要な決定

日常的な実装の詳細（変数名、ファイル配置など）はADRにする必要はありません。

### Q: ADRを後から変更できますか？

A: 承認後のADRは**変更すべきではありません**。ADRは歴史的記録です。決定を変更する必要がある場合は、新しいADRを作成し、古いADRを "Superseded" としてマークします。

軽微な修正（誤字脱字、リンク修正など）は許可されますが、決定内容自体の変更は新しいADRで行います。

### Q: 日本語と英語、どちらで書くべきですか？

A: このプロジェクトでは、ADRは**日本語**で記述します。これはプロジェクトの標準に従うためです。ただし、以下の要素は英語を使用できます：

- ファイル名
- コード例
- 技術用語（必要に応じて日本語の説明を追加）

### Q: 却下された代替案も記録すべきですか？

A: はい、**必ず記録してください**。却下された代替案とその理由を記録することで：

- 同じ議論を繰り返さない
- 将来、状況が変わった際に再評価できる
- 決定の背景を完全に理解できる

## 参考リソース

- [Architecture Decision Records (ADR) by Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
- [Joel Parker Henderson's ADR Templates](https://github.com/joelparkerhenderson/architecture-decision-record)
- [Documenting Architecture Decisions - ThoughtWorks](https://www.thoughtworks.com/en-us/radar/techniques/lightweight-architecture-decision-records)

## 貢献

プロジェクトメンバーは、重要なアーキテクチャ決定を行った際にADRを作成することを推奨します。質問や提案がある場合は、プロジェクトのメインREADMEを参照してください。

---

**最終更新**: 2026-04-11  
**メンテナー**: AI PowerPoint Generator Project Team
