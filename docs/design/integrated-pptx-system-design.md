# 統合 AI PPTX 生成システム 仕様・設計書

> 対象: `pptx-agent` と `powerpoint-maker` の統合による、調査エージェント連携型 PowerPoint 自動生成プラットフォーム
> ステータス: Draft v1.0
> 関連 ADR: [0001 テンプレート生成方針](../adr/0001-template-generation-plan-b.md) / [0003 QAアーキテクチャ](../adr/0003-qa-architecture.md) / [0004 テンプレートキャッシュ](../adr/0004-template-caching.md)

---

## 0. エグゼクティブサマリ（結論先出し）

| 論点 | 結論 |
|------|------|
| **どちらをベースにするか** | **分割採用**を推奨。**バックエンド = `pptx-agent`**、**フロントエンド = `powerpoint-maker` (frontend/)** |
| **生成エンジンの構成** | 既存 `pptx-agent` の XML 操作系を **ルートB** として温存しつつ、**ルートA（DOM/ヘッドレスレンダラー）を新設**するデュアルルート方式 |
| **エンジン切替の責務** | 新設する **Bridge Server**（ローカルブリッジ）が、スライド単位でルートA/Bを選択し、調査エージェントとの I/O を仲介 |
| **テンプレート置換の中核** | python-pptx ネイティブの `Chart.replace_data()` ＋ `templatepptx` 系の magic-word 置換を採用。ブランド一貫性を最優先 |

**理由の要約**: `pptx-agent` は QA/自動修正エンジン・SHA-256 テンプレートキャッシュ・厳格な型/バリデーション・CLI/API/MCP の多インターフェース・ADR 文化を備え、**「下流コンパイルエンジン」としての堅牢性**が圧倒的に高い。一方 `powerpoint-maker` は React 19 の **完成された対話的 UI とプレビュー/編集動線**を持ち、**「ユーザー接点」**として優れる。両者は FastAPI バックエンド同士で疎結合に分離できるため、それぞれの強みを活かす分割採用が最も合理的である。

---

## 1. ベース選定の評価と意思決定

### 1.1 評価マトリクス

| 評価軸 | pptx-agent | powerpoint-maker | 採用層 |
|--------|:----------:|:----------------:|--------|
| 生成エンジンの堅牢性（QA/自動修正） | ◎ (`qa/` + `fixer/`) | △（検出のみ） | **BE: agent** |
| テンプレート解析・キャッシュ | ◎ (SHA-256 永続) | ○（LRU/プロセス内） | **BE: agent** |
| バリデーション/セキュリティ | ◎ (1,524 LOC) | ○ | **BE: agent** |
| 型安全（pyright strict） | ◎ | △（BEは実行時のみ） | **BE: agent** |
| チャート/テーブル/SmartArt 生成 | ◎ (`pptx_wrapper/`) | △ | **BE: agent** |
| 多インターフェース（CLI/API/MCP） | ◎ | △（API/UIのみ） | **BE: agent** |
| Web UI（プレビュー/編集） | ✗ | ◎ (React 19) | **FE: maker** |
| Web 検索リサーチ生成 | ✗ | ◎ (DuckDuckGo) | 上流エージェント層へ昇格 |
| 既存 PPTX 抽出・再利用 | ✗ | ○ (`docling`) | FE/Bridge へ移植 |
| マルチブラウザ E2E | ✗ | ◎ (Playwright×3) | **FE: maker** |
| レイアウト抽象化思想 | ○（容量検証） | ◎ (`layout_intelligence`) | 設計思想を BE に統合 |

### 1.2 意思決定

```
推奨アーキテクチャ:
  バックエンド・コア   = pptx-agent          （生成・QA・キャッシュ・バリデーション）
  フロントエンド       = powerpoint-maker/frontend （UI・プレビュー・編集）
  リサーチ機能         = powerpoint-maker の research を「調査エージェント層」へ昇格
  レイアウト抽象化     = powerpoint-maker の layout_intelligence 思想を BE のスキーマに統合
```

**却下した代替案**:
- *powerpoint-maker 単独ベース*: 生成エンジンとして QA/自動修正・永続キャッシュ・型厳格性を欠き、要件（自動分割・フォールバック・SmartArt 部分置換）を満たすには大規模な作り込みが必要。
- *pptx-agent 単独ベース*: UI がゼロからの開発になり、`powerpoint-maker` の完成済み React 資産（プレビュー/編集/E2E）を捨てることになる。

