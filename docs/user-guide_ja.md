[English](user-guide.md) | [日本語](user-guide_ja.md)

# AI PowerPoint Presentation Generator - ユーザーガイド

## 目次

1. [はじめに](#はじめに)
2. [はじめの一歩](#はじめの一歩)
3. [インストール](#インストール)
4. [構成](#構成)
5. [基本的な使い方](#基本的な使い方)
6. [高度な機能](#高度な機能)
7. [テンプレートの要件](#テンプレートの要件)
8. [トラブルシューティング](#トラブルシューティング)
9. [FAQ](#faq)
10. [ベストプラクティス](#ベストプラクティス)

## はじめに

AI PowerPoint Presentation Generatorは、大規模言語モデル（LLM）を使用して、テキストまたはMarkdownドキュメントからプロフェッショナルなPowerPointプレゼンテーションを自動的に生成するコマンドラインツールです。このツールは、コンテンツを分析し、構造化されたアウトラインを生成し、詳細なスライドコンテンツを作成し、テンプレートを使用して完全なプレゼンテーションを組み立てます。

### 主な機能

- **自動コンテンツ分析**: 入力からトピック、キーメッセージ、構造を抽出します
- **インテリジェントなスライド生成**: 適切なレイアウトで3〜30枚のスライドを作成します
- **多言語サポート**: 日本語と英語を完全にサポート
- **スマートテキストフィッティング**: プレースホルダーに合わせてコンテンツを自動的に調整します
- **ビジュアルアセット**: グラフ、表、SmartArtの図を生成します
- **テンプレートベースのデザイン**: 一貫したブランディングのためにPowerPointテンプレートを使用します
- **本番環境対応**: 堅牢なエラー処理、再試行ロジック、およびプロバイダーのフォールバック

### システム要件

- **オペレーティングシステム**: macOS、Linux、またはWindows（WSL）
- **Python**: バージョン3.12以上
- **パッケージマネージャー**: [uv](https://github.com/astral-sh/uv) (最新バージョン)
- **タスクランナー**: [mise](https://mise.jdx.dev/) (任意ですが推奨)
- **LLMアクセス**: OpenAI、Anthropic Claude、またはIBM watsonx.aiへのAPIアクセス

## はじめの一歩

### クイックスタート（5分）

1. クローンしてインストール:

   ```bash
   git clone <repository-url>
   cd pptx-agent
   uv sync --all-extras
   ```

2. 構成（`.env`ファイルを作成）:

   ```bash
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-5-sonnet-20241022
   ANTHROPIC_API_KEY=your-api-key-here
   ```

3. 最初のプレゼンテーションを生成:
   ```bash
   uv run python -m pptx_agent.main \
     --input examples/01-business-quarterly-review.txt \
     --template templates/basic-template.pptx \
     --output my-presentation.pptx
   ```

## インストール

### 前提条件

#### 1. Python 3.12+ のインストール

**macOS（Homebrewを使用）**:

```bash
brew install python@3.12
```

**Linux（Ubuntu/Debian）**:

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

**Windows（WSL）**:
WSLをセットアップした後、Linuxの手順に従ってください。

#### 2. uvパッケージマネージャーのインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

またはpipで:

```bash
pip install uv
```

#### 3. miseのインストール（任意ですが推奨）

```bash
curl https://mise.run | sh
```

### ツールのインストール

1. **リポジトリのクローン**:

   ```bash
   git clone <repository-url>
   cd pptx-agent
   ```

2. **依存関係のインストール**:

   ```bash
   uv sync --all-extras
   ```

   これにより以下がインストールされます:
   - コアの依存関係（pydantic-ai、python-pptx、litellm）
   - 開発ツール（ruff、pyright、pytest）
   - オプションの追加機能（LLMトレース用のlogfire）

3. **インストールの確認**:

   ```bash
   uv run python -m pptx_agent.main --help
   ```

   利用可能なオプションを含むヘルプメッセージが表示されるはずです。

## 構成

### 環境変数

プロジェクトのルートディレクトリに `.env` ファイルを作成します:

```bash
touch .env
```

### プロバイダーの構成

#### オプション1: Anthropic Claude（本番環境に推奨）

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-api03-...
ENVIRONMENT=production
```

**APIキーの取得**: [https://console.anthropic.com/](https://console.anthropic.com/)

#### オプション2: OpenAI（ローカルエンドポイントまたはAPI経由）

**ローカル開発用（Ollama）**:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_BASE=http://localhost:11434/v1
ENVIRONMENT=development
```

**OpenAI API用**:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
```

#### オプション3: IBM watsonx.ai

```env
LLM_PROVIDER=watsonx
LLM_MODEL=ibm/granite-13b-chat-v2
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_APIKEY=your-watsonx-api-key
WATSONX_PROJECT_ID=your-project-id
ENVIRONMENT=production
```

### 環境設定

#### 開発モード（高速、耐障害性低）

```env
ENVIRONMENT=development
MAX_RETRIES=1
REQUEST_TIMEOUT=60
```

- 開発中のフィードバックが速い
- 早めに失敗するための最小限の再試行
- 短いタイムアウト

#### 本番モード（堅牢、高可用性）

```env
ENVIRONMENT=production
MAX_RETRIES=5
REQUEST_TIMEOUT=120
```

- 指数バックオフによる自動再試行
- プロバイダーフォールバック（watsonx → Claude）
- 包括的なエラーログ

### オプション: プロバイダーのフォールバック

本番環境の耐障害性のためにフォールバックプロセスを構成します:

```env
ENABLE_FALLBACK=true
FALLBACK_PROVIDER=anthropic
FALLBACK_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-api03-...
```

プライマリプロバイダーが失敗した場合、システムは自動的にフォールバックに切り替わります。

## 基本的な使い方

### コマンド構造

```bash
uv run python -m pptx_agent.main \
  --input <input-file> \
  --template <template-file> \
  --output <output-file> \
  [--language <en|ja>] \
  [--manifest <manifest-file>] \
  [--verbose]
```

### 必須の引数

- `--input` または `-i`: 入力テキスト/Markdownファイルのパス
- `--template` または `-t`: PowerPointテンプレート（.pptx）のパス
- `--output` または `-o`: 生成されるプレゼンテーション（.pptx）のパス

### オプションの引数

- `--language` または `-l`: 出力言語（英語は `en`、日本語は `ja`）
- `--manifest` または `-m`: テンプレートマニフェストJSONファイルのパス
- `--verbose`: 詳細なエラートレースを伴う詳細モードを有効にします

### 例1: 基本的な生成

```bash
uv run python -m pptx_agent.main \
  --input my-content.txt \
  --template templates/basic-template.pptx \
  --output presentation.pptx
```

### 例2: 日本語のプレゼンテーション

```bash
uv run python -m pptx_agent.main \
  --input content-ja.txt \
  --template templates/japanese-template.pptx \
  --output presentation-ja.pptx \
  --language ja
```

### 例3: テンプレートマニフェストの使用

```bash
uv run python -m pptx_agent.main \
  --input business-proposal.md \
  --template templates/corporate-template.pptx \
  --manifest templates/corporate-manifest.json \
  --output proposal.pptx
```

### 例4: デバッグ用の詳細モード

```bash
uv run python -m pptx_agent.main \
  --input my-content.txt \
  --template templates/basic-template.pptx \
  --output presentation.pptx \
  --verbose
```

## 高度な機能

### 多言語サポート

システムは自動的に入力言語を検出し、それに応じてスライドを生成します:

- **英語**: 全角テキストの容量計算を使用します
- **日本語**: 全角文字に対して0.55倍の容量乗算器を適用します
- **混在コンテンツ**: 日本語のテキスト内で英語の技術用語を保持します

**出力言語を強制する**:

```bash
# 入力は英語ですが、日本語のスライドを生成します
uv run python -m pptx_agent.main \
  --input input-en.txt \
  --template templates/template.pptx \
  --output presentation-ja.pptx \
  --language ja
```

### グラフと表

システムは入力内の数値や表形式のデータを見つけ、それらを視覚的要素に変換します。

**グラフの入力例**:

```markdown
## 販売実績

四半期の販売データは以下の通りです:

- Q1: $1.2M
- Q2: $1.5M
- Q3: $1.8M
- Q4: $2.1M
```

システムはこのデータで棒グラフを生成します。

**表の入力例**:

```markdown
## 製品比較

| 機能 | Basic | Pro | Enterprise |
| --- | --- | --- | --- |
| ユーザー | 10 | 100 | 無制限 |
| ストレージ | 10GB | 100GB | 1TB |
| 価格 | $10/月 | $50/月 | カスタム |
```

システムはフォーマットされた表を生成します。

### SmartArt の図

テンプレートにSmartArtのレイアウトが含まれている場合、システムはそれらを入力できます:

**プロセスフローの入力**:

```markdown
## 実装プロセス

1. 要件定義
2. 設計と計画
3. 開発
4. テストとQA
5. デプロイ
```

システムはこの手順でプロセスのSmartArtを入力します。

### テキストのオーバーフローの解決

システムは、収まりきらないテキストを自動的に処理します:

1. **フォントの縮小**: フォントサイズを10〜20％縮小します
2. **レイアウトの変更**: より大きなプレースホルダーのあるレイアウトに切り替えます
3. **コンテンツの分割**: コンテンツを複数のスライドに分割します
4. **要約**: コンテンツを要約するようLLMに要求します

ユーザーは何もする必要はありません。システムがこれを自動的に処理します。

## テンプレートの要件

### 最低要件

PowerPointテンプレートには以下を含める必要があります:

1. **タイトル スライド** (Title Slide): 最初と最後のスライド用
2. **タイトルおよびコンテンツ** (Title and Content): メインのコンテンツスライド用
3. **セクション見出し** (Section Header)（任意）: セクションの切り替え用

### レイアウトの命名規則

システムは以下の名前のレイアウトを探します:

- "Title Slide" (タイトル スライド)
- "Title and Content" (タイトルおよびコンテンツ)
- "Section Header" (セクション見出し)
- "Two Content" (2つのコンテンツ)
- "Title Only" (タイトルのみ)
- "Blank" (白紙)

### プレースホルダーの要件

各レイアウトには明確な名前のプレースホルダーが必要です:

- **タイトル**: "Title" または "Title 1"
- **コンテンツ**: "Content", "Text Placeholder", または "Body"
- **チャート**: "Chart Placeholder" または "Content"
- **表**: "Table Placeholder" または "Content"

### 互換性のあるテンプレートの作成

1. **Microsoft PowerPoint または LibreOffice Impress で開始**
2. **スライド マスターを作成** してブランディングを定義
3. **レイアウトを追加** し、適切なプレースホルダーを配置
4. **標準の規則を用いてレイアウトに名前を付ける**
5. **ツールでテスト** して互換性を確認

### テンプレートマニフェスト（任意）

生成を最適化するためにマニフェストを生成します:

```bash
uv run python -m pptx_agent.template_parser.parser \
  --template templates/my-template.pptx \
  --output templates/my-template-manifest.json
```

マニフェストには以下が含まれます:

- 利用可能なレイアウトとプレースホルダー
- テキストの容量計算
- SmartArtの構成
- 色とフォントのテーマ

## トラブルシューティング

### よくある問題

#### 問題: "Template file not found"（テンプレートファイルが見つかりません）

**原因**: テンプレートのパスが間違っているか、ファイルが存在しません。

**解決策**:

```bash
# 絶対パスを使用する
--template /full/path/to/template.pptx

# またはカレントディレクトリからの相対パス
--template ./templates/template.pptx
```

#### 問題: "Input validation failed: text too short"（入力検証に失敗しました: テキストが短すぎます）

**原因**: 入力ファイルが空であるか、10文字未満です。

**解決策**:

- 入力ファイルに十分なコンテンツがあることを確認してください（100文字以上を推奨）
- ファイルのエンコーディングを確認してください（UTF-8である必要があります）

#### 問題: "Required configuration for anthropic provider is incomplete"（Anthropicプロバイダーの必須構成が不完全です）

**原因**: 環境変数にAPIキーがありません。

**解決策**:

```bash
# .envファイルに追加
ANTHROPIC_API_KEY=your-actual-api-key-here
```

#### 問題: "Layout 'Title and Content' not found in template"（'タイトルおよびコンテンツ' レイアウトが見つかりません）

**原因**: テンプレートに必要なレイアウトがありません。

**解決策**:

- `templates/` ディレクトリから互換性のあるテンプレートを使用します
- または、PowerPointで不足しているレイアウトをテンプレートに追加します

#### 問題: 解決後もテキストがはみ出す（オーバーフロー）

**原因**: コンテンツが極端に長いか、テンプレートのプレースホルダーが非常に小さい。

**解決策**:

- 入力コンテンツを簡素化する
- プレースホルダーの大きいテンプレートを使用する
- マニフェストで要約を有効にする

### エラーメッセージ

#### "Validation Error: slide count exceeds maximum"

**意味**: 生成されたアウトラインのスライドが30枚を超えています。

**解決策**: 入力内容を減らすか、複数のプレゼンテーションに分割します。

#### "Provider error: rate limit exceeded"

**意味**: LLMプロバイダーへのAPIリクエストが多すぎます。

**解決策**:

- 待ってから再試行
- 再試行バックオフのある本番モードを使用
- APIのレート制限を確認

#### "Timeout error: outline generation exceeded 120s"

**意味**: LLMからの応答に時間がかかりすぎています。

**解決策**:

- 再試行（通常は2回目で成功します）
- LLMプロバイダーステータスの確認
- 入力の複雑さを軽減

### ヘルプを得るには

1. **ログの確認**: 詳細なエラー情報を見るには `--verbose` フラグを使用して実行します
2. **構成の確認**: `.env` ファイルに正しいAPIキーがあることを確認します
3. **テンプレートのテスト**: 最初に提供されたサンプルテンプレートで試してください
4. **APIステータスの確認**: LLMプロバイダーが動作していることを確認します

## FAQ

### Q: どのような入力形式がサポートされていますか？

**A**: プレーンテキスト（.txt）とMarkdown（.md）ファイルです。システムは英語と日本語のテキストの両方をサポートしています。

### Q: 入力テキストの長さはどれくらいにすべきですか？

**A**: 最適な結果を得るには100文字から30,000文字の間です。それより長いテキストは拒否されるか分割される場合があります。

### Q: 何枚のスライドが生成されますか？

**A**: コンテンツの複雑さに応じて3枚から30枚の間です。20枚を超えるスライドが生成されると警告が出ます。

### Q: 自分の会社のPowerPointテンプレートを使用できますか？

**A**: はい！標準のレイアウト命名規則に従っていれば可能です。[テンプレートの要件](#テンプレートの要件)を参照してください。

### Q: オフラインで動作しますか？

**A**: いいえ。LLM APIを呼び出すにはインターネットアクセスが必要です。ただし、オフラインで実行するためにローカルのLLMサーバー（Ollamaなど）を利用することは可能です。

### Q: 生成されたコンテンツの精度はどれくらいですか？

**A**: システムは入力テキストに基づいてコンテンツを生成します。品質は以下に依存します:

- 入力テキストの明確さと構造
- LLMモデルの品質（GPT-4およびClaude 3.5 Sonnetを推奨）
- テンプレート設計とプレースホルダーのサイズ

### Q: 生成されたプレゼンテーションは編集できますか？

**A**: はい！出力はMicrosoft PowerPoint、LibreOffice Impress、またはGoogle スライドで編集できる標準のPowerPointファイルです。

### Q: スピーカーノートについてはどうですか？

**A**: 各スライドごとにスピーカーノートが自動生成され、発表者を支援するためにスライドの内容の要約が生成されます。

## ベストプラクティス

1. **入力の構造化**: 明確な見出し、箇条書き、明確なセクションを使用して入力ドキュメントを構成します。
2. **テンプレートの検証**: テンプレート解析スクリプトにテンプレートを1回実行させ、レイアウトが正しく検出されるか確認します。
3. **抽出された統計の確認**: `--verbose` モードで実行し、最終的なPPTXをチェックする前にエージェントが何を抽出したかを確認します。
4. **反復的な改善**: 大幅なオーバーフロー縮小を避けるために、スライドのレイアウトを正しく判別できるように十分なコンテンツ文脈をLLMに提供します。
