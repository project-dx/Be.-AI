# Be.カラフル Well-being個別支援AI（仮称）

利用者が入力する日報とスタッフが入力する支援記録をAIが分析し、生活状態の見える化・スコア算出・支援提案・個別支援計画の下書き生成を行う、福祉事業所（就労移行支援・就労継続支援・生活訓練など）向けWebシステムです。

> ⚠️ **本システムは医療診断システムではありません。**
> AIの出力はすべて「支援判断を補助する参考情報」であり、スタッフの判断を代替するものではありません。リスク検知はルールベースの自動判定であり誤検知の可能性があるため、必ずスタッフによる確認を前提としています。外部への自動通報は行いません。

## 主な機能

| 機能 | 概要 |
|---|---|
| 利用者日報 | 気分・睡眠・食事・運動・ストレス等を毎日3分で入力。下書き保存対応 |
| スタッフ日報 | 支援記録・緊急度（至急はダッシュボードへ強調表示+アラート化） |
| スコア算出 | 生活リズム / 睡眠 / メンタル / 幸福度(PERMA) / 自己効力感 / 就労準備度（0〜100点、再現可能なルールベース計算） |
| AI分析 | マズロー・アドラー・PERMA・ABC分析・選択理論・行動経済学の6理論に基づく分析。事実と仮説を分離して表示 |
| 提案生成 | スタッフ向け提案・利用者向け提案（今日実行できる小さな行動、最大3件） |
| 個別支援計画 | AIによる下書き生成 → スタッフ編集 → 承認のワークフロー。変更履歴を保存 |
| 支援履歴・効果測定 | 支援実施記録と効果スコア（1〜5）の記録 |
| リスク検知 | ルールベース判定（ストレス連続・睡眠不足・日報途切れ等）。確認者・確認日時を記録 |
| ダッシュボード | 管理者 / スタッフ / 利用者のロール別。グラフ・空状態・スマートフォン対応 |
| 監査ログ | ログイン・データ変更等の操作履歴（管理者のみ閲覧可） |

## 技術構成

- **フロントエンド**: React 19 + TypeScript + Vite + Tailwind CSS v4 + React Router + Recharts + React Hook Form + Zod + Axios（テスト: Vitest + React Testing Library）
- **バックエンド**: Python 3.12 + FastAPI + SQLAlchemy 2.x + Pydantic v2 + Alembic（テスト: pytest）
- **データベース**: 開発 SQLite / 本番 PostgreSQL（`DATABASE_URL` で切替）
- **AI**: Google Gemini API（`AI_PROVIDER=gemini`）/ モックAI（`AI_PROVIDER=mock`、APIキー不要）
- **認証**: JWT（アクセス60分+リフレッシュ7日）、bcryptハッシュ、admin / staff / user の3ロールRBAC
- **パッケージ管理**: uv（Python）、npm（Node.js）

設計ドキュメントは [docs/](docs/) にあります（実装計画・DB設計・API設計・スコア計算仕様）。

## 必要環境

- **uv**（Pythonとパッケージを自動管理。Pythonの個別インストールは不要）
  - Windows: `winget install astral-sh.uv` または `irm https://astral.sh/uv/install.ps1 | iex`
- **Node.js 20以上** + npm
- （任意）Docker / Docker Compose

## 環境変数

`.env.example` を `backend/.env` へコピーして編集します。

```powershell
# Windows PowerShell
Copy-Item .env.example backend\.env
```

```bash
# macOS / Linux
cp .env.example backend/.env
```

| 変数 | 説明 | 既定値 |
|---|---|---|
| ENVIRONMENT | development / production | development |
| DATABASE_URL | DB接続文字列（SQLite / PostgreSQL） | sqlite:///./becolorful.db |
| SECRET_KEY | JWT署名鍵（**本番では必ず変更**） | 開発用の値 |
| AI_PROVIDER | mock / gemini | mock |
| GEMINI_API_KEY | Gemini APIキー（コードへ直接書かない） | 空 |
| GEMINI_MODEL | 使用モデル | gemini-2.0-flash |
| CORS_ORIGINS | 許可オリジン（カンマ区切り） | localhost:5173 |

## バックエンドの起動（uv）

```powershell
# Windows PowerShell / macOS / Linux 共通
cd backend
uv sync                            # 依存関係の同期（初回はPython 3.12も自動取得）
uv run alembic upgrade head        # マイグレーション適用
uv run python -m app.seed          # デモデータ投入（本番では無効）
uv run uvicorn app.main:app --reload   # http://localhost:8000 で起動
```

- OpenAPIドキュメント: http://localhost:8000/docs

