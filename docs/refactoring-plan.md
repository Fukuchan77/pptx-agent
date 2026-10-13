# リファクタリング計画: テンプレート／素材集準拠の精度向上

- ステータス: 提案（Draft）
- 作成日: 2026-10-13
- 対象: `src/pptx_agent` 全体（特に `template_parser` / `agents` / `pptx_wrapper` / `qa` / `fixer`）
- 参照仕様:
  - ISO/IEC 29500-1:2016（= ECMA-376 Part 1, 5th edition）— PresentationML（§19）、DrawingML（§20, §21）
  - ISO/IEC 29500-2（ECMA-376 Part 2）— Open Packaging Conventions（OPC）
  - ISO/IEC 29500-3（ECMA-376 Part 3）— Markup Compatibility and Extensibility（MCE）
  - ISO/IEC 29500-4（ECMA-376 Part 4）— Transitional Migration Features
  - Anthropic `skills/pptx/SKILL.md`（テンプレート編集・QA のベストプラクティス）

---

## 1. 目的

「指定したテンプレート」と「指定した素材集（アセットライブラリ）」に **忠実に従った** スライドを生成できるようにし、出力の精度（体裁・文字収まり・規格準拠・内容の忠実度）を定量的に向上させる。

### 1.1 ゴール（受け入れ基準の要約）

| # | ゴール | 測定方法 |
|---|---|---|
| G1 | テンプレートのレイアウト・プレースホルダー・書式（フォント／色／箇条書き／余白）を壊さない | 書式継承違反数 = 0（§6 の指標 M3, M4） |
| G2 | 素材集のスライドパターン・アイコン・画像・図表を正しく再利用できる | 素材適用成功率 ≥ 95%（M6） |
| G3 | 文字のはみ出しを生成前に防ぎ、生成後にレンダリングで検証する | レンダリング後のはみ出し率 ≤ 2%（M2） |
| G4 | 出力が ECMA-376 / ISO/IEC 29500 準拠で PowerPoint が修復ダイアログを出さない | XSD・OPC 検証エラー（テンプレート由来を除く）= 0（M1） |
| G5 | 精度を回帰テストで継続的に計測できる | 評価ハーネスが CI で動作（§6） |

### 1.2 スコープ外

- テンプレートを使わないゼロからのデザイン生成（`pptxgenjs` 型のフリーデザイン）
- `.ppt`（バイナリ形式）の直接サポート（必要なら LibreOffice で事前変換）
- Strict 形式（ISO/IEC 29500-1 Strict 名前空間）での出力。出力は PowerPoint 互換性のため **Transitional** とする（§4.6）

---

## 2. 現状分析

コードを読んで確認した、精度を直接損なっている問題点を重要度順に列挙する。

### 2.1 致命的（出力品質に直結）

| ID | 問題 | 該当箇所 | 影響 |
|---|---|---|---|
| P1 | テンプレート内の既存スライド（例: `basic-template.pptx` のサンプル 2 枚）を削除せずに後ろへ追加している | `pptx_wrapper/slide_builder.py:170-` `build_presentation` | 出力冒頭に "Sample Template" 等のゴミスライドが残る |
| P2 | `text_frame.text = text` でテキストを一括代入している | `pptx_wrapper/type_helpers.py:134`, `pptx_wrapper/slide.py:51` | 段落が 1 つの書式なし run に潰れ、レイアウトの `a:lstStyle`／段落レベル（`lvl`）／箇条書き書式が失われる（SKILL.md でも明示的に禁止） |
| P3 | プロンプトが箇条書き記号 `•` を本文に書かせている | `agents/prompts/content_generator.py:32` | テンプレートの箇条書き（`a:buChar`）と二重表示になる |
| P4 | スピーカーノートを PPTX に書き込んでいない（`SlideSchema.notes` が未使用） | `pptx_wrapper/slide_builder.py` | 生成したノートが失われる。QA の `SpeakerNotesVerificationRule` だけが存在 |
| P5 | 複数プレースホルダーのレイアウト（Two Content / Comparison / Content with Caption）で、最初の BODY/OBJECT にしか流し込まない | `agents/content_generator.py` `_determine_placeholder_name` | 2 列目・キャプション等が空欄のまま残る |
| P6 | オーバーフロー解決の結果をログ出力するだけで適用していない | `pipeline.py:224-` | 「Smart Content Fitting」が実質機能していない |
| P7 | 文字容量を「幅 0.1 インチ／行高 0.2 インチ」の固定値で推定し、日本語は一律 0.55 倍 | `template_parser/parser.py:189-`, `constants.py:27-30`, `utils/text_capacity.py:14` | フォントサイズ・内側余白・行間・自動調整設定・全角/半角幅を無視。例: タイトルの `max_chars` が 540〜680 字と非現実的（`templates/basic-manifest.json`） |

