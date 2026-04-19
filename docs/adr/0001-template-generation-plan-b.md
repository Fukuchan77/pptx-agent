# ADR 0001: テンプレート生成戦略 - Plan B（手動作成）の採用

## ステータス

Accepted（承認済み）

採用日：2026-04-05

## コンテキスト

### 背景

Phase 3（Template .pptx Generation Implementation）において、プログラム的なテンプレート生成を実装する必要がありました。これは以下の要件を満たすためです：

- **FR-CG-080**: テンプレート生成スクリプトの実装
- **FR-CG-081**: data-template.pptx の生成（チャート・テーブル用レイアウト）
- **FR-CG-082**: smartart-template.pptx の生成（SmartArt図形用レイアウト）
- **FR-CG-083**: 4種類のSmartArtレイアウト（Process、Hierarchy、Cycle、Relationship）

### 目的

テンプレート生成機能の実装により、以下を実現する予定でした：

1. **CI/CD自動化**: テンプレートファイルをプログラム的に生成し、リポジトリに手動でコミットする必要をなくす
2. **一貫性の保証**: コードベースからテンプレートを生成することで、構造の一貫性を保証する
3. **スケーラビリティ**: 新しいテンプレートタイプを追加する際のコスト削減
4. **テスト可能性**: テンプレート生成プロセスを自動テストに組み込む

### 技術的課題

Phase 3の実装中に、以下の根本的な技術制約が判明しました：

#### python-pptxライブラリの制限

1. **カスタムスライドレイアウトの作成不可**
   - python-pptxは既存のスライドマスター・レイアウトの読み取りは可能
   - しかし、新しいカスタムレイアウトをプログラム的に作成する機能は存在しない
   - スライドマスターの編集機能も提供されていない

2. **SmartArt図形の作成不可**
   - SmartArt図形はOffice Open XML（OOXML）の複雑なXML構造を持つ
   - python-pptxは既存のSmartArtへのテキスト入力のみサポート（[`populate_smartart()`](../../src/pptx_agent/pptx_wrapper/smartart.py:1)）
   - SmartArt図形自体の生成機能は提供されていない

3. **代替手段の限界**
   - lxmlによる直接的なXML操作も検討
   - しかし、スライドマスター/レイアウトのOOXML構造は極めて複雑
   - 手動で作成したテンプレートと同等の品質を保証することは実質不可能

### タイムボックスと決定プロセス

設計書（[`specs/002-content-generation/tasks.md`](../../specs/002-content-generation/tasks.md:1)）では以下のタイムボックス戦略が定義されていました：

- **Phase 3推定工数**: 3-5日間
- **SmartArt生成タイムボックス**: 3日間
- **Plan Bへの切り替え条件**: 技術的実現可能性の判断

実装時、python-pptxの技術制約が明確になった時点で、即座にPlan Bへ移行する決定を行いました。

## 決定事項

### Plan Bの採用：手動テンプレート作成

テンプレートファイル（`data-template.pptx`、`smartart-template.pptx`）はMicrosoft PowerPoint UIを使用して**手動で作成する**方針を採用しました。

### 実装内容

#### 1. テンプレート検証スクリプト

[`scripts/generate_templates.py`](../../scripts/generate_templates.py:1)は、当初の生成機能の代わりに以下を提供します：

- **検証機能**: 既存テンプレートが要件を満たすかをチェック
- **手動作成ガイド**: 不足しているテンプレートの作成手順を表示
- **テンプレート仕様参照**: 詳細な仕様書へのリンク提供

```python
def generate_data_template(output_path: str) -> None:
    """Provide instructions for manual data-template.pptx creation.

    PLAN B EXECUTION:
    python-pptx cannot create custom slide layouts programmatically.
    This function provides instructions for MANUAL template creation.
    """
```

#### 2. 詳細仕様書の作成

- [`templates/DATA-TEMPLATE-SPEC.md`](../../templates/DATA-TEMPLATE-SPEC.md:1): データ可視化テンプレートの仕様
- [`templates/SMARTART-TEMPLATE-SPEC.md`](../../templates/SMARTART-TEMPLATE-SPEC.md:1): SmartArtテンプレートの仕様
- [`templates/README.md`](../../templates/README.md:1): テンプレート全体のガイド

#### 3. テンプレート検証機能

[`src/pptx_agent/config.py`](../../src/pptx_agent/config.py:264)の[`validate_templates()`](../../src/pptx_agent/config.py:264)機能：

- アプリケーション起動時にテンプレートファイルの存在を確認
- `--generate-templates`フラグによる自動生成フォールバック（basic-template、japanese-templateのみ）
- 不足テンプレートの明確なエラーメッセージ提供

### Plan Bの技術的根拠

1. **実現可能性の優先**: 技術的に不可能なものを追求するより、実現可能な方法を選択
2. **品質の保証**: PowerPoint UIで作成することで、複雑なレイアウト・スタイルを完全にコントロール可能
3. **実装コストの削減**: 代替実装（XML直接操作など）の複雑さと不確実性を回避
4. **プロジェクト進行の優先**: テンプレート生成に時間を費やすより、コア機能の実装を優先