## フロントエンドの起動

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173 で起動（/api は 8000 へプロキシ）
```

## デモアカウント

`uv run python -m app.seed` 投入後に使用できます。

| ロール | メールアドレス | パスワード | 内容 |
|---|---|---|---|
| 管理者 | admin@example.com | Admin123! | 全体管理・監査ログ・設定 |
| スタッフ | staff@example.com | Staff123! | 3名の利用者を担当 |
| 利用者1 | user1@example.com | User123! | 正常傾向のデータ20日分 |
| 利用者2 | user2@example.com | User123! | 睡眠低下傾向（AI下書き支援計画あり） |
| 利用者3 | user3@example.com | User123! | ストレス上昇傾向（リスクアラート・至急記録あり） |

> 本番環境（`ENVIRONMENT=production`）ではシードスクリプトは `--force` を付けない限り実行されず、デモアカウントは作成されません。

## テスト

```powershell
# バックエンド（84テスト: 認証・権限・日報CRUD・スコア境界値・AIモック・支援計画・リスク検知・データ分離）
cd backend
uv run pytest

# フロントエンド（フォーム検証・ロール別表示・空状態・主要コンポーネント）
cd frontend
npm test

# lint / 型チェック / ビルド
npm run lint
npm run build
```

## Gemini APIの設定 / モックAIへの切り替え

1. [Google AI Studio](https://aistudio.google.com/) でAPIキーを取得
2. `backend/.env` に設定:
   ```
   AI_PROVIDER=gemini
   GEMINI_API_KEY=（取得したキー）
   ```
3. バックエンドを再起動

- モックAIへ戻す場合は `AI_PROVIDER=mock` にします。
- **APIキーが未設定の場合は自動的にモックAIで動作**するため、キーなしでも全機能を確認できます。
- Gemini呼び出しが失敗した場合や不正なJSONが返り続けた場合は、自動的にルールベースのフォールバック結果（`status=fallback`）を返します。

## Dockerでの起動

```powershell
Copy-Item .env.example .env
# .env の SECRET_KEY を変更してから:
docker compose up --build
```

- フロントエンド: http://localhost:8080 ／ バックエンドAPI: http://localhost:8000
- PostgreSQL 16 を使用し、起動時にマイグレーションが自動適用されます。
- デモデータが必要な場合: `docker compose exec backend uv run python -m app.seed`

## マイグレーション

```powershell
cd backend
uv run alembic upgrade head                            # 適用
uv run alembic revision --autogenerate -m "説明"       # モデル変更後の生成
uv run alembic downgrade -1                            # 1つ戻す
```

## デプロイ（公開サーバーでの運用）

Render への一括デプロイに対応しています（`render.yaml` 同梱）。
手順は **[docs/deploy.md](docs/deploy.md)** を参照してください（GitHubへpush → RenderでBlueprint選択 → 環境変数入力のみ）。

- 初期管理者は環境変数 `ADMIN_EMAIL` / `ADMIN_PASSWORD` で自動作成されます（DBが空の場合のみ）
- `DATABASE_URL` は `postgres://` 形式でも自動で `postgresql+psycopg://` に正規化されます

## 本番環境で必要な設定

- `ENVIRONMENT=production` を設定（デモシードの無効化）
- `SECRET_KEY` を32文字以上のランダム値へ変更
- `DATABASE_URL` をPostgreSQLへ変更
- `CORS_ORIGINS` を本番ドメインのみに限定
- **HTTPS前提**（リバースプロキシ等でTLS終端すること）
- デモアカウントを作成しない（シードを実行しない）

## スコア計算について

スコアはAIではなく再現可能なルールベースで計算されます（AIは解釈・提案のみを担当）。
計算式・配点は [docs/scoring-rules.md](docs/scoring-rules.md) を参照してください。
配点は管理者の「設定」画面から変更できます（`system_settings` に保存、次回計算から反映）。

## 既知の制限

- 本開発環境にDockerが無いため、`docker-compose.yml` / Dockerfile は**実行未検証**です（構成はベストプラクティスに準拠）
- Gemini API連携は実APIキーでの疎通テストを行っていません（モックとフォールバック経路はテスト済み）
- PERMA（幸福度）は専用設問がないため日報項目からの暫定マッピングです（docs/scoring-rules.md 参照）
- 「予定実行」の指標は「明日の目標」記入率を代理指標としています
- 危険表現の検知はキーワード方式のため誤検知・見逃しがあります。**必ずスタッフによる確認を行ってください**
- パスワードリセット（メール送信）機能は未実装です（管理者がアカウント管理画面から変更可能）

## 免責

本システムは医療診断を行うものではありません。AIの分析・提案・リスク検知はすべて参考情報であり、支援に関する最終判断は必ず資格を持つ支援スタッフが行ってください。