---

## 2. システム全体アーキテクチャ

### 2.1 4層構成

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 調査・構成エージェント層 (Research & Composition Agents)                   │
│    入力: PDF / Excel / 競合URL / 生テキスト                                   │
│    処理: ドキュメント解析(docling) → セマンティック解析 → 構成案構築          │
│    出力: ソース文書 + 設計定義マニフェスト (Markdown / JSON)                  │
│    基盤: powerpoint-maker/research(DuckDuckGo) + pptx-agent/story_analyzer    │
└─────────────────────────────────────────────────────────────────────────────┘
                         │  (Composition Manifest + Source Docs)
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. ローカルブリッジ (Bridge Server)  ★新設                                    │
│    - ローカルファイル監視 / 中間成果物ステージング                            │
│    - APIキー・環境変数の安全な集中管理 (pydantic-settings)                    │
│    - エージェントへの Skill 実行命令インターフェース                          │
│    - ★ルートA/B コンパイルエンジンのスライド単位切替 (Routing Policy)         │
└─────────────────────────────────────────────────────────────────────────────┘
                         │  (Render Plan: per-slide engine選択 + 配置定義)
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. PPTX 生成アプリ (下流コンパイルエンジン) = pptx-agent コア                 │
│                                                                               │
│  ┌─ ルートA: DOMベースレンダラー ★新設 ─┐  ┌─ ルートB: XMLマニピュレーター ─┐ │
│  │ - HTML/CSS(Flexbox/Grid)で版面定義   │  │ - テンプレート直接置換          │ │
│  │ - ヘッドレスブラウザで幾何確定        │  │   (templatepptx / slide_builder)│ │
│  │ - getBoundingClientRect → EMU 変換   │  │ - XMLツリー操作・複製           │ │
│  │ - python-pptx で図形を絶対配置        │  │ - replace_data() / SmartArt書換 │ │
│  └──────────────────────────────────────┘  └─────────────────────────────────┘ │
│                         ▼ 共通後段                                             │
│  QAエンジン (qa/) → 自動修正ループ (fixer/) → 最終 .pptx                       │
└─────────────────────────────────────────────────────────────────────────────┘
                         ▲
                         │  REST / SSE (job_id, status, preview, download)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. フロントエンド = powerpoint-maker/frontend (React 19 / Vite)               │
│    テンプレ投入 → 生成依頼 → プレビュー&編集 → ダウンロード                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 エンドツーエンドのデータフロー

1. **入力受領**: FE がソース（PDF/Excel/URL/テキスト）とテンプレート `.pptx` を Bridge にアップロード。
2. **調査・構成**: 調査エージェントが一次情報を解析し、`CompositionManifest`（後述 §5）を生成。
3. **テンプレート解析**: Bridge が `pptx-agent` の `template_parser` を呼び、SHA-256 キャッシュ付きで `TemplateManifest` を取得。
4. **Render Plan 生成**: Bridge の Routing Policy（§3.3.3）が、スライド毎に「ルートA / ルートB」を決定し `RenderPlan` を構築。
5. **コンパイル**: 生成エンジンが各スライドを該当ルートでレンダリング。
6. **QA → 自動修正**: `qa/` で検査、`fixer/` で反復修正（最大 N 回）。
7. **プレビュー**: 各スライドのサムネイル/構造を FE へ返却。ユーザーが編集 → 差分のみ再コンパイル。
8. **確定・ダウンロード**: 最終 `.pptx` を生成し `download/{job_id}` で配信。

---

## 3. レイヤー別 詳細設計

### 3.1 調査・構成エージェント層

| 項目 | 設計 |
|------|------|
| 入力ソース | PDF / Excel / 競合 URL / 生テキスト / Markdown |
| ドキュメント解析 | `docling`（powerpoint-maker から流用）でテキスト・表・画像を抽出 |
| Web リサーチ | `research.py`（DuckDuckGo / BeeAI）を**スタンドアロンの上流エージェント**へ昇格 |
| セマンティック解析 | `pptx-agent` の `story_analyzer`（トピック/聴衆/キーメッセージ/トーン/言語） |
| 出力 | `CompositionManifest`（JSON）＋正規化済みソース文書（Markdown） |
| 言語判定 | `utils/language_detector`（CJK/Latin 容量計算に直結） |

