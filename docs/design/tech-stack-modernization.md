# 技術スタック モダナイズ提案（pptx-maker-nx）

> 前提: `pptx-agent`（backend）と `powerpoint-maker`（frontend / 旧backend）の実依存定義を精査した上での評価。
> 結論先出し: **両スタックは既にモダン**。やるべきは「古い物の更新」ではなく **統合に伴う一本化（consolidation）とギャップ補完**。

## 0. 現状アセスメント（実バージョン）

| レイヤ | pptx-agent | powerpoint-maker | 評価 |
|--------|-----------|------------------|------|
| Python | `>=3.12`（CIで3.12/3.13） | `>=3.12` | ◎ モダン |
| Web FW | FastAPI 0.136 / uvicorn 0.46 | FastAPI 0.128 | ◎ |
| LLM 基盤 | **Pydantic AI 1.83 + LiteLLM** | **BeeAI 0.1.76** | ⚠ **二重化**。要一本化 |
| ビルド/pkg | uv + hatchling | uv | ◎ |
| Lint | ruff 0.15・**50+ ルールセット** | ruff 0.14・**5 ルール(E,F,I,W,B)** | ⚠ 格差大 |
| 型検査 | **pyright strict + ty** | **ty 0.0.13 のみ**（alpha） | ⚠ maker は型ゲート弱 |
| line-length | 100 | 120 | ⚠ 不一致 |
| 観測性 | **Logfire**(OTel/pydantic統合) | structlog + json-logger | ⚠ 不一致 |
| Frontend | — | React 19.2 / Vite 7 / Vitest 4 / Biome 2.3 / TS 5.9 / Playwright 1.58 / pnpm | ◎ 最先端 |
| FE データ層 | — | **生 axios のみ**（状態管理・サーバ状態ライブラリ無し） | ⚠ ギャップ |

→ つまり**バージョンは新しい**。問題は「2つの異なる選択が混在」していること。統合時に基準を揃えるのがモダナイズの主眼。

---

## 1. 最優先（P1）— 一本化で技術的負債を作らない

### P1-1. LLM フレームワークを Pydantic AI に統一 ★最重要
- 現状: agent=Pydantic AI+LiteLLM、maker=BeeAI(0.1.x)。**統合すると2つのLLM基盤が同居**する。
- 推奨: **Pydantic AI + LiteLLM に一本化**。理由:
  - 型安全な structured output（Pydanticモデル直結）、agent側で既に成熟運用。
  - LiteLLM 経由で OpenAI/Anthropic/watsonx/Ollama を網羅 → maker の Ollama 利用も吸収可能。
  - BeeAI は 0.1.x で API 安定性リスク。DuckDuckGo 検索は Pydantic AI の tool として再実装可能（数十行）。
- 効果: 依存削減、観測性(Logfire)とリトライ/フォールバックの実装を1系統に集約。

### P1-2. Lint / 型検査 / フォーマットを agent 基準に統一
- ruff: agent の **50+ ルールセット**（S=bandit, ASYNC, PTH, SIM, RET 等）をリポジトリ全体へ適用。
- 型: **pyright strict をゲート**に採用（maker backend を strict 化）。`ty` は高速プリチェックとして併用（ty は Astral 製の次世代型チェッカーだが 0.0.x のため**単独ゲートにはまだ早い**）。
- line-length は **100 に統一**（agent 準拠）。
- Frontend は **Biome 2** が既に高速・モダン。backend(ruff) と合わせ「Rust製ツールチェーン」で統一感あり。

### P1-3. 観測性を Logfire に統一
- LLM アプリはトークン/レイテンシ/トレースの可視化が要。**Logfire（OpenTelemetry ベース、Pydantic AI とネイティブ統合）** に寄せる。
- 既存 structlog のログは OTel ログとして送出可能。構造化ログ + 分散トレースを1基盤で。

---

## 2. 中優先（P2）— フロントエンドのギャップ補完

現状フロントは `axios + react` のみで、状態管理・サーバ状態・型共有が手薄。統合アプリ（ジョブ非同期 + プレビュー編集）では以下が効く。

### P2-1. 型安全な API 契約（最高ROI）
- FastAPI の **OpenAPI スキーマから TS 型を自動生成**（`openapi-typescript` もしくは `orval`）。
- 効果: バックエンドの Pydantic モデル変更が**コンパイル時にフロントへ波及** → 手書き axios 型を撤廃し、契約drift を根絶。