### 2.2 重大（テンプレート／素材集への準拠を阻害）

| ID | 問題 | 該当箇所 |
|---|---|---|
| P8 | プレースホルダーを **名前** の部分一致（fuzzy）で探している。規格上の対応キーは `p:ph/@idx`（と `@type`） | `pptx_wrapper/placeholder_ops.py:17-`, `pptx_wrapper/slide.py:72` |
| P9 | レイアウトの意味を名前文字列で判断（"Title Slide" 等）。`p:sldLayout/@type`（ST_SlideLayoutType: `title`, `obj`, `twoObj`, `secHead` 等）を使っていないため、日本語名レイアウト（「タイトル スライド」）や独自名テンプレートで破綻する | `agents/prompts/outline_generator.py`, `template_parser/parser.py` |
| P10 | テーマ（`a:clrScheme`, `a:fontScheme`）、マスターのテキストスタイル（`p:txStyles`）、`p:clrMap`、`a:bodyPr`（余白・アンカー・自動調整）を一切抽出していない | `template_parser/` 全体 |
| P11 | 「素材集」（アイコン・写真・図解パーツ・デザイン済みスライドパターン）の概念がない。画像は LLM がローカルパスを書く `ImageBlock` のみ | `schemas/visual_assets.py` |
| P12 | SmartArt は「スライドに既に存在する図」のテキスト置換のみ。レイアウトから追加したスライドには SmartArt が存在しないため、実用上ほぼ機能しない。また `dm`（データモデル）を書き換えても `dsp:drawing`（描画キャッシュ）を更新していない | `pptx_wrapper/smartart.py` |
| P13 | `supports_charts/tables/smartart` を `OBJECT` プレースホルダーの有無だけで判定 | `template_parser/manifest_builder.py:23-29` |
| P14 | マニフェストのスキーマが 2 系統（`TemplateMetadata` と `TemplateManifest`）あり、同梱 `basic-manifest.json` は前者の形（`has_smartart`）で後者と不整合 | `template_parser/models.py`, `schemas/template_manifest.py` |

### 2.3 品質保証の欠落

| ID | 問題 | 該当箇所 |
|---|---|---|
| P15 | OOXML スキーマ（XSD）検証・OPC 検証（リレーションシップ／Content Types／孤立パート）がない | `validators/file_validator.py` は ZIP の安全性のみ |
| P16 | はみ出し検出が文字数ヒューリスティックのみで、レンダリング結果を見ていない | `qa/rules/layout_checks.py:26-` |
| P17 | スタイル系ルールの一部が未実装（`OffTemplateColorRule` は常に空を返す） | `qa/rules/style_checks.py:107-129` |
| P18 | テンプレートの残留テキスト（"Click to add text"、"Lorem ipsum"、サンプル文言）の検出がない | `qa/rules/` |
| P19 | 精度を測る評価セット・指標がない（単体テストは豊富だが「良いスライドか」を測っていない） | `tests/` |

### 2.4 構造上の問題

- `pipeline.py` が逐次手続きで、各ステージの入出力が `Any`／ファイルパス経由（QA・Fix がファイルを再読込）。ステージ単位の差し替え・再実行・キャッシュがしにくい。
- コンテンツブロックの Union（`schemas/slide.py`）に判別子（discriminator）がなく、プロンプトの `"type"` フィールドとスキーマが一致していない。
- `slide_builder.py` の `build_presentation` と `rebuild_slide_with_layout` でブロック描画処理が重複している。

---

## 3. 設計方針

1. **テンプレートファースト／素材集ファースト**: LLM に「自由に書かせて後から直す」のではなく、テンプレートと素材集から抽出した **スロット（差し込み口）と予算（行数・文字幅）** を先に確定し、LLM にはそのスロットを埋めさせる。
2. **規格準拠の継承モデルに従う**: プレースホルダーは `idx` で slide → layout → master の順に継承される（§19 PresentationML）。書式は上書きせず継承させ、必要な場合のみ最小限の `a:pPr`／`a:rPr` を書く。
3. **決定的処理と LLM 処理の分離**: 解析・容量計算・配置・検証は決定的（テスト可能）に、LLM は「構成・言語表現・素材選択」に限定する。
4. **計測して直す**: 文字収まりは実フォントメトリクスで計測し、最終的にはレンダリング画像で検証する。
5. **Python スタックを維持**: テンプレート編集が主用途のため、SKILL.md の推奨どおり「既存 PPTX の XML を編集する」方式を採る。`pptxgenjs` は導入しない。python-pptx は高レベル操作に使い、足りない部分は `lxml` で OOXML を直接操作する（未信頼入力のパースは `defusedxml`）。