## 影響（Consequences）

### ポジティブな影響

1. **完全な品質コントロール**
   - PowerPoint UIを使用することで、デザイナーやユーザーが求める品質を確実に実現
   - 複雑なレイアウト、カラースキーム、フォント設定を正確に反映可能

2. **複雑な機能のサポート**
   - SmartArtの複雑なXML構造を手動で最適化可能
   - グラデーション、影、3D効果などの高度な視覚効果を利用可能

3. **メンテナンスの直感性**
   - PowerPointに慣れたユーザーであれば、誰でもテンプレートを編集可能
   - 視覚的なUIによるWYSIWYG編集

4. **即座の実装完了**
   - プログラム的実装の試行錯誤（3-5日以上）を回避
   - 手動作成は数時間で完了可能

### ネガティブな影響

1. **CI/CD自動化の制限**
   - テンプレートファイルをGitリポジトリに手動でコミットする必要
   - テンプレート生成をCI/CDパイプラインに組み込めない

2. **一貫性の手動管理**
   - 複数のテンプレート間の一貫性を手動で維持する必要
   - 仕様書とテンプレートファイルの同期を人手で確認

3. **スケーラビリティの課題**
   - 新しいテンプレートタイプを追加する際、手動作業が必要
   - 多数のテンプレートを管理する場合、作業コストが増大

4. **テスト自動化の限界**
   - テンプレート生成プロセス自体をユニットテストできない
   - 検証機能のテストのみ可能

### 対策（Mitigations）

#### 1. テンプレート検証機能の実装

[`validate_templates()`](../../src/pptx_agent/config.py:264)関数により、以下を実現：

```python
def validate_templates(templates_dir: Path | None = None,
                      auto_generate: bool = False) -> None:
    """Validate that required template files exist.

    - アプリケーション起動時の自動検証
    - 不足テンプレートの検出と詳細なエラーメッセージ
    - 自動生成オプション（basic/japaneseテンプレート）
    """
```

#### 2. 自動生成フォールバック機能

`--generate-templates`フラグにより、以下のテンプレートを自動生成：

- `basic-template.pptx`: 基本的な英語プレゼンテーションテンプレート
- `japanese-template.pptx`: 日本語最適化テンプレート

これにより、開発環境でのセットアップコストを削減。

#### 3. 詳細な仕様書の整備

- [`templates/DATA-TEMPLATE-SPEC.md`](../../templates/DATA-TEMPLATE-SPEC.md:1): 4つの必須レイアウト仕様
- [`templates/SMARTART-TEMPLATE-SPEC.md`](../../templates/SMARTART-TEMPLATE-SPEC.md:1): 4つのSmartArtタイプ仕様
- 各仕様書にスクリーンショットと詳細な手順を記載

#### 4. テンプレート検証テストの実装

[`tests/unit/test_generate_templates.py`](../../tests/unit/test_generate_templates.py:1)により：

- テンプレート検証ロジックのテスト（8テスト）
- 不足テンプレート検出のテスト
- 手動作成指示の明確性テスト
- template_parser互換性テスト

全テストが成功（8/8）：要件FR-CG-084（template_parser互換性）を満たす。

## 検討した代替案

### 代替案1: Plan A - 完全なプログラム的生成

**概要**:
python-pptxとlxmlを使用して、テンプレートファイルを完全にプログラム的に生成する。

**アプローチ**:

1. `Presentation()`で空のプレゼンテーションを作成
2. lxmlで`prs.slide_master._element`を直接操作
3. カスタムスライドレイアウトをXMLレベルで構築
4. SmartArtのOOXML構造を手動でアセンブル

**却下理由**:

- **技術的実現性**: python-pptxがスライドマスター編集をサポートしていない根本的制約
- **OOXML複雑性**: スライドレイアウトとSmartArtのXML構造が極めて複雑（数百～数千行のXML）
- **品質リスク**: 手動XML操作では、PowerPoint UI作成と同等の品質を保証できない
- **メンテナンスコスト**: XML生成コードの保守が困難
- **実装期間**: タイムボックス（3-5日）を大幅に超過する可能性が高い

**参考**: [`scripts/generate_templates.py`](../../scripts/generate_templates.py:4-6)のコメント参照

### 代替案2: ハイブリッドアプローチ

**概要**:
ベーステンプレートは手動作成し、プログラムで部分的にカスタマイズする。

**アプローチ**:

1. PowerPoint UIで基本的なテンプレートを作成（スライドマスターのみ）
2. プログラムで各スライドレイアウトを動的に生成
3. プレースホルダー配置をコードで調整
4. SmartArtのみ手動で挿入

**却下理由**:

