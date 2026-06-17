# pptx-maker-nx モノレポ統合ガイド（git subtree / 履歴保持）

> 目的: `pptx-agent`（バックエンド）と `powerpoint-maker` の `frontend/`（フロントエンド）を、
> **コミット履歴を保持したまま** 単一モノレポ `pptx-maker-nx` に統合する。
> 本手順は本リポジトリの実環境で `git subtree split` / `git subtree add` を実行し検証済み。

## 完成形

```
pptx-maker-nx/
├── backend/      ← pptx-agent 全体（src/ tests/ docs/ pyproject.toml mise.toml …）
├── frontend/     ← powerpoint-maker の frontend/ のみ（React19 + Vite + Playwright）
├── pnpm-workspace.yaml   （任意）
├── mise.toml             （ルート集約タスク）
└── README.md
```

- **方式**: git subtree（`--squash` を付けないことで履歴をグラフト＝保持）
- **検証結果**: backend(48) + frontend(6) + 初期/マージコミットが統合され、合計コミット数が積算されること、
  両ディレクトリのファイルが配置されることを確認済み。

---

## 前提

- `git` 2.x（`git subtree` 同梱）。`git subtree --help` が通ること。
- 上流2リポジトリが push 済み・クリーンであること。
- 以後のコマンドはユーザーのローカルマシンを想定。リモート URL は適宜読み替え:
  - `https://github.com/Fukuchan77/pptx-agent.git`
  - `https://github.com/Fukuchan77/powerpoint-maker.git`

> ⚠️ コミット署名を強制している環境では、subtree が作る**マージコミットも署名対象**になる。
> 通常のローカル環境では問題ないが、署名サーバ前提の CI 等で実行する場合は identity 設定に注意。

---

## 手順

### STEP 0 — モノレポを初期化

```bash
mkdir pptx-maker-nx && cd pptx-maker-nx
git init
git commit --allow-empty -m "chore: init pptx-maker-nx monorepo"
```

### STEP 1 — 上流をリモート登録（将来の追従に必須）

```bash
git remote add upstream-agent https://github.com/Fukuchan77/pptx-agent.git
git remote add upstream-maker https://github.com/Fukuchan77/powerpoint-maker.git
git fetch upstream-agent
git fetch upstream-maker
```

### STEP 2 — backend を取り込む（pptx-agent 全体）

```bash
git subtree add --prefix=backend upstream-agent main \
  -m "merge: import pptx-agent into backend/ (history preserved)"
```

> 設計書（`docs/design/…`）も含めたい場合は `main` の代わりに該当ブランチ名を指定する。

### STEP 3 — frontend を取り込む（powerpoint-maker の frontend/ サブツリーのみ）

`powerpoint-maker` 全体ではなく `frontend/` だけが欲しいので、**一度サブツリーを切り出す（split）** 必要がある。
上流クローンを一時取得して split → モノレポへ add する。

```bash
# 3-1. 一時クローンで frontend/ を履歴ごと切り出す
git clone https://github.com/Fukuchan77/powerpoint-maker.git /tmp/_maker
cd /tmp/_maker
git subtree split --prefix=frontend -b frontend-only
#   → 'frontend-only' ブランチに frontend/ をルート化した履歴ができる

# 3-2. モノレポへ取り込む
cd -   # pptx-maker-nx に戻る
git subtree add --prefix=frontend /tmp/_maker frontend-only \
  -m "merge: import powerpoint-maker frontend/ into frontend/ (history preserved)"

# 3-3. 後片付け
rm -rf /tmp/_maker
```

これで `backend/` と `frontend/` が履歴付きで配置される。確認:

```bash
ls                              # backend  frontend
git log --oneline | head        # 上流のコミットがグラフトされている
git log --oneline -- backend | head
git log --oneline -- frontend | head
```

### STEP 4 — ルートのモノレポ整備

最低限、以下を用意する。

**`.gitignore`**（両者の内容をマージ。`backend/.venv`, `frontend/node_modules`, `*.pptx` 出力等）

**`pnpm-workspace.yaml`**（フロントを workspace 化する場合）

```yaml
packages:
  - "frontend"
```

**ルート `mise.toml`**（両スタックのタスクを集約する例）

```toml
[tasks."backend:dev"]
dir = "backend"
run = "uv run uvicorn pptx_agent.interfaces.api:app --reload"

[tasks."frontend:dev"]
dir = "frontend"
run = "pnpm dev"

[tasks."dev"]
depends = ["backend:dev", "frontend:dev"]

[tasks."ci"]
run = ["mise run backend:ci", "mise run frontend:ci"]
```

**フロントの API 接続先**を Bridge（backend）に向ける（`frontend/src` の axios baseURL / `.env`）。

**初期コミット**:

```bash
git add .
git commit -m "chore: scaffold monorepo root (workspace, tasks, gitignore)"
```

### STEP 5 — 新しいリモートへ push（任意）

```bash
git remote add origin https://github.com/<you>/pptx-maker-nx.git
git push -u origin main
```

---

## 上流の更新を取り込む（将来のメンテ）

履歴を保持しているので、上流の変更を後から取り込める。

```bash
# backend（pptx-agent）の更新
git subtree pull --prefix=backend upstream-agent main -m "merge: sync backend with upstream"

# frontend（powerpoint-maker/frontend）の更新 … 都度 split が必要
cd /tmp && git clone https://github.com/Fukuchan77/powerpoint-maker.git _maker && cd _maker
git subtree split --prefix=frontend -b frontend-only
cd -  # モノレポ
git subtree pull --prefix=frontend /tmp/_maker frontend-only -m "merge: sync frontend with upstream"
rm -rf /tmp/_maker
```

> frontend 側は「split してから pull」が定型。頻繁に追従するならこの2コマンドをスクリプト化（例 `scripts/sync-frontend.sh`）すると良い。

---

## 補足・判断材料

| 論点 | 方針 |
|------|------|
| `--squash` を付けるか | **付けない**（履歴・blame を残すため）。リポジトリを軽くしたいだけなら `--squash` で1コミットに圧縮も可。 |
| backend は src だけで良いか | **リポジトリ全体**を取り込む（tests/docs/pyproject/mise/CI が揃い、そのまま動く）。 |
| frontend の lock/設定 | `frontend/pnpm-lock.yaml` 等は frontend 配下に保持されるため、そのまま `pnpm install` 可能。 |
| Python と JS の混在 | Nx は不要。**uv/mise（backend）＋ pnpm workspace（frontend）** が最小構成。 |
| 双方向の貢献 | モノレポ→上流へ戻す場合は `git subtree push --prefix=backend upstream-agent <branch>` が使える。 |

## トラブルシュート

- `git subtree add` が `working tree has modifications` で失敗 → 作業ツリーをコミット/stash してクリーンにする。
- 署名強制環境でマージコミットが失敗 → コミット identity が署名鍵の許可対象か確認（CI 等）。
- `frontend/` の履歴が `git log -- frontend` で薄く見える → split で paths が再ルート化されるための表示上の挙動。`git log --follow` や全体の `git log` では履歴は残っている。