---

## 4. 目標アーキテクチャ

### 4.1 全体フロー

```
入力テキスト ─┐
テンプレート ─┼─▶ [A] TemplateProfiler ──▶ TemplateProfile ─┐
素材集 ───────┘    [B] AssetCataloger  ──▶ AssetCatalog ───┤
                                                              ▼
            [1] StoryAnalyzer (LLM) ─▶ [2] SlidePlanner (LLM + 制約ソルバ)
                                              │  レイアウト/素材パターン/スロット割当
                                              ▼
                                       [3] SlotFiller (LLM, 予算付き)
                                              │  スロット単位で文章を生成
                                              ▼
                                       [4] FitEngine (決定的)
                                              │  実測→要約再生成→分割→自動調整
                                              ▼
                                       [5] Renderer (OOXML 直接操作)
                                              ▼
                                       [6] Validator (OPC/XSD/意味/レンダリング)
                                              ▼
                                       [7] FixLoop ─(未解決)─▶ [3] or [4] へ差し戻し
                                              ▼
                                           出力 .pptx + QA レポート
```

### 4.2 モジュール構成（案）

```
src/pptx_agent/
├── ooxml/                 # 新設: 規格レベルの低水準操作
│   ├── namespaces.py      # Transitional 名前空間定数
│   ├── package.py         # OPC: パート・リレーションシップ・[Content_Types].xml
│   ├── slide_ops.py       # スライド複製/削除/並べ替え、孤立パート掃除（clean）
│   ├── text.py            # 段落・run 単位のテキスト書き込み（書式保持）
│   ├── import_part.py     # 別パッケージ（素材集）からのスライド/メディア/チャート取り込み
│   └── schema/            # XSD 一式と検証器（§4.6）
├── profile/               # template_parser を置換
│   ├── profiler.py        # TemplateProfile 抽出
│   ├── inheritance.py     # slide→layout→master→theme の書式解決
│   ├── metrics.py         # フォントメトリクスと実測による容量計算
│   └── models.py          # TemplateProfile / LayoutProfile / SlotProfile
├── assets/                # 新設: 素材集
│   ├── catalog.py         # AssetCatalog 構築（索引・サムネイル・スロット抽出）
│   ├── models.py          # AssetManifest スキーマ
│   └── selector.py        # 素材選択（制約 + LLM ランキング）
├── planning/              # outline_generator を置換
├── generation/            # content_generator を置換（スロット単位生成）
├── fitting/               # overflow_resolver + fixer/text_overflow を統合
├── render/                # slide_builder を置換
├── qa/                    # 既存を拡張（render_check, ooxml_check を追加）
└── pipeline/              # ステージをクラス化、PipelineContext で受け渡し
```

既存の `interfaces/`（CLI・REST API・MCP）、`validators/security.py`、`cache/` は維持し、内部呼び出し先だけを差し替える。

### 4.3 TemplateProfile（テンプレート解析の深掘り）

抽出対象（すべて ECMA-376 Part 1 の要素に対応づける）:

