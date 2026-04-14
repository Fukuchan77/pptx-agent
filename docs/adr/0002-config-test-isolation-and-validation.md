# ADR 0002: Config Test Isolation and Validation

## ステータス

Accepted

## コンテキスト

このリファクタリング以前、テストスイートには以下の重大な問題がありました：

1. **環境変数の漏洩**: テストがシェルの環境変数（例：`export LLM_PROVIDER=watsonx`）の影響を受け、非決定的な動作を引き起こしていた
2. **不明瞭なテスト設定**: テストでConfigインスタンスを作成する標準的な方法が存在しなかった
3. **脆弱なAPI鍵バリデーション**: 本番コードが「test-api-key」のような明らかにテスト用の値を使用できていた
4. **不十分なスレッドセーフティテスト**: 並行アクセス時のConfigの動作が検証されていなかった

これらの問題により、以下の状況が発生していました：

- 環境によってテスト結果が異なる
- CI/CDでは失敗するがローカルでは成功するテストがあり、デバッグが困難
- テスト用API鍵を本番環境に誤ってデプロイするリスク
- 並行アクセスパターンでの動作が不明

## 決定事項

3つのフェーズに分けてリファクタリングを実施しました：

### Phase 1: 環境変数の隔離

- [`ignore_env_file`](tests/conftest.py:11)フィクスチャを[`isolate_config_from_environment`](tests/conftest.py:49)に置き換え
- テストで設定関連の環境変数をすべて明示的にクリア
- `monkeypatch.delenv()`を使用して完全な隔離を保証
- `autouse=True`により全テストに自動適用

### Phase 2: テスト設定戦略

- 標準化されたConfig作成のために[`make_test_config()`](tests/conftest.py:103)フィクスチャファクトリーを作成
- 包括的なスレッドセーフティテストを追加
- 統合テスト用の[`.env.test.template`](.env.test.template)を作成
- 明確なテストガイドラインを含むドキュメントを更新

### Phase 3: API鍵バリデーション

- Configクラスに[`allow_test_keys`](src/pptx_agent/config.py:115)フィールドを追加（シリアライゼーションから除外）
- テストパターン（「test」、「dummy」、「fake」など）を拒否するバリデーションを実装
- `allow_test_keys=True`によりテストコードの後方互換性を維持
- すべてのフィクスチャを新しいバリデーションシステムを使用するよう更新

## 影響（Consequences）

### ポジティブな影響

- **決定的なテスト**: ホスト環境に関係なく、テストが同一の結果を生成
- **開発者体験の向上**: テストのための明確で文書化されたパターン
- **本番環境の安全性**: テスト用API鍵を本番環境で誤って使用できない
- **スレッドセーフティの検証**: 並行アクセスパターンがテストされ、正常に動作することを確認
- **保守性**: テスト設定への標準化されたアプローチ

### ネガティブな影響

- **テストの更新が必要**: 既存のテストを新しいフィクスチャを使用するよう更新する必要があった
- **追加の複雑性**: より洗練されたフィクスチャインフラストラクチャ
- **学習曲線**: 開発者が新しいテストパターンを理解する必要がある

### 中立的な影響

- **テスト数の増加**: 9つの新しいテスト（バリデーション、スレッドセーフティ、フィクスチャ動作）を追加
- **コードカバレッジ**: 91%以上のカバレッジを維持
- **パフォーマンス**: テスト実行時間への測定可能な影響なし

## 実装の詳細

### 変更されたファイル

**コア実装:**

- [`src/pptx_agent/config.py`](src/pptx_agent/config.py): バリデーションロジックと[`allow_test_keys`](src/pptx_agent/config.py:115)フィールドを追加

**テストインフラストラクチャ:**

- [`tests/conftest.py`](tests/conftest.py): 新しいフィクスチャ（[`isolate_config_from_environment`](tests/conftest.py:49)、[`make_test_config`](tests/conftest.py:103)）
- [`tests/integration/conftest.py`](tests/integration/conftest.py): 統合テスト固有のフィクスチャ
- [`tests/unit/agents/conftest.py`](tests/unit/agents/conftest.py): エージェント固有のフィクスチャ

**ドキュメント:**

- [`docs/developer-guide.md`](docs/developer-guide.md): 「Testing Configuration」セクションを追加
- [`.env.test.template`](.env.test.template): 統合テスト用テンプレート
- [`docs/adr/0002-config-test-isolation-and-validation.md`](docs/adr/0002-config-test-isolation-and-validation.md): このADR

**テスト:**

- 17のテストファイルを更新
- 9つの新しいテストを追加
- 合計870のテストが成功

### テストアプローチ

厳格なTDD（テスト駆動開発）に従いました：

1. RED: 失敗するテストを書く
2. GREEN: 最小限の解決策を実装
3. REFACTOR: コード品質を改善

すべてのフェーズで完全なテストカバレッジを維持して完了しました。

## 検討した代替案

### 代替案1: 環境変数のモックのみ

**却下理由**: テスト設定の標準化やAPI鍵バリデーションに対応できない

### 代替案2: 別のテスト用Configクラス

**却下理由**: メンテナンスの負担が増え、テストと本番の設定に乖離が生じる

### 代替案3: テストモードでバリデーションを無効化

**却下理由**: 潜在的なバリデーション問題を隠蔽する；我々のアプローチはより明示的

## 参照（References）

- 初期問題レポート: [`config_review_report.md`](.sdd/reviews/config_review_report.md)
- 詳細な実装計画: [`.sdd/steering/config-refactoring-plan.md`](.sdd/steering/config-refactoring-plan.md)
- テスト隔離パターン: pytest monkeypatch ドキュメント
- スレッドセーフティテスト: Python threading モジュールドキュメント

## 採用日

2026-04-14

## 著者

- AI Assistant (実装)
- Project Team (レビューと承認)
