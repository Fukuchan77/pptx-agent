[English](README.md) | [日本語](README_ja.md)

# AI PowerPoint Presentation Generator

テキストやMarkdownの入力から、大規模言語モデル (LLM) を使用してプロフェッショナルなPowerPointプレゼンテーションを生成するAI搭載ツールです。

## 📚 ドキュメント

- **[ユーザーガイド](docs/user-guide_ja.md)** - 完全なインストール、構成、および使用手順
- **[開発者ガイド](docs/developer-guide.md)** - アーキテクチャ、開発ワークフロー、および貢献ガイドライン
- **[API リファレンス](docs/api-reference.md)** - 技術的なAPIドキュメント
- **[アーキテクチャ決定記録 (ADR)](docs/adr/)** - 重要なアーキテクチャ決定と技術的選択の記録
- **[デプロイメントガイド](docs/deployment.md)** - 本番環境のデプロイ手順 _(近日公開)_

## ✨ 機能

- **自動プレゼンテーション生成**: テキスト/Markdownドキュメントを構造化されたPowerPointプレゼンテーションに変換します
- **多言語サポート**: 日本語と英語をサポートし、言語を考慮したテキスト容量計算を行います
- **インテリジェントなレイアウト選択**: コンテンツに基づいて適切なスライドレイアウトを自動的に選択します
- **スマートコンテンツフィッティング**: フォントの縮小、レイアウトの切り替え、またはコンテンツの要約により、テキストのオーバーフローを解決します
- **ビジュアルアセットのサポート**: グラフ、表を生成し、SmartArtの図にコンテンツを入力します
- **テンプレートベース**: 一貫したブランディングのために、カスタマイズ可能なPowerPointテンプレートを使用します
- **本番環境対応**: 組み込みの再試行戦略、プロバイダーのフォールバック、および包括的なエラー処理

## 要件