- **複雑性の増大**: 手動部分とプログラム部分の境界が不明確
- **デバッグの困難**: 問題が手動部分かコード部分かの切り分けが困難
- **中途半端な自動化**: CI/CD完全自動化も完全な手動管理もできない
- **実装コスト**: Plan Aと同等の技術的課題を抱える
- **メンテナンス負荷**: 2つのメンテナンス経路（手動編集とコード修正）を管理

### 代替案3: 外部ツールの利用

**概要**:
python-pptx以外のライブラリ・ツールを使用する。

**検討した選択肢**:

- **COM Automation（pywin32）**: Windows専用、環境依存性が高い
- **LibreOffice UNO API**: 複雑なAPI、学習コストが高い
- **Aspose.Slides**: 商用ライブラリ、ライセンスコストが必要

**却下理由**:

- **プラットフォーム依存**: macOS/Linux環境でCI/CD実行できない（pywin32）
- **学習コスト**: 新しいAPI習得に時間がかかる（UNO）
- **ライセンス制約**: 商用利用にコストが発生（Aspose）
- **python-pptxとの統合**: 既存のpython-pptxベースコードとの統合が必要

## 参照（References）

### 関連ドキュメント

- [`specs/002-content-generation/tasks.md`](../../specs/002-content-generation/tasks.md:1) - Phase 3実装タスクとPlan B実行記録
- [`scripts/generate_templates.py`](../../scripts/generate_templates.py:1) - テンプレート検証スクリプト（Plan B実装）
- [`templates/README.md`](../../templates/README.md:1) - テンプレート全体ガイド
- [`templates/DATA-TEMPLATE-SPEC.md`](../../templates/DATA-TEMPLATE-SPEC.md:1) - データテンプレート仕様書
- [`templates/SMARTART-TEMPLATE-SPEC.md`](../../templates/SMARTART-TEMPLATE-SPEC.md:1) - SmartArtテンプレート仕様書

### 実装コード

- [`src/pptx_agent/config.py`](../../src/pptx_agent/config.py:264) - [`validate_templates()`](../../src/pptx_agent/config.py:264) 機能
- [`src/pptx_agent/pptx_wrapper/smartart.py`](../../src/pptx_agent/pptx_wrapper/smartart.py:1) - [`populate_smartart()`](../../src/pptx_agent/pptx_wrapper/smartart.py:1) 実装

### テストコード

- [`tests/unit/test_generate_templates.py`](../../tests/unit/test_generate_templates.py:1) - テンプレート検証テスト（8/8成功）
- [`tests/unit/test_template_validation.py`](../../tests/unit/test_template_validation.py:1) - テンプレート検証機能のテスト
- [`tests/unit/test_template_fallback.py`](../../tests/unit/test_template_fallback.py:1) - フォールバック機能のテスト

### 外部リソース

- [python-pptx Documentation](https://python-pptx.readthedocs.io/) - 公式ドキュメント
- [Office Open XML (OOXML) Specification](http://officeopenxml.com/) - OOXMLフォーマット仕様
- [Michael Nygard ADR Template](https://github.com/joelparkerhenderson/architecture-decision-record) - ADRフォーマット

## 今後の推奨アクション

この決定に基づく継続的な改善と拡張については、プロジェクトのissue trackerおよびロードマップを参照してください。

主な推奨事項：

- テンプレートライブラリの拡充（業種別・用途別テンプレート）
- テンプレート管理プロセスの改善（バージョン管理、品質保証）
- 技術的代替案の定期的な再評価（python-pptxの進化、新しいツール）
- コミュニティからのテンプレート寄贈とエコシステム構築

詳細なアクションアイテムおよび優先順位は、プロジェクトのissue trackerで継続的に管理されます。

## 結論

Plan B（手動テンプレート作成）の採用は、python-pptxライブラリの根本的な技術制約を考慮した、現実的かつ実用的な決定でした。

### 成功のポイント

1. **早期の技術検証**: タイムボックスを設定し、技術的実現可能性を早期に判断
2. **実用主義**: 理想的な自動化より、実現可能な品質を優先
3. **包括的な対策**: 検証機能、仕様書、フォールバック機能による多層的サポート
4. **透明性**: 決定プロセスと理由を明確に文書化

### 学んだ教訓

1. **技術制約の早期把握**: ライブラリの制限を早期に理解することの重要性
2. **プラグマティズムの価値**: 完璧な自動化より、実用的な解決策を選択
3. **代替手段の準備**: Plan Bを事前に定義しておくことで、迅速な意思決定が可能
4. **品質保証の多様化**: 自動化できない部分は、検証とドキュメントでカバー

Plan Bの採用により、プロジェクトは予定通り進行し、Phase 4以降のコア機能実装に注力することができました。この決定は、技術的制約を認識し、実用的な解決策を選択した好例として、今後のアーキテクチャ決定の参考になります。

---

**最終更新**: 2026-04-11
**文書作成者**: AI PowerPoint Generator Project Team
**レビュー**: 承認済み
