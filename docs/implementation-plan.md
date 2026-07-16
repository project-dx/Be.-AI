# Be.カラフル Well-being個別支援AI 実装計画

作成日: 2026-07-16

## 1. 事前調査の結果

| 項目 | 結果 |
|---|---|
| 既存プロジェクト | **なし**（`image.png` の参考画像1点のみの新規プロジェクト） |
| 既存技術構成 | なし → 仕様書の推奨技術構成をそのまま採用 |
| 既存機能・壊れる恐れのある箇所 | なし |
| Node.js | v24.18.0 / npm 11.16.0（導入済み） |
| Python | 未導入（Windows Storeスタブのみ）→ **uvがPython 3.12を自動管理** |
| uv | v0.11.28 を winget で導入済み |
| Docker | 未確認（フェーズ8で確認。未導入の場合は構成ファイルのみ提供し既知の制限に記載） |

参考画像（image.png）から反映するデザイン要素:
- 白基調 + 緑メイン、青・オレンジ・ピンク・紫の補助色によるカードUI
- スコアカード（生活リズム78点等の大きな数字 + アイコン + 色分け）
- 折れ線（睡眠・ストレス）、棒（幸福度）、ドーナツ（達成率）グラフ
- 「AIからスタッフへの提案」「AIから利用者への提案」「個別支援計画」のカード構成

## 2. 技術構成（確定）

- **フロントエンド**: React 18 + TypeScript + Vite + Tailwind CSS v4 + React Router + Recharts + React Hook Form + Zod + Axios / Vitest + React Testing Library
- **バックエンド**: Python 3.12 + FastAPI + SQLAlchemy 2.x + Pydantic v2 + Alembic + uv + pytest
- **DB**: 開発 SQLite / 本番 PostgreSQL 切替（`DATABASE_URL` 環境変数のみで切替）
- **AI**: `AI_PROVIDER=mock|gemini`。Gemini は REST API（httpx）で呼び出し、サービス層 `services/ai/` に分離。プロバイダ差替可能な抽象基底クラス方式
- **認証**: JWT（PyJWT）+ bcrypt ハッシュ、admin / staff / user の3ロールRBAC
- **その他**: Docker / docker-compose 対応、.env.example、日本語README、PowerShell対応

## 3. ディレクトリ構成