- Python 3.12 以上
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー
- [mise](https://mise.jdx.dev/) タスクランナー

## インストール

1. リポジトリをクローンします:

```bash
git clone <repository-url>
cd pptx-agent
```

2. uvを使用して依存関係をインストールします:

```bash
uv sync --all-extras
```

3. 環境変数を設定します:

```bash
cp .env.template .env
# .envを編集してAPIキーと構成を設定します
```

## 構成

### 環境変数

このツールは複数のLLMプロバイダーをサポートしています。好みのプロバイダーを `.env` で設定してください:

**OpenAI (ローカルエンドポイントまたはAPI経由):**

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
# OpenAI API用:
OPENAI_API_KEY=your-api-key
# またはローカルエンドポイント用 (例: Ollama):
# LLM_API_BASE=http://localhost:11434/v1
```

**本番環境 (IBM watsonx.ai):**

```bash
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_APIKEY=your-api-key
WATSONX_PROJECT_ID=your-project-id
```

**本番環境フォールバック (Anthropic Claude):**

```bash
ANTHROPIC_API_KEY=your-api-key
```

## 🚀 クイックスタート

3つのステップで最初のプレゼンテーションを生成します:

```bash
# 1. インストール
uv sync --all-extras

# 2. 構成 (APIキーを.envに追加)
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# 3. 生成
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output my-presentation.pptx
```

## 📖 使用例

### 基本的なプレゼンテーション生成

```bash
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output output.pptx
```

### 日本語のプレゼンテーション

```bash
uv run python -m pptx_agent.main \
  --input examples/03-python-programming-basics-ja.txt \
  --template templates/japanese-template.pptx \
  --output presentation-ja.pptx \
  --language ja
```

### テンプレートマニフェストを使用 (最適化)

```bash
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output proposal.pptx \
  --manifest basic-manifest.json
```

### 詳細モード (デバッグ用)

```bash
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output output.pptx \
  --verbose
```

その他の例と詳細な使用手順については、**[ユーザーガイド](docs/user-guide_ja.md)**を参照してください。

## 開発

### miseタスクの使用

プロジェクトはタスク管理にmiseを使用しています。利用可能なタスク:

```bash
# テストの実行
mise run test

# カバレッジレポート付きでテストを実行
mise run test-cov

# リンターチェックの実行
mise run lint

# リンターの問題を自動修正
mise run lint-fix

# コードのフォーマット
mise run format

# 型チェッカーの実行
mise run typecheck

# すべてのCIチェック（lint, typecheck, test）の実行
mise run ci
```

### 開発ワークフロー

1. **テストファースト (TDD)**:
   - 失敗するテストを書く
   - パスするための最小限のコードを実装する
   - テストを成功させたままリファクタリングする

2. **コードスタイルの遵守**:
   - Google Python Style Guide
   - lintingとフォーマットにはruffを使用
   - 型チェックにはpyrightを使用

3. **テストカバレッジの維持**:
   - コアモジュールで最低80%のカバレッジ
   - カバレッジを確認するには `mise run test-cov` を実行

4. **コミット標準**:
   - コミットする前に `mise run ci` を実行
   - 明確で説明的なコミットメッセージを書く

### プロジェクト構造

```
pptx-agent/
├── src/
│   └── pptx_agent/           # メインパッケージ
│       ├── agents/           # LLMエージェント (ストーリーアナライザー、アウトラインジェネレーターなど)
│       ├── pptx_wrapper/     # PowerPoint操作レイヤー
│       ├── template_parser/  # テンプレート解析とマニフェスト生成
│       ├── validators/       # 入力とコンテンツの検証
│       ├── schemas/          # Pydanticモデル
│       └── utils/            # ユーティリティ関数
├── tests/
│   ├── unit/                 # 単体テスト
│   ├── integration/          # 統合テスト
│   └── fixtures/             # テストデータとテンプレート
├── templates/                # PowerPointテンプレート
└── docs/                     # ドキュメント
```

## アーキテクチャ

システムはパイプライン・アーキテクチャに従っています:

1. **ストーリーアナライザー**: 入力テキストを分析して要約します
2. **アウトラインジェネレーター**: スライドタイプを含むプレゼンテーションの構造を作成します
3. **コンテンツジェネレーター**: 各スライドの詳細なコンテンツを生成します
4. **バリデーター**: テンプレートの制約に対してアウトラインとコンテンツを検証します
5. **スライドビルダー**: PowerPointのスライドにコンテンツを入力します
6. **オーバーフローリゾルバー**: 段階的な戦略を通じてテキストのオーバーフローを処理します

### LLMの統合

- 型安全なLLMインタラクションのために [Pydantic AI](https://ai.pydantic.dev/) を使用
- Pydanticモデルによる構造化された出力検証
- 指数バックオフによる自動再試行
- プロバイダーフォールバック (watsonx.ai → Claude)
- Logfireによる包括的なロギング

## テスト

### テストの実行

```bash
# 全テストの実行
mise run test

# 単体テストのみ実行
uv run pytest tests/unit/ -x

# 統合テストの実行（API鍵が必要）
uv run pytest tests/integration/ -x

# カバレッジレポート付きで実行
mise run test-cov
```

### テスト設定

**単体テスト**: 環境変数から自動的に隔離されます。[`make_test_config()`](tests/conftest.py:103)フィクスチャを使用してください:

```python
def test_something(make_test_config):
    config = make_test_config(llm_provider="openai")
    # テストロジック
```

**統合テスト**: 実際のAPI鍵が必要です。テスト環境をセットアップしてください:

1. テンプレートをコピー: `cp .env.test.template .env.test`
2. テスト用API鍵を記入
3. 統合テストを実行: `uv run pytest tests/integration/ -x`

**注意**: `.env.test`はgitignoreされており、コミットしてはいけません。

詳細については、[開発者ガイド](docs/developer-guide.md#testing-configuration)を参照してください。

## 🤝 貢献

貢献を歓迎します！詳細は以下をご覧ください：

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - 貢献ガイドライン
- **[開発者ガイド](docs/developer-guide.md)** - 開発セットアップとワークフロー
- **[API リファレンス](docs/api-reference.md)** - 技術文書

### 簡単な貢献ステップ

1. リポジトリをフォークする
2. フィーチャーブランチを作成する: `git checkout -b feature/amazing-feature`
3. TDDに従う: 最初にテストを書き、その後に実装する
4. CIチェックを実行する: `mise run ci`
5. Pull Requestを提出する

## ライセンス

[ライセンス情報を追加]

## 謝辞

- [python-pptx](https://python-pptx.readthedocs.io/) で構築されています
- [Pydantic AI](https://ai.pydantic.dev/) を介したLLM統合
- Pydantic AIのマルチプロバイダーサポート (OpenAI、Anthropicなど) を使用