> **設計判断**: リサーチを「アプリ内機能」ではなく「上流の独立エージェント」に切り出すことで、Bridge から見れば *入力はすべて構造化マニフェスト* に統一でき、下流エンジンを入力ソースから疎結合化できる。

### 3.2 ローカルブリッジ（Bridge Server）★新設

`pptx-agent` の `interfaces/api.py`（FastAPI）を母体に拡張する。

| 責務 | 実装方針 |
|------|---------|
| ファイル監視・ステージング | `watchdog` でローカル入出力ディレクトリを監視、中間成果物を `job_id` 単位で隔離 |
| 環境変数/APIキー管理 | `pydantic-settings`（既存 `config.py`）で集中管理。鍵は FE に渡さず Bridge 内に閉じる |
| Skill 実行 IF | エージェント/MCP ツール（`analyze_template`, `generate_presentation`, `validate`, `run_autofix`）を REST + MCP で公開（`interfaces/mcp.py` を拡張） |
| **エンジン切替** | Routing Policy に基づき `RenderPlan` を構築（§3.3.3） |
| ジョブ管理 | 既存の非同期ジョブキュー（TTL 付き結果キャッシュ、TOCTOU 対策済み）を流用 |
| 進捗通知 | SSE / WebSocket で FE にステージ進捗・プレビューを push |

### 3.3 PPTX 生成エンジン（デュアルルート）

#### 3.3.1 ルートB: XML マニピュレーター（既存資産ベース・既定ルート）

ブランド一貫性とパフォーマンスを最優先する**既定ルート**。テンプレートのデザインを最大限保持する。

| 機能 | 実装 |
|------|------|
| プレースホルダ置換 | 既存 `pptx_wrapper/slide_builder.py` ＋ `templatepptx` の magic-word 置換 |
| 既存チャートのデータ置換 | python-pptx ネイティブ `Chart.replace_data(CategoryChartData)`（XML と埋め込み Excel ワークシートの両方を更新 → デザイン形状を維持したままデータのみ差替え） |
| 新規チャート追加 | `chart_builder.py`（bar/column/line/pie/scatter/area/doughnut/radar） |
| テーブル | `table_builder.py` |
| SmartArt 部分書換 | `smartart.py`（diagram data part の XML を直接操作しノードテキストを置換。テンプレートに既存 SmartArt 形状が必要） |
| 適用条件 | スライド内容がテンプレートのレイアウト/プレースホルダに**素直にマッピングできる**場合 |

#### 3.3.2 ルートA: DOM ベースレンダラー ★新設（自由版面ルート）

テンプレートのプレースホルダに収まらない**自由レイアウト**や、CSS 的な相対配置で「エージェント側の座標計算を抑えたい」場合に使用する。

```
[CSS版面定義(Flexbox/Grid)] 
        │  ← エージェントは "px/%/flex" のレイアウト思考のみ
        ▼
[ヘッドレスブラウザ(Playwright)で実レンダリング]
        │  各要素の getBoundingClientRect() で確定 px を取得
        ▼
[座標変換器: px → EMU]  (1 inch = 914400 EMU, 96px = 1 inch 基準)
        │
        ▼
[python-pptx で図形/テキストボックスを絶対配置(Inches/Pt/EMU)]
```

| 項目 | 設計 |
|------|------|
| 版面記述 | スライド = 1 HTML ページ。スライドサイズ（例 13.333"×7.5" = 1280×720px 相当）を viewport に設定 |
| レイアウトエンジン | ブラウザの Flexbox/Grid をそのまま利用し、エージェントは絶対座標を計算しない |
| 幾何確定 | Playwright（Chromium）で `getBoundingClientRect()` を全要素から収集 |
| 変換 | `EMU = px / 96 * 914400`。フォントは `Pt`、図形は `Emu` で python-pptx に渡す |
| 描画図表 | 動的ライブラリ（Chart.js / ECharts 等）で描画 → ①画像として貼付 or ②データ抽出してネイティブチャート化（§4.3） |
| 出力 | テキストはネイティブテキストボックス（編集可能性を保持）、装飾は図形。**画像化は最終手段** |

