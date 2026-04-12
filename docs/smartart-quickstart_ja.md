[English](smartart-quickstart.md) | [日本語](smartart-quickstart_ja.md)

# SmartArt テンプレート作成クイックスタート

## 目次

1. [概要](#概要)
2. [目的の違い](#目的の違い)
3. [現在の状況](#現在の状況)
4. [必要な作業（PowerPointで手動）](#必要な作業powerPointで手動)
5. [検証手順](#検証手順)
6. [トラブルシューティング](#トラブルシューティング)
7. [まとめ](#まとめ)

## 概要

**このガイドは「テストを通すこと」に特化しています。**

統合テストを通すためのSmartArtテンプレートを**10-15分で作成**する方法を説明します。本番用の完全なテンプレート作成については、[smartart-manual-setup_ja.md](smartart-manual-setup_ja.md)を参照してください。

## 目的の違い

| 目的                       | 方法                                      | 対象                | ガイド                                                     |
| -------------------------- | ----------------------------------------- | ------------------- | ---------------------------------------------------------- |
| **統合テストを通す**       | 通常のスライドにSmartArt挿入              | `prs.slides`        | 👉 このドキュメント                                        |
| **本番用テンプレート作成** | スライドマスター/レイアウトにSmartArt配置 | `prs.slide_layouts` | [smartart-manual-setup_ja.md](smartart-manual-setup_ja.md) |

### なぜ違うのか？

- **テスト**: [test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py)は`prs.slides`をイテレート → 通常のスライドが必要
- **本番**: [TemplateParser](../src/pptx_agent/template_parser/parser.py)は`prs.slide_layouts`を解析 → スライドレイアウトが必要

## 現在の状況

✅ ファイル名を修正済み: `tests/fixtures/smartart_test_template.pptx`
❌ このファイルには**本物のSmartArt図形がまだ含まれていません**

検証結果:

```
Slide 1-4: Rectangle, TextBox のみ（SmartArtではない）
❌ No SmartArt shapes found (only placeholder shapes)
```

## 必要な作業（PowerPointで手動）

### Option A: 既存ファイルを編集（推奨）

1. **PowerPointで開く**
   ```bash
   open tests/fixtures/smartart_test_template.pptx
   ```
2. **各スライドで以下を実行**（4スライド分）:

   **Slide 1 - Process Flow:**
   - Rectangle 3（プレースホルダー）を削除
   - 「挿入」→「SmartArt」→「プロセス」→「基本プロセス」を選択
   - ノード数を**3個**に設定
   - テキスト: "Node 1", "Node 2", "Node 3"

   **Slide 2 - Hierarchy:**
   - Rectangle 3を削除
   - 「挿入」→「SmartArt」→「階層構造」→「組織図」を選択
   - ノード数を**3個**に設定（トップ1個、子2個）
   - テキスト: "CEO", "VP Sales", "VP Engineering"

   **Slide 3 - Cycle:**
   - Rectangle 3を削除
   - 「挿入」→「SmartArt」→「循環」→「基本的な循環」を選択
   - ノード数を**4個**に設定
   - テキスト: "Plan", "Do", "Check", "Act"

   **Slide 4 - Relationship:**
   - Rectangle 3を削除
   - 「挿入」→「SmartArt」→「関係」→「基本ベン」を選択
   - ノード数を**3個**に設定
   - テキスト: "Group 1", "Group 2", "Group 3"

3. **保存**
   - Ctrl+S / Cmd+Sで上書き保存

### Option B: 新規作成（詳細ガイド使用）

詳細な手順は [smartart-manual-setup_ja.md](smartart-manual-setup_ja.md) を参照

## 検証手順

### 1. SmartArt含有を確認

```bash
uv run python -c "
from pptx import Presentation
from pathlib import Path

template_path = 'tests/fixtures/smartart_test_template.pptx'
prs = Presentation(template_path)
smartart_count = 0

for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if hasattr(shape, '_element'):
            if 'graphicFrame' in str(shape._element.tag):
                smartart_count += 1
                print(f'✓ Slide {i+1}: Found SmartArt - {shape.name}')

if smartart_count > 0:
    print(f'\n✓ SUCCESS: Template has {smartart_count} SmartArt shapes')
    print('テストを実行できます: uv run pytest tests/integration/test_smartart_real_templates.py -v')
else:
    print('\n❌ FAILED: No SmartArt shapes found')
    print('PowerPointで手動編集が必要です')
"
```

**期待される出力:**

```
✓ Slide 1: Found SmartArt - Content Placeholder 2
✓ Slide 2: Found SmartArt - Content Placeholder 2
✓ Slide 3: Found SmartArt - Content Placeholder 2
✓ Slide 4: Found SmartArt - Content Placeholder 2

✓ SUCCESS: Template has 4 SmartArt shapes
```

### 2. テストを実行

```bash
uv run pytest tests/integration/test_smartart_real_templates.py -v
```

**期待される結果:**

```
test_smartart_with_real_template_process_flow PASSED
test_smartart_all_types_in_real_template PASSED
test_smartart_end_to_end_workflow PASSED
```

## トラブルシューティング

### Q: PowerPointが使えない

**A:** LibreOffice ImpressではSmartArt作成機能が限定的です。以下の選択肢があります:

1. **Microsoft 365を試用**（1ヶ月無料トライアルあり）
2. **他のPCで作成**してファイルをコピー
3. **商用ライブラリ使用**（Aspose.Slides等）を検討
4. **テストをスキップ**したまま運用（既存の単体テストでSmartArtロジックは検証済み）

### Q: ノード数が合わない

**A:** SmartArtのノード数を以下に合わせてください:

- Process: 3ノード
- Hierarchy: 3ノード（トップ1、子2）
- Cycle: 4ノード
- Relationship: 3ノード

### Q: 既存のプレースホルダーを削除できない

**A:** スライドマスタービューではなく、通常のスライドビューで編集してください。

## まとめ

### 現在の状態

- ✅ テストコード完成
- ✅ SmartArt処理ロジック完成
- ✅ ファイル配置・命名完了
- ❌ **PowerPointでのSmartArt挿入待ち**

### 次のステップ

1. PowerPointで `tests/fixtures/smartart_test_template.pptx` を開く
2. 4スライドにSmartArtを挿入（上記手順参照）
3. 保存
4. 検証スクリプトを実行
5. テストを実行

**所要時間**: 約10-15分
