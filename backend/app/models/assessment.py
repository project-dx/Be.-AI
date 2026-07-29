"""初期アセスメント・カラフルピラミッド・モニタリング評価。

「データ駆動型の個別支援サイクル」を構成する3要素:
  多角的な初期アセスメント → 日々の記録の集約 → 6か月ごとの継続モニタリング
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utcnow


class Assessment(Base):
    """多角的な初期アセスメント（利用者1名につき1件・更新していく）"""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)

    life_history: Mapped[str | None] = mapped_column(Text)  # 生育歴
    disability_characteristics: Mapped[str | None] = mapped_column(Text)  # 障害特性
    thinking_style: Mapped[str | None] = mapped_column(Text)  # 思考特性の所見（ハーマンモデル）
    # ハーマンモデルの4象限（各0〜100。本人の傾向を把握する目安であり優劣ではない）
    herrmann_a: Mapped[int | None] = mapped_column(Integer)  # A: 論理・分析
    herrmann_b: Mapped[int | None] = mapped_column(Integer)  # B: 堅実・計画
    herrmann_c: Mapped[int | None] = mapped_column(Integer)  # C: 感情・対人
    herrmann_d: Mapped[int | None] = mapped_column(Integer)  # D: 創造・全体
    personal_values: Mapped[str | None] = mapped_column(Text)  # 価値観
    strengths: Mapped[str | None] = mapped_column(Text)  # 強み・得意なこと
    support_needs: Mapped[str | None] = mapped_column(Text)  # 必要な配慮・支援
    notes: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ColorfulPyramid(Base):
    """カラフルピラミッド（ウェルビーイング→パッション→ビジョン→ミッション）"""

    __tablename__ = "colorful_pyramids"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)

    wellbeing: Mapped[str | None] = mapped_column(Text)  # 土台: どんなときに幸せを感じるか
    passion: Mapped[str | None] = mapped_column(Text)  # 情熱・好きなこと
    vision: Mapped[str | None] = mapped_column(Text)  # なりたい姿
    mission: Mapped[str | None] = mapped_column(Text)  # 果たしたい役割

    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class MonitoringEvaluation(Base):
    """6か月ごとの継続モニタリング評価（支援計画の振り返りと調整）"""

    __tablename__ = "monitoring_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    support_plan_id: Mapped[int | None] = mapped_column(ForeignKey("support_plans.id"), index=True)
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    score_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # 期間のスコア推移（集計値）
    overall_evaluation: Mapped[str | None] = mapped_column(Text)  # 総合評価（1000文字以内・期間全体のまとめ）
    achievements: Mapped[str | None] = mapped_column(Text)  # 達成できたこと
    challenges: Mapped[str | None] = mapped_column(Text)  # 残された課題
    plan_adjustments: Mapped[str | None] = mapped_column(Text)  # 支援計画の調整内容
    next_period_focus: Mapped[str | None] = mapped_column(Text)  # 次期の重点
    staff_comment: Mapped[str | None] = mapped_column(Text)  # スタッフによる確認コメント

    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(50))

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