> **重要な設計指針**: ルートA は「ブラウザに版面計算を委譲」する方式であり、**幾何配置の正確性**と**CSS による表現力**を得る代わりに、ヘッドレスブラウザ依存・レンダリングコスト・テキスト編集性の制約を負う。よって既定はルートB、ルートAは*必要なスライドのみ*に限定する。

#### 3.3.3 Routing Policy（スライド単位のエンジン選択）

Bridge が `CompositionManifest` × `TemplateManifest` を突合し、各スライドに対し以下の優先順で判定する。

```
1. テンプレに対応レイアウトが存在し、容量内に収まる        → ルートB（ブランド維持・高速）
2. 既存チャート/SmartArt のデータ差替のみ                  → ルートB（replace_data / XML書換）
3. テンプレに無い自由レイアウト or 複雑なFlex/Grid配置     → ルートA（DOM計算）
4. ルートBで生成後 QA が ERROR を返し、自動修正で解消不能  → ルートA へフォールバック再試行
```

判定結果は `RenderPlan.slides[].engine ∈ {"xml", "dom"}` として記録され、監査可能にする。

### 3.4 フロントエンド（powerpoint-maker/frontend）

| 流用する既存資産 | 役割 |
|------------------|------|
| `TemplateUploader` | テンプレート/既存 PPTX のアップロード・解析 |
| `ContentInput`（タブ式） | Web検索 / Markdown / テキスト入力の切替 |
| `Preview` / `MarkdownPreview` | 生成結果のプレビューと**編集**、構文エラーの行/列表示 |
| `ErrorBoundary` | エラー UI |
| Playwright E2E（×3 ブラウザ） | 回帰テスト |

API 接続先を Bridge Server に向け、ジョブ進捗は SSE で受信。プレビューはスライド構造（JSON）＋サムネイルで表現する。

---

## 4. 機能要件 詳細設計

### 4.1 テンプレート

- 既存 `.pptx` を直接読込み、スライドマスター/レイアウト/プレースホルダを解析（`template_parser/parser.py`）。
- 解析結果 `TemplateManifest` は SHA-256 をキーに永続キャッシュ（`cache/`、解析コスト 80–90% 削減）。
- プレースホルダ毎の**文字容量**を言語別（CJK/Latin）に算出し、後段のオーバーフロー判定に供給。

### 4.2 レイアウト制御

| 方式 | 用途 | 実現 |
|------|------|------|
| 静的絶対配置（Inches/Pt/EMU） | テンプレート準拠スライド | ルートB。プレースホルダ座標を継承 |
| CSS 抽象（Flexbox/Grid イメージ） | 自由版面・複雑配置 | ルートA。ブラウザに計算委譲し px→EMU 変換 |

`powerpoint-maker` の **抽象レイアウト型（7種・容量上限付き）** の思想を `pptx-agent` のスキーマに取り込み、「抽象レイアウト → 実テンプレートレイアウト」のマッピング層を `LayoutTypeMapper` 相当として実装する。これにより**エージェントは具体座標ではなく抽象レイアウト型を選ぶ**だけでよくなる。

### 4.3 図表（チャート）

2 系統を併用する。

1. **ネイティブチャート（推奨）**: `CategoryChartData` ＋ `shapes.add_chart()` / `Chart.replace_data()`。PowerPoint 上で編集・再配色可能。**ブランド一貫性が最重要なケースの既定**。
2. **Web 動的描画の挿入**: Chart.js/ECharts 等でルートA上に描画。可能ならデータを抽出してネイティブ化、不可なら高解像度画像として貼付。

> **既存チャートのデータ置換**: テンプレートのデザイン済みチャート形状（`GraphicFrame` with chart）を検出し、背後の埋め込み Excel データシートのみを `replace_data()` で上書きする。これにより**配色・スタイル・凡例位置などのブランド資産を維持**したまま数値だけを動的更新できる。

### 4.4 SmartArt

- テンプレート内に**既存の SmartArt オブジェクト**を配置しておき、`diagram` data part の XML を経由してノードテキストのみを部分書換（`smartart.py`）。
- 動的な新規 SmartArt 生成や複雑階層は python-pptx の制約上未サポート → 「テンプレート前提のテキスト差替」に割り切る（[smartart-manual-setup](../smartart-manual-setup.md) 準拠）。
- 将来的に COM 経由（Windows + PowerPoint）での高度操作を**オプション**として検討（クロスプラットフォーム既定は XML 方式）。

### 4.5 templatepptx の活用／応用