| 抽出項目 | 取得元（OOXML 要素） | 用途 |
|---|---|---|
| スライドサイズ | `p:presentation/p:sldSz` | 座標計算・境界チェック |
| レイアウト種別 | `p:sldLayout/@type`（ST_SlideLayoutType） | 名前非依存のレイアウト選択（P9） |
| プレースホルダー | `p:nvPr/p:ph` の `@type` `@idx` `@sz` `@orient` `@hasCustomPrompt` | `idx` ベースのスロット同定（P8） |
| 位置・サイズ | `a:xfrm`（未指定時は layout→master から継承解決） | 容量計算・配置 |
| テキスト本文設定 | `a:bodyPr` の `lIns/tIns/rIns/bIns`（既定 91440/45720/91440/45720 EMU）, `anchor`, `wrap`, `vert`, `a:normAutofit`/`a:spAutoFit`/`a:noAutofit` | 容量計算・はみ出し方針 |
| 段落レベル書式 | `a:lstStyle/a:lvl1pPr…lvl9pPr`（`sz`, `marL`, `indent`, `a:lnSpc`, `a:spcBef`, `a:buChar`/`a:buAutoNum`/`a:buNone`） | 行高・箇条書き・インデント |
| マスターの既定スタイル | `p:sldMaster/p:txStyles`（`p:titleStyle`, `p:bodyStyle`, `p:otherStyle`） | 継承解決の最終段 |
| 色マッピング | `p:sldMaster/p:clrMap`, `p:sldLayout/p:clrMapOvr` | テーマ色解決 |
| テーマ | `a:theme/a:themeElements/a:clrScheme`（dk1, lt1, dk2, lt2, accent1–6, hlink, folHlink）, `a:fontScheme`（`a:majorFont`/`a:minorFont` の `a:latin`/`a:ea`/`a:cs`） | 色・フォント準拠チェック、チャート配色 |
| プロンプト文言 | プレースホルダー内の既定テキスト | 残留テキスト検出（P18） |
| 装飾シェイプ | layout/master 上の非プレースホルダー図形 | 重なり判定の除外・衝突領域 |
| サムネイル | LibreOffice でレンダリング | LLM（VLM）によるレイアウト選択補助 |

**SlotProfile**（スロット = 1 つの差し込み口）:

```python
class SlotProfile(BaseModel):
    idx: int                      # p:ph/@idx
    ph_type: PlaceholderType      # title / body / obj / pic / chart / tbl / dgm / subTitle ...
    role: SlotRole                # title / subtitle / body / body_left / body_right / caption / image ...
    bbox_emu: Rect                # 継承解決後の位置・サイズ
    insets_emu: Insets
    autofit: Literal["none", "shape", "normal"]
    levels: list[LevelStyle]      # lvl1..lvl9 の font_size_pt / line_spacing / indent / bullet
    font: ResolvedFont            # +mj-lt/+mn-lt/+mn-ea をテーマから解決した実フォント名
    budget: dict[Lang, TextBudget]  # 言語別: max_lines, max_chars_per_line(level別)
    accepts: set[BlockKind]       # text / chart / table / image / diagram
```

`role` は `ph_type` と幾何配置（左右・上下関係）から決定的に推論する（例: `twoObj` の 2 つの `obj` は x 座標で left/right）。

**容量計算（P7 の置換）**:

- テーマ／継承から解決した実フォントのメトリクスを `fontTools` で読み、文字ごとの送り幅を合算して行幅を測る。フォントファイルが無い場合は、メトリクス互換フォント（Carlito↔Calibri、Liberation Sans↔Arial 等）か、Unicode East Asian Width（全角 = 1em、半角 ≈ 0.5em）による近似にフォールバックする。
- 有効幅 = `cx − lIns − rIns − marL`、有効高 = `cy − tIns − bIns`。行高 = フォントサイズ × 行間（`a:lnSpc` の `spcPct`/`spcPts`）＋ `spcBef`/`spcAft`。
- 日本語は禁則処理（行頭禁則・行末禁則）を考慮した折返しシミュレーションを行う。
- 出力は「文字数」ではなく **行数と行幅の予算**（`TextBudget`）とし、LLM には「1 項目あたり全角 N 文字以内 × 最大 M 項目」の形で渡す。

### 4.4 AssetCatalog（素材集）

素材集は次の 2 形態を受け付ける。

1. **素材集デッキ（.pptx/.potx）**: デザイン済みスライドパターン（3 カラムカード、タイムライン、KPI、比較表、プロセス図、SmartArt 見本、チャート見本、アイコン一覧など）を並べたファイル
2. **素材フォルダ**: アイコン（SVG/EMF/PNG）、写真、ロゴ等の画像ファイル

それぞれにサイドカーの `asset-manifest.yaml`（任意。無ければ自動抽出 + LLM で補完）を置く:

```yaml
version: 1
library: corporate-assets-2026
patterns:
  - id: kpi-3cards
    source: patterns.pptx#slide=4        # 素材集デッキの 4 枚目
    tags: [kpi, numbers, summary]
    use_when: "3 つの数値指標を並べて強調する"
    slots:                                # 自動抽出（cNvPr/@name と @descr で同定）を上書き可能
      - { shape: "KPI1_Value", role: stat_value, max_chars: 6 }
      - { shape: "KPI1_Label", role: stat_label, max_chars: 12 }
      # ...
    repeatable_group: "KPI{n}_*"          # 項目数に応じてグループ単位で削除/複製
    min_items: 2
    max_items: 4
icons:
  - { id: ico-security, file: icons/shield.svg, tags: [security, 安全], aspect: 1.0 }
images:
  - { id: img-team, file: photos/team.jpg, tags: [team, people], alt: "チームの集合写真", license: internal }
```

