[English](smartart-manual-setup.md) | [日本語](smartart-manual-setup_ja.md)

# SmartArt テンプレート手動作成ガイド（本番用）

## 目次

1. [概要](#概要)
2. [目的の違い](#目的の違い)
3. [問題の背景](#問題の背景)
4. [手動作成手順](#手動作成手順)
5. [検証手順](#検証手順)
6. [既存コードへの統合](#既存コードへの統合)
7. [トラブルシューティング](#トラブルシューティング)
8. [参考資料](#参考資料)
9. [まとめ](#まとめ)

## 概要

**このガイドは「本番用テンプレート作成」のための完全版です。**

このドキュメントでは、Microsoft PowerPointでスライドマスター/レイアウトにSmartArtを配置した本番用テンプレートを作成する手順を説明します。

統合テストを通すだけなら、[smartart-quickstart_ja.md](smartart-quickstart_ja.md)を参照してください（10-15分で完了）。

## 目的の違い

| 目的                       | 方法                                      | 対象                | ガイド                                                               |
| -------------------------- | ----------------------------------------- | ------------------- | -------------------------------------------------------------------- |
| **統合テストを通す**       | 通常のスライドにSmartArt挿入              | `prs.slides`        | [smartart-quickstart_ja.md](smartart-quickstart_ja.md) 👈 簡単・迅速 |
| **本番用テンプレート作成** | スライドマスター/レイアウトにSmartArt配置 | `prs.slide_layouts` | 👉 このドキュメント                                                  |

### 統合テストを通すだけなら

**[smartart-quickstart_ja.md](smartart-quickstart_ja.md)を参照してください（10-15分で完了）**

このドキュメントは、本番環境で使用する完全なテンプレートを作成したい場合に使用します。

## 問題の背景

### なぜテストがスキップされるのか

1. **python-pptxの制限**: `python-pptx`ライブラリは、SmartArt図形を**プログラムで作成できません**
2. **テストの要件**: 統合テスト（[test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py)）は、本物のSmartArt図形を含むテンプレートが必要
3. **現状**: [templates/smartart-test-template.pptx](../templates/smartart-test-template.pptx)は、プレースホルダー図形のみを含む（本物のSmartArtではない）

### スキップされる3つのテスト

1. [test_smartart_with_real_template_process_flow()](../tests/integration/test_smartart_real_templates.py) - プロセスフロー型SmartArtのテスト
2. [test_smartart_all_types_in_real_template()](../tests/integration/test_smartart_real_templates.py) - 4種類のSmartArtタイプのテスト
3. [test_smartart_end_to_end_workflow()](../tests/integration/test_smartart_real_templates.py) - エンドツーエンドワークフローのテスト

## 手動作成手順

### 前提条件

- **Microsoft PowerPoint**（Windows版またはMac版）が必要
  - LibreOffice ImpressはSmartArt作成機能が限定的なため非推奨
- PowerPoint 2016以降を推奨

### Step 1: 新しいテンプレートファイルを作成

1. Microsoft PowerPointを起動
2. 「新しいプレゼンテーション」を選択
3. 白紙のプレゼンテーションで開始

### Step 2: スライドマスタービューに移動

1. メニューバーから「表示」→「スライドマスター」を選択
2. スライドマスタービューに入る

### Step 3: カスタムレイアウトを作成（4種類）

#### レイアウト1: Process Flow (プロセスフロー)

1. 「レイアウトの挿入」をクリック
2. レイアウト名を「Process Flow」に変更
3. 「挿入」→「SmartArt」を選択
4. **カテゴリ**: 「プロセス」
5. **種類**: 「基本プロセス」または「ステップアッププロセス」を選択
6. SmartArtを挿入後、以下を設定:
   - ノード数: **3個**に設定（Add Shape/Delete Shapeで調整）
   - 各ノードのテキスト: "Node 1", "Node 2", "Node 3"
   - サイズ: スライドの中央に配置、幅8インチ×高さ4インチ程度
7. タイトルプレースホルダーを追加（「プレースホルダーの挿入」→「タイトル」）

#### レイアウト2: Hierarchy (階層構造)

1. 新しいレイアウトを挿入
2. レイアウト名を「Hierarchy」に変更
3. 「挿入」→「SmartArt」を選択
4. **カテゴリ**: 「階層構造」
5. **種類**: 「組織図」を選択
6. SmartArtを挿入後、以下を設定:
   - ノード数: **3-4個**（トップレベル1個、子2-3個）
   - テキスト例:
     - レベル0: "CEO"
     - レベル1: "VP Sales", "VP Engineering"
   - サイズ: 同様に中央配置
7. タイトルプレースホルダーを追加

#### レイアウト3: Cycle (サイクル)

1. 新しいレイアウトを挿入
2. レイアウト名を「Cycle」に変更
3. 「挿入」→「SmartArt」を選択
4. **カテゴリ**: 「循環」
5. **種類**: 「基本的な循環」を選択
6. SmartArtを挿入後、以下を設定:
   - ノード数: **4個**（Plan, Do, Check, Act）
   - 各ノードのテキスト: "Plan", "Do", "Check", "Act"
7. タイトルプレースホルダーを追加

#### レイアウト4: Relationship (関係)

1. 新しいレイアウトを挿入
2. レイアウト名を「Relationship」に変更
3. 「挿入」→「SmartArt」を選択
4. **カテゴリ**: 「関係」
5. **種類**: 「基本ベン」または「グループ化リスト」を選択
6. SmartArtを挿入後、以下を設定:
   - ノード数: **3個**
   - テキスト: "Group 1", "Group 2", "Group 3"
7. タイトルプレースホルダーを追加

### Step 4: スライドマスタービューを終了して保存

1. 「スライドマスター」タブの「マスター表示を閉じる」をクリック
2. 「ファイル」→「名前を付けて保存」を選択
3. **保存先**: `tests/fixtures/smartart_test_template.pptx`
4. **ファイル形式**: PowerPointプレゼンテーション (\*.pptx)
5. 保存

### Step 5: 本番用テンプレートもコピー作成（オプション）

```bash
# コマンドラインで実行
cp tests/fixtures/smartart_test_template.pptx templates/smartart-template.pptx
```

## 検証手順

### 1. スクリプトでテンプレートを検証

```bash
# テンプレートにSmartArtが含まれているか確認
uv run python -c "
from pptx import Presentation
from pathlib import Path

template_path = 'tests/fixtures/smartart_test_template.pptx'
if not Path(template_path).exists():
    print(f'❌ Template not found: {template_path}')
    exit(1)

prs = Presentation(template_path)
smartart_count = 0

for slide in prs.slides:
    for shape in slide.shapes:
        if hasattr(shape, '_element'):
            elem = shape._element
            if 'graphicFrame' in str(elem.tag):
                smartart_count += 1
                print(f'✓ Found SmartArt: {shape.name}')

if smartart_count > 0:
    print(f'\n✓ Template has {smartart_count} SmartArt shapes')
else:
    print('\n❌ No SmartArt shapes found')
"
```

### 2. テストを実行

```bash
# スキップされていたテストを実行
uv run pytest tests/integration/test_smartart_real_templates.py -v

# 期待される結果:
# test_smartart_with_real_template_process_flow PASSED
# test_smartart_all_types_in_real_template PASSED
# test_smartart_end_to_end_workflow PASSED
```

### 3. すべてのテストを実行

```bash
# 全テストスイートを実行して回帰がないか確認
uv run pytest tests/ -v
```

## 既存コードへの統合

### 統合は不要 - テンプレートファイルの追加のみ

このタスクでは、**既存のコードを変更する必要はありません**。以下の理由により:

1. **テストコードは既に完成**: [test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py)のテストロジックは完全
2. **SmartArt処理コードも完成**: [smartart_builder.py](../src/pptx_agent/pptx_wrapper/smartart_builder.py)と[smartart.py](../src/pptx_agent/pptx_wrapper/smartart.py)は実装済み
3. **必要なのはテンプレートファイルのみ**: 手動作成したテンプレートファイルを配置するだけ

### ファイル配置場所

作成したテンプレートファイルは以下のいずれかに配置:

```
tests/fixtures/smartart_test_template.pptx  ← テスト用（優先）
templates/smartart-template.pptx            ← 本番用（オプション）
```

### テストのfixtureが自動検出

[template_with_smartart](../tests/integration/test_smartart_real_templates.py) fixtureが、以下の順序で自動的にテンプレートを検索:

```python
possible_paths = [
    "tests/fixtures/smartart_test_template.pptx",  # 最優先
    "templates/smartart-template.pptx",            # 次点
    "tests/fixtures/basic-template.pptx",          # フォールバック
]
```

## トラブルシューティング

### 問題: SmartArtが検出されない

**症状**: テストが依然としてスキップされる

**解決策**:

1. PowerPointでファイルを開き、SmartArtが実際に挿入されているか確認
2. 通常の図形ではなく、SmartArt（グラフィックフレーム）であることを確認
3. スライドマスタービューで作成したか確認（通常のスライドではなく）

### 問題: ノード数が合わない

**症状**: `ValueError: Expected X nodes but SmartArt has Y nodes`

**解決策**:

1. SmartArtのノード数をテストデータと一致させる
2. Process Flow: 3ノード
3. Hierarchy: 3-4ノード
4. Cycle: 4ノード
5. Relationship: 3ノード

### 問題: LibreOffice Impressで作成した

**症状**: SmartArtが正しく動作しない

**解決策**:

- LibreOffice ImpressはSmartArt作成機能が限定的
- **Microsoft PowerPointで再作成することを推奨**

## 参考資料

- [SMARTART-TEMPLATE-SPEC.md](../templates/SMARTART-TEMPLATE-SPEC.md) - SmartArtテンプレートの仕様
- [test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py) - 統合テストコード
- [smartart_builder.py](../src/pptx_agent/pptx_wrapper/smartart_builder.py) - SmartArtビルダー実装
- [smartart.py](../src/pptx_agent/pptx_wrapper/smartart.py) - SmartArtラッパー実装

## まとめ

### やるべきこと（人手作業）

1. ✅ Microsoft PowerPointを開く
2. ✅ 4種類のSmartArtレイアウトを作成（Process, Hierarchy, Cycle, Relationship）
3. ✅ `tests/fixtures/smartart_test_template.pptx`として保存
4. ✅ テストを実行して検証

### やらなくて良いこと

- ❌ 既存コードの変更
- ❌ 新しいテストの作成
- ❌ ビルドスクリプトの修正
- ❌ 依存関係の追加

### 期待される結果

```bash
$ uv run pytest tests/integration/test_smartart_real_templates.py -v

tests/integration/test_smartart_real_templates.py::test_smartart_with_real_template_process_flow PASSED
tests/integration/test_smartart_real_templates.py::test_smartart_all_types_in_real_template PASSED
tests/integration/test_smartart_real_templates.py::test_smartart_end_to_end_workflow PASSED

====== 3 passed in 2.45s ======
```