- magic-word（`{{placeholder}}`）・テーブル・画像の一括置換に `templatepptx`（または `pptx-template`/`pptx-replace` 系）を採用し、ルートB の生産性を引上げる。
- `strict_mode` を有効化し、未解決プレースホルダが残る場合は**意味のあるエラーコードで失敗**させ、サイレントな欠落を防ぐ。
- 既存 `slide_builder.py` と役割が重複するため、**magic-word 置換は templatepptx、構造的配置・チャート・SmartArt は自前 wrapper** と責務分担する。

---

## 5. データモデル / マニフェスト仕様

### 5.1 CompositionManifest（調査エージェント → Bridge）

```jsonc
{
  "meta": { "topic": "string", "audience": "string", "language": "ja|en", "tone": "string" },
  "sources": [ { "type": "pdf|xlsx|url|text", "ref": "string", "extracted": "markdown" } ],
  "slides": [
    {
      "abstract_layout": 1,              // 抽象レイアウト型(1-7)
      "title": "string",
      "blocks": [
        { "kind": "bullets", "items": ["..."] },
        { "kind": "chart", "chart_type": "bar", "data": { "categories": [], "series": [] },
          "bind_to_template_chart": "Chart 3" },   // 既存チャートへの replace_data 指定(任意)
        { "kind": "table", "rows": [[...]] },
        { "kind": "smartart", "nodes": ["...", "..."], "target_shape": "Diagram 1" }
      ],
      "free_layout_css": null            // ルートA要求時のみ HTML/CSS を格納
    }
  ]
}
```

### 5.2 RenderPlan（Bridge → 生成エンジン）

```jsonc
{
  "template_sha256": "…",
  "slides": [
    { "index": 0, "engine": "xml", "template_layout": "Title and Content",
      "mapping": { "Title 1": "…", "Content Placeholder 2": ["…"] } },
    { "index": 1, "engine": "dom", "viewport": [1280, 720], "html": "<…>" }
  ]
}
```

---

## 6. 例外処理・エラーハンドリング設計

`pptx-agent` の既存 `overflow_resolver.py` ＋ `fixer/` を中核に、要件 3 項目を体系化する。

### 6.1 自動スケール・改行ハンドラー

| 入力過多度（容量比） | 戦略 | 実装 |
|---------------------|------|------|
| 0–20% 超過 | フォント縮小（最小サイズ下限あり） | `fixer/strategies/text_overflow.py` |
| 20–50% 超過 | レイアウト変更（別の抽象レイアウト型へ） | `LayoutTypeMapper` 再選択 |
| 50–100% 超過 | スライド分割（§6.2） | 分割ロジック |
| 100% 超過 | 要約 ＋ 強制トランケート | `overflow_resolver` + LLM 要約 |

改行は言語別（CJK は文字単位、Latin は単語境界）で wrap し、最小フォントサイズは QA ルールの `min_font_size` で担保。

### 6.2 スライド自動分割ロジック

- 1 スライドの容量超過が閾値（既定 50%）を超えた場合、ブロック境界（箇条書き項目・段落）で分割し「(続き)」スライドを生成。
- タイトルは継承、ページ番号/連番を付与。分割後に各スライドを再 QA。

### 6.3 フォント置換フォールバック

- テンプレート指定フォントが環境に存在しない場合、フォントマップ（例: メイリオ→Yu Gothic→sans-serif、Calibri→Arial）に従い段階フォールバック。
- 置換が発生した場合は QA レポートに `WARNING`（off-template font）として記録し、ブランド逸脱を可視化。

### 6.4 共通フロー

```
生成 → QAエンジン(qa/) で検査 → ERROR有り? 
  ├─ No  → 確定
  └─ Yes → fixer/ で自動修正(最大N回) → 再QA
            └─ 解消不能 → Routing でルートA再試行 → なお不能なら WARNING付きで確定 + ユーザー通知
```

---

## 7. 既存資産マッピング（流用 / 新規開発の区分）