カタログ構築（`AssetCataloger`）の処理:

- 各パターンスライドをサムネイル化し、テキストを持つ図形を **スロット** として抽出（`p:cNvPr/@name`・`@descr`（代替テキスト）・グループ構造から同定）。スロットごとに §4.3 と同じ容量計算を行う。
- 「繰り返しグループ」（カード 1 枚分 = 画像 + 見出し + 本文のグループ）を検出し、項目数が素材の枠数と異なる場合はグループ単位で削除・複製できるようにする（SKILL.md「Template slots ≠ source items」）。
- 結果は `AssetCatalog`（JSON）としてテンプレートと同じハッシュベースキャッシュ（ADR 0004）に載せる。

**素材の取り込み（OOXML 操作）**: 素材集デッキのスライドを出力デッキへ取り込む際は、

- スライドパートと、それが参照する画像・チャート（`c:chartSpace` と埋め込みブック）・ダイアグラム（`dgm` の data/layout/quickStyle/colors/drawing の 5 パート）を **すべて複製** し、`r:id` を張り替える（複製元を参照したままにしない）。
- `[Content_Types].xml` に拡張子／パートの型を登録し、`p:sldIdLst` に ID（ST_SlideId: 256 以上、一意）を採番する。
- 取り込み先テンプレートのレイアウトにマッピングする（素材側レイアウトの `@type` と一致するもの、無ければ `blank`/`titleOnly`）。マスター・テーマは持ち込まない（テンプレートの見た目を優先）。
- 色は `a:srgbClr` ではなく `a:schemeClr` を使っていれば自動でテンプレートのテーマ色に追従する。`srgbClr` が混在する素材は検出して QA で警告する。
- SVG アイコンは PNG フォールバック付きで、`a:blip/a:extLst` に SVG 拡張（`asvg:svgBlip`）を MCE（Part 3）準拠の拡張として格納する。

### 4.5 計画・生成（LLM 部分）の再設計

**SlidePlanner**（`outline_generator` を置換）:

- 入力: StoryAnalysis、TemplateProfile（レイアウト一覧を `@type`・スロット構成・サムネイル付きで提示）、AssetCatalog（パターン一覧を `use_when`・枠数付きで提示）。
- 出力: スライドごとに `layout_ref`（テンプレートレイアウト）**または** `pattern_ref`（素材パターン）と、各スロットへ割り当てる内容の種類・項目数。
- 制約（決定的にチェックし、違反時は修正指示付きで再生成）:
  - 存在しないレイアウト／パターンの禁止
  - 項目数がパターンの `min_items..max_items` に収まること
  - 同一レイアウトの連続使用の上限（単調なデッキの防止）
  - 表紙は `title`、章扉は `secHead`、結びは指定レイアウトなど、`@type` ベースの規則
  - 数値データ → チャート可能スロット、手順 → プロセス系パターン等の対応

**SlotFiller**（`content_generator` を置換）:

- スライド単位で、そのスライドの **スロット一覧と各スロットの予算** を構造化して渡し、スロット ID をキーにした出力を返させる（Pydantic AI の `output_type` で型保証）。
- 箇条書きは「段落の配列（`text`, `level`）」で返させ、記号は書かせない（P3）。
- 強調は run 単位の構造（`[{text, bold}]`）で返させる。
- スピーカーノートはスロットとは別フィールド（P4）。
- 素材の画像・アイコンは **カタログ ID** で指定させ、パスを書かせない（P11、パストラバーサル対策にもなる）。
- コンテンツブロックは `kind: Literal[...]` による判別共用体にする。

### 4.6 Renderer（OOXML 直接操作）

`slide_builder.py` を置き換える。原則:

1. **構造操作を先に、内容の書き込みを後に**（SKILL.md）。テンプレート既存スライドの削除（P1）→ スライド追加・素材取り込み → 並べ替え → 孤立パート掃除 → 各スロットへの書き込み。
2. **テキスト書き込み**（P2, P3）:
   - 1 項目 = 1 つの `a:p`。階層は `a:pPr/@lvl` で表現し、箇条書きは継承に任せる（必要時のみ `a:buNone` 等で上書き）。
   - 既存の最初の段落・run の `a:pPr`/`a:rPr` を雛形として複製し、`run.text` 相当で文字だけ差し替える。
   - 言語属性: `a:rPr/@lang`（`ja-JP`/`en-US`）と `@altLang` を設定し、日本語フォントは `a:ea` から解決させる。
   - 前後空白を含むテキストには `xml:space="preserve"`。
   - 未使用スロットは空のまま残さず、プレースホルダー要素ごと削除する（"クリックしてテキストを入力" が表示されないように）。
