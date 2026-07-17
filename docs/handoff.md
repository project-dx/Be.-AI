# 引き継ぎ書（別のPCで続きから作業するためのメモ）

最終更新: 2026-07-17

## いまどこまで終わっているか

| 項目 | 状態 |
|---|---|
| システム開発（全機能・17画面・テスト108件） | ✅ 完成 |
| 公式ロゴ反映・ログイン入力の保存ボタン | ✅ 完了 |
| GitHubへの公開 | ✅ 完了 → https://github.com/project-dx/Be.-AI |
| Neonで無料データベース作成 | ⬜ **ここから再開**（下記ステップ1） |
| Renderでアプリ公開 | ⬜ 未着手（ステップ2） |
| UptimeRobotでスリープ対策 | ⬜ 未着手（ステップ3） |

運用方針（決定済み）: **完全無料構成**（Render無料 + Neon無料DB + UptimeRobotで9〜18時の業務利用に対応）

## 残りの作業（どのPCのブラウザからでも可能）

コードやこのPCは不要です。ブラウザだけで完結します。

### ステップ1: Neonで無料データベースを作る（約5分）

1. https://neon.tech →「Sign up」→ **GitHubアカウント（project-dx）で登録**
2. 「Create project」→ 名前 `becolorful`、Region **Asia Pacific (Singapore)**
3. 表示される **Connection string**（`postgresql://...neon.tech/...` の長い文字列）をコピーして控える

### ステップ2: Renderでアプリを公開する（約10分）

1. https://render.com →「Get Started」→ **GitHubアカウントで登録**
2. 「New +」→「**Blueprint**」→ リポジトリ **project-dx/Be.-AI** を選択（出ない場合は Configure account でアクセス許可）
3. 環境変数を入力:
   - `DATABASE_URL` = ステップ1の接続文字列を丸ごと貼り付け
   - `ADMIN_EMAIL` = 最初の管理者のメールアドレス（例: dxso@be-colorful.school）
   - `ADMIN_PASSWORD` = 管理者パスワード（8文字以上）※忘れないよう控える
   - `GEMINI_API_KEY` = 空のままでOK（モックAIで動作）
4. 「Apply」→ 5〜10分待つ
5. https://becolorful-app.onrender.com を開き、ADMIN_EMAIL/ADMIN_PASSWORDでログイン確認

### ステップ3: UptimeRobotでスリープ対策（約5分）

1. https://uptimerobot.com で無料登録
2. 「+ New Monitor」→ Type: **HTTP(s)** / URL: `https://becolorful-api.onrender.com/api/health` / Interval: **5 minutes**
3. これで業務時間中（9〜18時）も眠らずサクサク動く

### 運用開始

管理者でログイン →「アカウント管理」からスタッフ・利用者を登録。
本番にはデモデータは入りません（デモアカウントも作成されません）。

## 別のPCで「開発」も続ける場合（コードをいじる場合のみ）

```powershell
# 1. 必要な道具を入れる
winget install astral-sh.uv          # Python環境（uv）
# Node.js 20以上を https://nodejs.org からインストール

# 2. コードを取得
git clone https://github.com/project-dx/Be.-AI.git
cd Be.-AI

# 3. 起動（詳細は README.md）
cd backend; uv sync; uv run alembic upgrade head; uv run python -m app.seed; uv run uvicorn app.main:app --reload
# 別ターミナルで:
cd frontend; npm install; npm run dev   # http://localhost:5173
```

ローカルのデモアカウントは README.md の「デモアカウント」参照。

## Claude Code（AI）に続きを頼む場合

別のPCでClaude Codeを開き、リポジトリをcloneしたフォルダで次のように伝えれば続きから進められます:

> 「docs/handoff.md を読んで、続きの作業を手伝ってください」

## 未決事項・今後の候補

- Gemini APIキーの設定（実AIへの切り替え）→ 取得後、Renderの環境変数に設定するだけ
- 数週間の無料運用後、不便なら有料化（render.yaml の `plan: free` → `plan: starter`、月$7）
- GitHubリポジトリは Private 推奨（現状の公開設定を要確認）
