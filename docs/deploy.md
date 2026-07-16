# デプロイ手順（Render）

このプロジェクトは [Render](https://render.com/) への一括デプロイに対応しています（`render.yaml` 同梱）。
DB（PostgreSQL）・バックエンドAPI・フロントエンドの3つが自動で作成されます。

## なぜRenderか

| 観点 | 内容 |
|---|---|
| 簡単さ | 設定ファイル同梱済み。アカウント作成後は画面のボタン操作のみ |
| 構成適合 | Docker（FastAPI）+ PostgreSQL + 静的サイトをすべて1か所で管理できる |
| HTTPS | 自動で有効化（証明書の管理不要） |
| 費用 | 無料枠で試用可能。常時稼働は月 約$13〜（API $7 + DB $6） |
| リージョン | シンガポール（日本から最も近い） |

> **機微情報の取り扱いについて**: 福祉利用者の個人情報を本格運用で扱う場合、国内リージョンを希望されるなら Google Cloud Run（東京）への移行も可能です（Dockerfile がそのまま使えます）。まずはRenderで運用を開始し、必要になったら移行する流れを推奨します。

## 事前に必要なもの（ご自身で作成が必要です）

1. **GitHubアカウント**（無料） … コードの置き場所
2. **Renderアカウント**（無料登録） … https://render.com/ ※GitHubアカウントでそのまま登録できます
3. （AI分析を本物にする場合）**Gemini APIキー** … https://aistudio.google.com/

## 手順

### 1. GitHubへコードをアップロード

ローカルのGit初期化・コミットは済んでいます。GitHubで空のリポジトリ（**Private推奨**）を作成し、以下を実行してください:

```powershell
cd C:\Users\DX15B\Desktop\利用者AI
git remote add origin https://github.com/＜あなたのユーザー名＞/becolorful-ai.git
git push -u origin main
```

### 2. RenderでBlueprintデプロイ

1. Renderにログイン → 右上の「New +」→「**Blueprint**」
2. GitHubリポジトリ「becolorful-ai」を接続して選択
3. サービス一覧（becolorful-db / becolorful-api / becolorful-app）が表示されるので確認
4. 環境変数の入力を求められたら:
   - `ADMIN_EMAIL` … 最初の管理者のメールアドレス（例: dxso@be-colorful.school）
   - `ADMIN_PASSWORD` … 管理者パスワード（8文字以上、推測されにくいもの）
   - `GEMINI_API_KEY` … 空のままでもOK（モックAIで動作）。後から設定可能
5. 「Apply」を押してデプロイ開始（初回は5〜10分かかります）

### 3. 動作確認

- フロントエンド: `https://becolorful-app.onrender.com`
- APIドキュメント: `https://becolorful-api.onrender.com/docs`
- 手順2-4で設定した `ADMIN_EMAIL` / `ADMIN_PASSWORD` でログイン
- 管理者の「アカウント管理」からスタッフ・利用者を登録して運用開始

> 本番はデモデータなしで始まります（`ENVIRONMENT=production` のため）。初期管理者はDBが空のときだけ自動作成されます。

### 4. Gemini AIへの切り替え（任意）

1. Renderダッシュボード → becolorful-api → Environment
2. `GEMINI_API_KEY` にキーを入力、`AI_PROVIDER` を `gemini` に変更 → 自動で再起動

### 5. 以後の更新

コードを変更したら `git push` するだけで自動再デプロイされます。

## 料金プランの目安

| プラン | 内容 | 用途 |
|---|---|---|
| 無料（free） | APIは15分無アクセスでスリープ（次回アクセスに約1分）。DBは**90日で削除**される | 動作確認・デモのみ |
| 有料（約$13/月） | API常時稼働（starter $7）+ DB（basic-256mb $6） | 実運用の最小構成 |

無料で試す場合は `render.yaml` の `plan: starter` を `plan: free`、DBの `plan` を `free` に変更してからpushしてください。**実運用では必ず有料DBを使用してください**（無料DBは90日で消えます）。

## トラブルシューティング

- **APIが起動しない** → becolorful-api の「Logs」を確認。`alembic upgrade head` の失敗が多い（DATABASE_URLの設定を確認）
- **画面は出るがログインできない** → CORS_ORIGINS がフロントエンドのURLと一致しているか確認
- **管理者でログインできない** → ADMIN_EMAIL/ADMIN_PASSWORD は「DBにユーザーが1人もいない時」だけ有効。DBを作り直すか、Renderのシェルから `uv run python -m app.seed --force`（デモデータ）も可

## 代替案（参考）

| 選択肢 | 向いているケース |
|---|---|
| Google Cloud Run + Cloud SQL（東京） | データを国内に置きたい / Google Workspaceと統一したい（設定はやや技術的） |
| さくらVPS / ConoHa + docker compose | 月額を最小化したい / 自前管理できる人がいる |