3. **チャート**: python-pptx の `add_chart` で作成後、系列色を `a:schemeClr`（accent1..6）に設定し、タイトル・データラベル・凡例をテンプレート規約に合わせる。素材集に「チャート見本」がある場合は、その `c:chartSpace` の書式を雛形にデータだけ差し替える。
4. **表**: テンプレートの表スタイル（`a:tblStyleId`）を使用し、セル書式を直書きしない。
5. **ノート**: ノートスライドを生成して本文を書き込む（P4）。
6. **出力形式**: Transitional 名前空間（`http://schemas.openxmlformats.org/...`）で出力する。ISO/IEC 29500-1:2016 は Strict を規定するが、PowerPoint の既定保存形式と python-pptx は Transitional（Part 4）であり、互換性を優先する。
7. XML のシリアライズは `lxml` で行い、`xml.etree.ElementTree` で往復させない（名前空間プレフィックスが書き換わり破損するため）。

### 4.7 Validator（検証層）

| 層 | 内容 | 規格根拠 |
|---|---|---|
| V1 パッケージ | `[Content_Types].xml` の網羅性、全リレーションシップのターゲットが存在、孤立パートなし、`r:id` 一意 | Part 2（OPC） |
| V2 スキーマ | 変更したパート（slide / chart / notes / presentation.xml）を Transitional XSD で検証。テンプレート由来のエラーは **ベースライン差分** で除外（SKILL.md の `--original` と同じ考え方） | Part 1 + Part 4 の XSD |
| V3 意味的整合性 | `p:sldId/@id` が 256 以上かつ一意、`p:cNvPr/@id` がスライド内で一意、`p:presentation` の子要素順序、プレースホルダーの `idx` が layout に存在、チャートの軸 ID 整合 | Part 1 §19 / §21 |
| V4 テンプレート準拠 | フォントはテーマ参照（`+mj-lt`/`+mn-lt`/`+mn-ea`）または許可リストのみ、色は `schemeClr` またはパレット内、書式の直書き（`sz` 等）件数、レイアウト外へのはみ出し | テンプレートプロファイル |
| V5 内容 | 残留プロンプト文言・Lorem ipsum・`XXX`・テンプレートのサンプル文言の検出（P18）、空スロット、重複タイトル | — |
| V6 レンダリング | LibreOffice → PDF → 画像化し、(a) テキストの描画領域がシェイプ境界を越えていないか、(b) 要素の重なり、(c) 余白不足を検査。オプションで VLM による目視チェック | — |

V6 のフォント置換問題（LibreOffice で別フォントに置き換わると収まり判定が狂う）に対しては、テンプレートのフォントがメトリクス互換フォントで代替可能かを TemplateProfile に記録し、不可の場合は V6 の結果を「参考」扱いに格下げして §4.3 の実測値を優先する。

既存の `qa/` のルールレジストリ（ADR 0003）は維持し、V1〜V6 を新しいルールカテゴリとして登録する。

### 4.8 FitEngine と FixLoop

はみ出し対策を「生成前予算 → 実測 → 段階的解決」に一本化する（P6, P16）:

1. **予算内生成**: SlotFiller にスロット予算を渡す（大半はここで解決）。
2. **実測**: 書き込み前に §4.3 の折返しシミュレーションで行数を算出。
3. **解決順序**（スロット単位）:
   1. LLM による当該スロットのみの要約再生成（目標行数を明示、最大 2 回）
   2. 次スライドへの分割（「(続き)」スライドを同レイアウトで追加）
   3. より容量の大きいレイアウト／パターンへの切り替え
   4. フォント縮小（`a:normAutofit/@fontScale`、テンプレートが許す場合のみ・下限 pt を設定）
4. **生成後 FixLoop**: V1〜V6 の結果から、修正可能なものは自動修正、内容に関わるものは該当ステージへ差し戻す。`fixer/` の戦略レジストリはこの差し戻し機構に統合する。

---

## 5. 実施計画（フェーズ）