### P2-2. サーバ状態ライブラリ TanStack Query
- 生 axios → **TanStack Query** に置換。ジョブ status のポーリング/SSE、キャッシュ、リトライ、ローディング/エラー状態を宣言的に。
- 「生成→QA→自動修正」の長時間ジョブ進捗管理と相性が良い。

### P2-3. 軽量クライアント状態 Zustand
- プレビュー編集のスライド状態が育つと props バケツリレーが破綻する。**Zustand**（Redux より軽量、React 19 と好相性）を導入。

### P2-4. テストの底上げ
- **Vitest 4 の browser mode** を活用し jsdom 依存を削減（実ブラウザ DOM での検証）。
- Playwright(×3ブラウザ) は維持。MSW でAPIモックを共通化。

---

## 3. 低優先 / 検討（P3）

| 項目 | 推奨 |
|------|------|
| Python 既定 | floor は 3.12 維持しつつ、CI/Docker 既定を **3.13** に（性能・型改善）。free-threading は要件次第で様子見。 |
| MCP 依存 | agent の MCP サーバが参照する `mcp` パッケージを **依存に明示追加**（現状未宣言）。 |
| Frontend FW | **Vite SPA を維持推奨**。フォルダ名の "Next" は次世代の意とのことなので Next.js 移行は不要。Python バックエンド + ローカルツールの性格上、SSR/RSC の便益は薄く、移行コストに見合わない。BFF が要るなら FastAPI(Bridge) が担う。 |
| モノレポ task | **mise**（backend）+ **pnpm workspace**（frontend）で十分。Turborepo/Nx は 1FE+1BE 規模では過剰。 |
| uv workspace | backend を将来パッケージ分割するなら uv workspace を採用。現状は単一で不要。 |
| コンテナ | マルチステージ + distroless で軽量化。`docker-compose` で backend+frontend+（任意 Ollama）を一括起動。ルートA用に Playwright ブラウザ同梱イメージを別途。 |
| ルートA ランタイム | DOM レンダラーは **Playwright(Chromium)** をサーバサイドで使用（フロントのテスト用 Playwright とバージョン統一）。 |

---

## 4. 推奨スタック最終形（統合後）

```
Backend (pptx-agent ベース)
  言語     : Python 3.12 floor / 3.13 既定
  Web      : FastAPI + uvicorn（Bridge Server もここ）
  LLM      : Pydantic AI + LiteLLM（BeeAI は廃止）   ← P1-1
  観測     : Logfire (OpenTelemetry)                ← P1-3
  品質     : ruff(50+) + pyright strict + ty(高速プリチェック) ← P1-2
  pkg/task : uv + hatchling + mise

Frontend (powerpoint-maker/frontend ベース)
  Core     : React 19 + Vite 7 + TypeScript 5.9（維持）
  API      : OpenAPI → TS 型自動生成                ← P2-1
  サーバ状態: TanStack Query                         ← P2-2
  client状態: Zustand                                ← P2-3
  品質     : Biome 2 + Vitest 4(browser mode) + Playwright ← P2-4
  pkg      : pnpm workspace
```

---

## 5. 段階移行（モノレポ統合と並行）

| 順 | 作業 | 破壊度 | 価値 |
|----|------|--------|------|
| 1 | ルートに ruff/pyright/biome 設定を一本化、line-length=100 | 低 | 一貫性 |
| 2 | OpenAPI → TS 型生成を CI に組込み | 低 | 契約安全 |
| 3 | TanStack Query 導入（axios 呼び出しを順次置換） | 中 | UX/保守性 |
| 4 | maker の research を BeeAI → Pydantic AI tool へ移植、BeeAI 依存削除 | 中 | 負債解消 |
| 5 | Logfire に観測性を統一 | 中 | 運用性 |
| 6 | Zustand でプレビュー編集状態を集約 | 中 | 拡張性 |

> 重要: いずれも **「新しくする」より「2系統を1系統に畳む」** 作業。バージョン更新の緊急性は低く、統合のタイミングで基準を agent 側（より厳格・成熟）に寄せるのが最小コスト。

---

## 付録: 出典（一次情報）

- 現状バージョンは各リポジトリの `pyproject.toml` / `frontend/package.json` を直接参照。
- Pydantic AI / LiteLLM, Logfire(OpenTelemetry), TanStack Query, openapi-typescript, Zustand, Vitest browser mode は各公式ドキュメント参照のこと。