```
project-root/
├─ frontend/            # React + Vite + TS
│  └─ src/{components, pages, layouts, hooks, services, types, schemas, stores, utils}
├─ backend/
│  ├─ app/{main.py, core, models, schemas, api, services, repositories, prompts, utils}
│  ├─ tests/
│  ├─ alembic/
│  └─ pyproject.toml
├─ docs/                # 設計ドキュメント（本ファイル等）
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## 4. 作成予定ファイル一覧（主要）

### バックエンド
| ファイル | 内容 |
|---|---|
| `app/main.py` | FastAPIアプリ、CORS、ルーター登録、例外ハンドラ |
| `app/core/config.py` | pydantic-settings による環境変数管理 |
| `app/core/database.py` | エンジン・セッション・Base |
| `app/core/security.py` | bcryptハッシュ / JWT発行・検証 |
| `app/core/deps.py` | 認証・RBAC依存関係（get_current_user 等） |
| `app/models/*.py` | users, profiles, user_daily_reports, staff_daily_reports, score_results, ai_analyses, support_plans, support_plan_versions, support_actions, goals, risk_alerts, audit_logs, system_settings |
| `app/schemas/*.py` | Pydanticスキーマ（入出力・AI結果スキーマ） |
| `app/api/*.py` | auth, users, daily_reports, staff_reports, scores, ai_analyses, support_plans, goals, risks, dashboard, audit_logs, settings |
| `app/services/scoring.py` | ルールベーススコア計算（docs/scoring-rules.md 準拠） |
| `app/services/risk.py` | ルールベースリスク検知 |
| `app/services/audit.py` | 監査ログ記録 |
| `app/services/ai/{base,mock,gemini,factory}.py` | AI抽象化・モック・Gemini |
| `app/prompts/*.md` | プロンプト5種（バージョン付き） |
| `app/seed.py` | デモデータ投入（本番では無効） |
| `alembic/` | マイグレーション |
| `tests/*.py` | 認証・権限・CRUD・スコア境界値・AIモック・支援計画・リスク・データ分離 |

### フロントエンド
| ファイル | 内容 |
|---|---|
| `src/services/api.ts` | Axiosクライアント（JWT付与・401処理） |
| `src/stores/AuthContext.tsx` | 認証状態・ロール管理 |
| `src/layouts/AppLayout.tsx` | ロール別サイドバー/ヘッダー（レスポンシブ） |
| `src/components/` | ScoreCard, TrendChart, EmptyState, RiskBanner, RecommendationCard ほか |
| `src/pages/` | Login, AdminDashboard, StaffDashboard, UserDashboard, UsersList, UserDetail, DailyReportForm, StaffReportForm, AiAnalysisPage, SupportPlanPage, SupportHistory, GoalsPage, SettingsPage, AccountsPage, AuditLogsPage, ErrorPage, ForbiddenPage |
| `src/schemas/*.ts` | Zodフォームスキーマ（日本語エラー） |
| `src/types/*.ts` | API型定義 |

## 5. 実装フェーズと優先順位

1. **フェーズ1 調査・設計**（本ドキュメント + DB/API/スコア設計）
2. **フェーズ2 基盤**: 雛形、DB、Alembic、JWT認証、RBAC、レイアウト
3. **フェーズ3 日報**: 利用者/スタッフ日報CRUD + フォーム + 下書き
4. **フェーズ4 スコア**: ルールベース計算 + グラフ + 境界値テスト
5. **フェーズ5 AI**: 抽象化、モック、Gemini、スキーマ検証、再試行、フォールバック
6. **フェーズ6 支援計画**: 下書き生成、編集、承認、バージョン、支援履歴、効果測定
7. **フェーズ7 ダッシュボード**: 3ロール別 + グラフ + 空状態 + レスポンシブ
8. **フェーズ8 品質**: テスト、lint、型、build、セキュリティ、README、Docker

## 6. 合理的な仮設定（仕様にない部分の判断）

| # | 項目 | 仮設定 | 理由 |
|---|---|---|---|
| 1 | Python環境 | uv管理のPython 3.12 | システムPython不在のため |
| 2 | パスワードハッシュ | bcrypt | 実績・Windowsホイールの安定性 |
| 3 | JWT | アクセストークン60分 + リフレッシュ7日 | 福祉現場の利用実態と安全性のバランス |
| 4 | Gemini呼び出し | REST API（httpx） | SDK依存を減らし差替を容易にするため |
| 5 | Geminiモデル | `gemini-2.0-flash`（環境変数で変更可） | コストと速度のバランス |
| 6 | PERMAの算出元 | 日報項目からのマッピング（scoring-rules.md参照） | 専用設問がないため暫定マッピング |
| 7 | スコア計算対象期間 | 直近7日（安定性系は要2日以上） | 仕様の初期ルール例に準拠 |
| 8 | 「予定実行」の代理指標 | 「明日の目標」記入率 | 予定実行の直接データがないため |
| 9 | 危険表現検知 | キーワードリスト方式（誤検知前提で「要スタッフ確認」表示） | 仕様15章の指示どおり断定しない |
| 10 | スコア配点の変更 | system_settings にJSONで保存し管理画面から編集可能 | 仕様10章「将来変更できる設計」 |
| 11 | 日報の一意性 | (user_id, report_date) にDB一意制約。既存日はフロントで更新確認 | 仕様7章 |
| 12 | Tailwind | v4（@tailwindcss/vite） | 設定ファイル削減・現行推奨 |
| 13 | デモアカウントのメール | admin@example.com / staff@example.com / user1@example.com ほか | READMEに記載 |
| 14 | シード実行の本番ガード | `ENVIRONMENT=production` で `--force` なしのシードを拒否 | 仕様22章 |

## 7. リスク・注意点

- Docker が本環境に無い場合、compose 構成の動作確認は不可 → README の既知の制限に明記
- Gemini API キー無しでも全機能がモックで動作することを完了条件とする
- AI出力は参考情報であり医療診断ではない旨を全AI表示画面に常時表示する