各フェーズは独立して main にマージ可能な単位とし、既存の CLI/API/MCP の互換性を保つ。

### Phase 0: 評価基盤の整備（先行）

精度向上を測れる状態を先に作る。

- 評価用コーパス: 既存 `examples/` 5 本 + 日本語中心のケース（長文・数値多め・手順多め）を追加し、計 10〜15 本。
- 評価用テンプレート: 同梱 2 種 + 「独自レイアウト名・日本語レイアウト名」「2 カラム多用」「装飾シェイプ多め」の 3 種を追加。
- 評価用素材集: パターン 10 種程度のデッキ + アイコン 20 個のフォルダ（テスト用、ライセンスフリーで自作）。
- 指標（§6）を算出する `scripts/evaluate.py` と、ベースライン（現行実装）のスコア記録。
- LLM 呼び出しは録画／再生（記録済みレスポンス）で決定的に回せるようにし、CI で実行可能にする。

完了条件: 現行実装のベースライン指標が `docs/evaluation/baseline.md` に記録されている。

### Phase 1: 即効性のある不具合修正（低リスク・高効果）

- P1: 生成前にテンプレート既存スライドを削除（オプションで保持可）＋孤立パート掃除
- P2: テキスト書き込みを段落・run 単位に変更（書式保持）
- P3: プロンプトから `•` を削除し、段落配列での出力に変更
- P4: スピーカーノートの書き込み
- P5: 複数プレースホルダーのレイアウトで全スロットを埋める（暫定: 段落を均等配分）
- P8: プレースホルダー同定を `idx` ベースに変更（名前一致はフォールバック）
- 未使用プレースホルダーの削除
- V5 の残留テキスト検出ルール追加

完了条件: 既存テストがすべて通り、Phase 0 指標の M3（書式継承違反）・M5（空スロット）・M7（残留テキスト）が改善している。

### Phase 2: TemplateProfile と容量計算

- `ooxml/` の基盤（名前空間、継承解決、パート操作）
- `profile/`（§4.3）の実装と、`TemplateMetadata`/`TemplateManifest` の統合（P14）。旧 `TemplateManifest` は `TemplateProfile` からの変換で後方互換を提供し、`--manifest` 引数は維持（非推奨警告）
- フォントメトリクス実測による `TextBudget`（P7）。`language_ratio`／0.55 固定値を廃止
- レイアウト種別を `@type` で判定（P9）
- キャッシュキーにプロファイラのバージョンを含める（ADR 0004 の拡張）

完了条件: 同梱テンプレートで、各スロットの予算と実レンダリング（LibreOffice）での行数の誤差が ±1 行以内となる割合が 90% 以上。

### Phase 3: 計画・生成の再設計（スロット駆動）

- SlidePlanner（制約チェック付き）と SlotFiller（スロット予算付き）
- 判別共用体スキーマ、`kind` フィールド
- FitEngine（§4.8 の 1〜3）。`overflow_resolver` と `fixer/strategies/text_overflow` を統合
- `pipeline.py` をステージクラス + `PipelineContext` に再構成（ファイル再読込の排除）

完了条件: M2（レンダリング後はみ出し率）≤ 5%、M5（空スロット）= 0。

### Phase 4: 素材集サポート

- `assets/`（カタログ構築、スロット抽出、繰り返しグループ検出）
- `ooxml/import_part.py`（スライド・メディア・チャート・ダイアグラムのパッケージ間取り込み）
- SlidePlanner への素材パターン統合、アイコン・画像のカタログ ID 指定
- SVG（PNG フォールバック付き）対応
- SmartArt は「素材集の見本スライドを取り込み、データモデルを書き換え、描画キャッシュ（`dsp:drawing`）を削除して再レイアウトさせる」方式に変更（P12）
- CLI/API/MCP に `--assets <path>` を追加

完了条件: M6（素材適用成功率）≥ 95%、素材取り込みスライドで V1〜V3 エラー 0。

### Phase 5: 検証層の完成

- V1（OPC）、V2（XSD、ベースライン差分）、V3（意味的整合性）
- V4 のフォント／色準拠（P17 の実装）
- V6 レンダリング QA（LibreOffice は任意依存。無い環境ではスキップし、レポートに明記）
- FixLoop と差し戻し機構

完了条件: M1（規格検証エラー）= 0、評価セット全件で PowerPoint 互換性チェック項目をすべて通過。

### Phase 6: 仕上げ

