# 引き継ぎ書（運用メモ）

最終更新: 2026-07-22

## 状況: 🎉 本番公開完了

| 項目 | 状態 |
|---|---|
| システム開発（全機能・17画面・テスト108件） | ✅ 完成 |
| GitHubへの公開 | ✅ https://github.com/project-dx/Be.-AI |
| Neonで無料データベース作成 | ✅ 完了（プロジェクト名 becolorful / Singapore） |
| Renderでアプリ公開 | ✅ 完了 |
| UptimeRobotでスリープ対策 | ✅ 完了（/api/health を5分間隔で監視） |
| デザイン刷新（温かい紙の質感+ブランドカラー） | ✅ 完了 |
| ダミーデータ投入（利用者3名・日報/支援記録 各60件） | ✅ 完了 |

## 本番環境

- **アプリURL**: https://becolorful-app.onrender.com
- **API**: https://becolorful-api.onrender.com （ヘルスチェック: /api/health）
- **DB**: Neon PostgreSQL（console.neon.tech / project-DX / becolorful）
- **監視**: UptimeRobot（dashboard.uptimerobot.com）

### アカウント

- 管理者: `dxso@be-colorful.school`（パスワードは管理者が別途保管）
- スタッフ（ダミー・パスワードは全員 `Staff123!`）:
  - 田中 誠 `staff.suzuki@example.com` → 鈴木一郎 担当
  - 高橋 沙織 `staff.sato@example.com` → 佐藤花子 担当
  - 伊藤 健 `staff.yamada@example.com` → 山田太郎 担当
- 利用者（ダミー・パスワードは全員 `User123!`）:
  - 鈴木 一郎 `imported.user3@example.com`
  - 佐藤 花子 `imported.user1@example.com`
  - 山田 太郎 `imported.user2@example.com`

## 運用メモ

- **デプロイ**: GitHubへpushしただけでは反映されません（Public Git Repository接続のため自動デプロイ無効）。
  Renderダッシュボード → 各サービス →「Manual Deploy」→「Deploy latest commit」を実行すること。
  becolorful-app（フロント）と becolorful-api（API）の両方を忘れずに。
- **Excelダミーデータの再投入**: `backend/app/seed_from_excel.py` を参照。
  `DATABASE_URL=... uv run python -m app.seed_from_excel --user-report <xlsx> --staff-report <xlsx> --force`
- **担当スタッフの割り当て**: `backend/app/assign_dedicated_staff.py`
- **Neon接続の注意**: サーバーレスDBのため非アクティブ時に接続が切れる。
  `pool_pre_ping` 対応済み（app/core/database.py）。

## 未決事項・今後の候補

- Gemini APIキーの設定（実AIへの切り替え）→ 取得後、Renderの `GEMINI_API_KEY` と `AI_PROVIDER=gemini` を設定
- RenderのGitHubアカウント連携（push時の自動デプロイを有効化）
- 数週間の無料運用後、不便なら有料化（render.yaml の `plan: free` → `plan: starter`、月$7）
- GitHubリポジトリは Private 推奨（現状Public。Private化するとRenderの再接続が必要）
- 本番運用開始時はダミーアカウントを削除し、実際のスタッフ・利用者を「アカウント管理」から登録