| コンポーネント | 出所 | 区分 |
|----------------|------|------|
| 生成パイプライン / QA / fixer / cache / validators | pptx-agent | **流用** |
| chart/table/smartart wrapper | pptx-agent | **流用**（replace_data 検出は拡張） |
| CLI / API / MCP | pptx-agent | **流用＋拡張**（Bridge 化） |
| React UI（Uploader/Preview/Editor/E2E） | powerpoint-maker | **流用** |
| Web リサーチ（DuckDuckGo） | powerpoint-maker | **移植**（上流エージェント化） |
| docling による既存 PPTX/PDF 抽出 | powerpoint-maker | **移植** |
| 抽象レイアウト型 + Mapper | powerpoint-maker | **思想移植**（スキーマ統合） |
| Bridge Server（監視/ステージング/Routing） | — | **新規開発** |
| ルートA（DOM レンダラー + px→EMU 変換器） | — | **新規開発** |
| templatepptx 連携層 | OSS | **新規統合** |

---

## 8. 段階的実装計画（フェーズ）

| フェーズ | 目標 | 主要成果物 | 検証 |
|----------|------|-----------|------|
| **P0: 基盤統合** | agent を BE、maker/frontend を FE として疎結合接続 | Bridge(API) 経由で maker UI から agent 生成を実行 | 既存 E2E が緑 |
| **P1: ルートB 強化** | templatepptx 統合 + `replace_data()` による既存チャート差替 | ブランド維持の置換生成 | 視覚回帰 |
| **P2: 調査エージェント層** | リサーチ/抽出を上流化し CompositionManifest を確立 | PDF/Excel/URL → マニフェスト | スキーマ検証 |
| **P3: ルートA（DOM）** | ヘッドレスレンダラー + px→EMU 変換器の PoC→実装 | 自由版面スライド生成 | 幾何精度検証 |
| **P4: Routing & QA 統合** | スライド単位の A/B 切替 + 自動修正フォールバック | RenderPlan 駆動の生成 | QA ゼロ ERROR 率 |
| **P5: 例外処理完成** | 自動分割/フォント FB/自動スケールの全戦略実装 | 堅牢な生成 | ストレステスト |

---

## 9. 技術検証項目（PoC で先に潰すリスク）

1. **px→EMU 変換の精度**: ブラウザの 96dpi 前提と PowerPoint の EMU/Pt 換算で、テキストベースライン・行間に許容誤差内で収まるか。
2. **ヘッドレスブラウザのコスト**: スライド毎に Playwright を起動するレイテンシ。ページ再利用/プールで吸収できるか。
3. **`replace_data()` の互換性**: テンプレート作成元（PowerPoint バージョン/外部ツール）による埋め込み Excel 構造差で失敗しないか。
4. **SmartArt XML 書換の堅牢性**: 未知レイアウトでノード数不一致時の安全な失敗（現状 `NotImplementedError` スタブ）。
5. **templatepptx と自前 wrapper の責務衝突**: 二重置換・スタイル喪失が起きないか。
6. **ライセンス整合**: pptx-agent(Apache/MIT 系)・powerpoint-maker(MIT)・templatepptx の各ライセンス確認。

---

## 10. リポジトリ／ディレクトリ構成案

```
（モノレポ化 or サブモジュール）
integrated-pptx/
├── backend/                 # = pptx-agent をベース
│   └── src/pptx_agent/
│       ├── bridge/          # ★新設: 監視/ステージング/Routing Policy
│       ├── renderers/
│       │   ├── xml_route/   # 既存 pptx_wrapper を再編
│       │   └── dom_route/   # ★新設: Playwright + px→EMU 変換
│       ├── agents/          # story_analyzer + research(移植)
│       ├── qa/  fixer/  cache/  validators/  template_parser/   # 流用
│       └── interfaces/      # api(Bridge化) / cli / mcp
├── frontend/                # = powerpoint-maker/frontend をベース (React 19)
└── docs/
    └── design/integrated-pptx-system-design.md   # 本書
```

---

## 付録: 出典

- [templatepptx (Samir-Sell)](https://github.com/Samir-Sell/templatepptx) — テンプレート全置換・strict_mode
- [pptx-template (m3dev)](https://github.com/m3dev/pptx-template) — JSON モデル駆動テンプレートエンジン
- [pptx-replace (PyPI)](https://pypi.org/project/pptx-replace/) — テキスト/画像/テーブル置換
- [python-pptx: ChartData / replace_data](https://python-pptx.readthedocs.io/en/latest/api/chart-data.html) — XML＋埋め込み Excel ワークシートの同時更新
- [python-pptx: Concepts](https://python-pptx.readthedocs.io/en/latest/user/concepts.html)