- 旧 API（`TemplateParser`、`resolve_overflow` 等）の削除または薄いラッパー化
- ドキュメント更新（user-guide / developer-guide / api-reference の日英）
- ADR の追加（下記）

### 追加予定の ADR

| 番号 | タイトル（案） |
|---|---|
| 0005 | OOXML 直接操作レイヤーの導入と Transitional 出力の採用 |
| 0006 | TemplateProfile とフォントメトリクスによる容量計算 |
| 0007 | 素材集（AssetCatalog）のフォーマットと取り込み方式 |
| 0008 | スロット駆動生成（SlidePlanner / SlotFiller）への移行 |
| 0009 | 多層検証（OPC / XSD / 意味 / レンダリング）とベースライン差分 |

---

## 6. 精度の評価指標

| ID | 指標 | 定義 | 目標 |
|---|---|---|---|
| M1 | 規格検証エラー | V1〜V3 のエラー件数（テンプレート由来を除く） | 0 |
| M2 | はみ出し率 | レンダリング後にはみ出したテキストスロット数 / 全テキストスロット数 | ≤ 2% |
| M3 | 書式継承違反 | テンプレートのスタイルを直書きで上書きした run 数（許可されたもの除く） | 0 |
| M4 | 準拠違反 | テーマ外フォント・パレット外色の使用件数 | 0 |
| M5 | 空スロット | 最終出力に残った空プレースホルダー数 | 0 |
| M6 | 素材適用成功率 | 計画で選ばれた素材パターンが V1〜V5 を通過して描画された割合 | ≥ 95% |
| M7 | 残留テキスト | プロンプト文言・サンプル文言・Lorem ipsum の残存件数 | 0 |
| M8 | レイアウト多様性 | 連続同一レイアウトの最大連続数 | ≤ 3 |
| M9 | 内容忠実度 | 入力の主要主張がスライドに反映された割合（LLM 判定 + 抜き取りの人手確認） | ≥ 90% |
| M10 | 予算精度 | 予算上の行数と実レンダリング行数の誤差 ±1 行以内の割合 | ≥ 90% |

各フェーズの PR では Phase 0 の評価スクリプトの結果（ベースラインとの差分）を記載する。

---

## 7. リスクと対策

| リスク | 対策 |
|---|---|
| フォントファイルが実行環境にない（游ゴシック、メイリオ等） | メトリクス互換フォント／East Asian Width 近似へフォールバックし、近似で計算したスロットには 10% の余裕を持たせる。ユーザーがフォントディレクトリを指定できる設定を追加 |
| LibreOffice のレンダリングが PowerPoint と異なる | V6 は補助扱い。合否判定の主軸は §4.3 の実測と V1〜V5 |
| 素材集の作りがばらつく（グループ化されていない、名前が無い） | 自動抽出 + LLM 補完 + `asset-manifest.yaml` による上書き。抽出結果をレビューできる `analyze-assets` CLI を用意 |
| パッケージ間取り込みでのリレーション破損 | V1/V3 を取り込み直後に実行。プロパティベーステストで任意の素材スライドの取り込み→検証を回す |
| 大規模変更による回帰 | フェーズごとに評価指標で比較、旧実装を Phase 5 までフラグで切り替え可能に保持 |
| LLM のコスト・遅延増（スロット単位の再生成） | 再生成は該当スロットのみ、回数上限 2。スライド単位で並列実行 |
| XSD のライセンス・入手性 | ECMA-376 の配布 XSD を使用（ECMA は無償公開）。リポジトリへの同梱可否を確認し、不可ならダウンロードスクリプトにする |

---

## 8. 確認したい事項（未決定）

1. **素材集の実体**: 想定している素材集は「パターンスライドを並べた .pptx」か「画像・アイコンのフォルダ」か、あるいは両方か。サンプルがあれば Phase 0 の評価セットに使いたい。
2. **対象テンプレート**: 実運用で使う社内テンプレートのレイアウト名は日本語か。プレースホルダーにカスタムプロンプト文言が入っているか。
3. **LibreOffice の利用可否**: 本番／CI 環境で LibreOffice を使えるか（V6 レンダリング QA の可否）。
4. **フォント**: 指定テンプレートで使用しているフォントと、そのフォントファイルを実行環境に置けるか。
5. **後方互換**: `--manifest` 形式や `TemplateManifest` を利用している外部システムがあるか（廃止時期の判断）。
6. **Strict 形式**: ISO/IEC 29500 Strict での出力が要件か（現計画は Transitional 出力のみ。Strict 形式のテンプレート入力は対象外）。
