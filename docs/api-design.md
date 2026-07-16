# API設計

ベースURL: `/api`。全エンドポイントはログイン以外JWT必須（`Authorization: Bearer <token>`）。
OpenAPIドキュメント: `http://localhost:8000/docs`

## 権限表記

- **A** = admin、**S** = staff、**U** = user（本人のみ）
- スタッフは担当利用者（profiles.assigned_staff_id が自分）のみアクセス可
- 利用者は自分のデータのみアクセス可（他利用者は404/403）

## エンドポイント一覧

### 認証
| メソッド | パス | 権限 | 説明 |
|---|---|---|---|
| POST | /api/auth/login | 公開 | email+password → access/refresh トークン |
| GET | /api/auth/me | A/S/U | 自分の情報+プロフィール |
| POST | /api/auth/refresh | 公開 | refresh_token → 新しい access_token |

### 利用者・アカウント
| POST/GET | /api/users | A（GETはSも=担当利用者のみ） | 一覧・作成（作成はロール指定可） |
| GET/PATCH | /api/users/{id} | A / S(担当) / U(本人) | 詳細・更新（ロール変更・有効化はAのみ） |

### 利用者日報
| GET | /api/users/{id}/daily-reports?from&to&limit | A/S(担当)/U(本人) | 一覧（日付降順） |
| POST | /api/users/{id}/daily-reports | U(本人) | 作成（同日既存時は409を返しフロントで更新確認） |
| GET | /api/users/{id}/daily-reports/{report_id} | A/S(担当)/U(本人) | 詳細 |
| PATCH | /api/users/{id}/daily-reports/{report_id} | U(本人) | 更新・下書き確定 |

### スタッフ日報
| GET | /api/users/{id}/staff-reports | A/S(担当) | 一覧 |
| POST | /api/users/{id}/staff-reports | S(担当)/A | 作成（urgency=urgent でリスクアラート自動生成） |
| PATCH | /api/users/{id}/staff-reports/{report_id} | S(記録者)/A | 更新 |

### スコア
| GET | /api/users/{id}/scores?from&to | A/S(担当)/U(本人) | スコア推移 |
| POST | /api/users/{id}/scores/recalculate | A/S(担当) | 期間再計算 |

### AI分析
| GET | /api/users/{id}/ai-analyses | A/S(担当)/U(本人※) | 一覧 ※利用者はuser_recommendations等本人向け項目のみ |
| POST | /api/users/{id}/ai-analyses | A/S(担当) | 分析実行（body: analysis_type, period） |
| GET | /api/users/{id}/ai-analyses/{analysis_id} | 同上 | 詳細 |

### 個別支援計画
| GET | /api/users/{id}/support-plans | A/S(担当)/U(本人=承認済みのみ) | 一覧 |
| POST | /api/users/{id}/support-plans/generate | S(担当)/A | AI下書き生成 |
| POST | /api/users/{id}/support-plans | S(担当)/A | 手動作成 |
| PATCH | /api/support-plans/{plan_id} | S(担当)/A | 編集（編集毎にバージョン保存） |
| POST | /api/support-plans/{plan_id}/approve | S(担当)/A | 承認（approved_by/at 記録） |
| GET | /api/support-plans/{plan_id}/versions | S(担当)/A | 変更履歴 |

### 支援実施記録（効果測定）
| GET/POST | /api/users/{id}/support-actions | S(担当)/A | 実施記録・効果スコア |

### 目標
| GET/POST | /api/users/{id}/goals | A/S(担当)/U(本人) | 一覧・作成 |
| PATCH | /api/goals/{goal_id} | 本人/S(担当)/A | 進捗・状態更新 |

### リスク
| GET | /api/risk-alerts?status= | A(全件)/S(担当分) | 一覧 |
| POST | /api/risk-alerts/{id}/acknowledge | A/S(担当) | 確認済み化（確認者・日時保存） |

### ダッシュボード
| GET | /api/dashboard/admin | A | 事業所全体サマリ（利用者数・入力率・未確認アラート・至急日報等） |
| GET | /api/dashboard/staff | S | 担当利用者サマリ+アラート+至急表示 |
| GET | /api/dashboard/user | U | 本人スコア・グラフ・今日の提案 |
| GET | /api/users/{id}/dashboard | A/S(担当) | 特定利用者のダッシュボードデータ |

### 監査ログ・設定
| GET | /api/audit-logs?actor&action&from&to | A | 監査ログ |
| GET/PUT | /api/settings/scoring-weights | A | スコア配点の閲覧・変更 |

## エラー形式

```json
{ "detail": "日本語のエラーメッセージ" }
```

- 401: 未認証 / トークン失効
- 403: 権限なし（画面側は権限エラー画面へ）
- 404: 対象なし（他人のリソースも404で存在を秘匿）
- 409: 同一日の日報が既に存在
- 422: 入力検証エラー（フィールド別詳細）

## AI分析結果 JSONスキーマ（result_json）

```json
{
  "summary": "string",
  "strengths": ["string"],
  "concerns": ["string"],
  "trend_analysis": "string",
  "maslow_analysis": "string",
  "adler_analysis": "string",
  "perma_analysis": "string",
  "abc_analysis": "string",
  "choice_theory_analysis": "string",
  "behavioral_economics_analysis": "string",
  "staff_recommendations": [
    {"title": "", "reason": "", "action": "", "priority": "low|medium|high",
     "observed_facts": [""], "hypothesis": "", "questions": [""], "avoid": "", "next_check_date": ""}
  ],
  "user_recommendations": [
    {"title": "", "reason": "", "action": "", "amount": "", "alternative": ""}
  ],
  "questions_for_staff": ["string"],
  "risk_flags": [{"type": "", "detail": ""}],
  "confidence": 0.0,
  "data_limitations": ["string"]
}
```

- Pydanticで検証。不正JSONは最大2回再試行し、失敗時は `status=fallback` で安全な固定文+ルールベース情報を返す
- user_recommendations は最大3件に制限
