# デプロイ手順（完全無料構成: Render + Neon）

このプロジェクトは無料でインターネット公開できます（`render.yaml` 同梱）。

| 役割 | サービス | 費用 | 制限 |
|---|---|---|---|
| API + 画面 | [Render](https://render.com/)（無料プラン） | 0円 | 15分アクセスがないとスリープ。次のアクセスで起動に**約1分**かかる |
| データベース | [Neon](https://neon.tech/)（無料プラン） | 0円 | 容量0.5GBまで（日報用途なら数年分）。**期限なし・データは消えない** |

> Renderの無料PostgreSQLは**約1か月で削除される**ため使いません。DBだけNeonを使うのがポイントです。
> 機微情報を本格運用する段階になったら、有料化（API月$7で常時稼働）や国内リージョン（Google Cloud Run 東京）への移行も可能です。

## 事前に必要なもの（無料登録）

1. **GitHubアカウント** … https://github.com
2. **Renderアカウント** … https://render.com （GitHubアカウントでそのまま登録可）
3. **Neonアカウント** … https://neon.tech （GitHub/Googleアカウントで登録可）
4. （任意）Gemini APIキー … https://aistudio.google.com/

## 手順（約20分）

### 1. GitHubへコードをアップロード

ローカルのGit初期化・コミットは済んでいます。GitHubで空のリポジトリ（**Private推奨**）を作成し:

```powershell
cd C:\Users\DX15B\Desktop\利用者AI
git remote add origin https://github.com/＜あなたのユーザー名＞/becolorful-ai.git
git push -u origin main
```

### 2. NeonでデータベースURLを取得

1. Neonにログイン →「Create project」（プロジェクト名: becolorful など。リージョンは Asia Pacific (Singapore) 推奨）
2. 作成直後の画面に表示される **Connection string** をコピー
   （`postgresql://ユーザー:パスワード@xxx.neon.tech/neondb?sslmode=require` の形式）
3. これを手順3-4で使うのでメモしておく

### 3. RenderでBlueprintデプロイ

1. Renderにログイン →「New +」→「**Blueprint**」
2. GitHubリポジトリ「becolorful-ai」を接続して選択
3. becolorful-api / becolorful-app の2サービスが表示される
4. 環境変数の入力欄で以下を入力:
   - `DATABASE_URL` … 手順2でコピーしたNeonの接続文字列
   - `ADMIN_EMAIL` … 最初の管理者のメールアドレス（例: dxso@be-colorful.school）
   - `ADMIN_PASSWORD` … 管理者パスワード（8文字以上、推測されにくいもの）
   - `GEMINI_API_KEY` … 空のままでOK（モックAIで動作。後から設定可能）
5. 「Apply」→ 初回デプロイは5〜10分待つ

### 4. 動作確認

- 画面: `https://becolorful-app.onrender.com`
- APIドキュメント: `https://becolorful-api.onrender.com/docs`
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` でログイン → 「アカウント管理」からスタッフ・利用者を登録

> 本番はデモデータなしで始まります。初期管理者はDBが空のときだけ自動作成されます。
> スリープ後の初回アクセスは約1分かかります（画面が出るまで待ってください）。これが無料プランの唯一の不便です。

### 5. Gemini AIへの切り替え（任意）

Renderダッシュボード → becolorful-api → Environment で
`GEMINI_API_KEY` にキーを入力し、`AI_PROVIDER` を `gemini` に変更（自動で再起動されます）。
Gemini APIにも無料枠があるため、AIも無料で使えます。

### 6. 以後の更新

コードを変更して `git push` するだけで自動再デプロイされます。

## 無料プランの制限まとめ

- **スリープ**: 15分アクセスなしでAPIが停止 → 次のアクセスで約1分の起動待ち（データは消えません）
- **DB容量**: Neon無料枠は0.5GB（テキスト中心の日報なら長期間問題なし）
- 朝の始業前に誰かが一度アクセスしておくと、その後は快適に使えます

## 後から有料化する場合（月約$7〜）

`render.yaml` の becolorful-api の `plan: free` を `plan: starter` に変えて push するだけで常時稼働になります。DBはNeonのまま無料で継続できます。

## トラブルシューティング

- **APIが起動しない** → becolorful-api の「Logs」を確認。多くは `DATABASE_URL` の貼り間違い（Neonの接続文字列を丸ごと貼る）
- **管理者でログインできない** → ADMIN_EMAIL/ADMIN_PASSWORD は「DBが空の時」だけ有効。Neonのダッシュボードでテーブルを空にしてから再デプロイすると再作成されます
- **画面は出るがAPIエラー** → `CORS_ORIGINS` がフロントエンドのURL（https://becolorful-app.onrender.com）と一致しているか確認
