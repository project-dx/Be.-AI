"""モックAI。APIキーなしでもアプリ全体を動作確認できる。

固定文ではなく、入力データ（睡眠・ストレス・成功体験・記録件数）に
応じて分岐した結果を返す。
"""

from typing import Any

from app.schemas.ai import (
    AiAnalysisResult,
    RiskFlag,
    StaffRecommendation,
    SupportPlanDraft,
    UserRecommendation,
)
from app.services.ai.base import AIService


class MockAIService(AIService):
    name = "mock"

    def analyze_daily(self, context: dict[str, Any]) -> AiAnalysisResult:
        stats = context.get("stats", {})
        report_count = context.get("report_count", 0)
        avg_sleep = stats.get("avg_sleep_recent")
        avg_sleep_prev = stats.get("avg_sleep_earlier")
        avg_stress = stats.get("avg_stress_recent")
        avg_mood = stats.get("avg_mood")
        success_days = stats.get("success_experience_days", 0)

        strengths: list[str] = []
        concerns: list[str] = []
        staff_recs: list[StaffRecommendation] = []
        user_recs: list[UserRecommendation] = []
        limitations: list[str] = []
        summary_parts: list[str] = []

        # 記録の継続
        if report_count >= 7:
            strengths.append(f"期間中{report_count}日分の日報入力を継続できています")
        if success_days >= 3:
            strengths.append(f"成功体験を{success_days}日分、具体的に記録できています")

        # 睡眠
        sleep_declining = (
            avg_sleep is not None and avg_sleep_prev is not None and avg_sleep_prev - avg_sleep >= 0.8
        )
        if avg_sleep is not None and avg_sleep < 6:
            concerns.append(f"直近の平均睡眠時間が{avg_sleep}時間と短めの傾向があります")
            summary_parts.append("睡眠時間の短縮傾向")
            staff_recs.append(
                StaffRecommendation(
                    title="睡眠状況の確認",
                    reason=f"直近の平均睡眠時間が{avg_sleep}時間と短い傾向があるため",
                    action="本人が負担を感じない形で、就寝前の過ごし方を確認する",
                    priority="medium",
                    observed_facts=[f"直近の平均睡眠時間: {avg_sleep}時間"]
                    + ([f"前半期間の平均: {avg_sleep_prev}時間"] if avg_sleep_prev else []),
                    hypothesis="就寝前の過ごし方や環境の変化が睡眠時間に影響している可能性があります",
                    questions=["夜、眠りにくいと感じることはありますか", "就寝前はどのように過ごしていますか"],
                    avoid="睡眠不足を責めるような聞き方は避ける",
                    next_check_date="3日後",
                )
            )
            user_recs.append(
                UserRecommendation(
                    title="就寝準備を10分早める",
                    reason="大きな変更より小さな一歩のほうが実行しやすいためです",
                    action="今日だけ、いつもより10分早くスマートフォンを充電場所へ置きましょう",
                    amount="今日1日だけ・10分",
                    alternative="難しい場合は、布団に入る時間を5分だけ早めてみましょう",
                )
            )
        elif sleep_declining:
            concerns.append(
                f"平均睡眠時間が{avg_sleep_prev}時間から{avg_sleep}時間へ短くなっている可能性があります"
            )
            summary_parts.append("睡眠時間の減少傾向")

        # ストレス
        if avg_stress is not None and avg_stress >= 3.5:
            concerns.append(f"ストレスの自己評価が平均{avg_stress}と高めの傾向があります")
            summary_parts.append("ストレスの上昇傾向")
            staff_recs.append(
                StaffRecommendation(
                    title="負担要因の確認",
                    reason=f"ストレス自己評価の平均が{avg_stress}と高めのため",
                    action="最近の作業量や人間関係で負担になっていることがないか、雑談の中で確認する",
                    priority="high" if avg_stress >= 4.2 else "medium",
                    observed_facts=[f"直近のストレス自己評価平均: {avg_stress}"],
                    hypothesis="作業内容または対人関係の変化が負担になっている可能性があります",
                    questions=["最近、疲れが取れにくいと感じることはありますか"],
                    avoid="原因を性急に特定しようとする質問の連続は避ける",
                    next_check_date="2日後",
                )
            )
            user_recs.append(
                UserRecommendation(
                    title="5分だけ休憩を先に決める",
                    reason="休憩のタイミングを先に決めておくと、負担をためこみにくくなるためです",
                    action="今日の作業の途中に「5分休む時間」を1回だけ決めておきましょう",
                    amount="1回・5分",
                    alternative="難しい場合は、深呼吸を3回するだけでも構いません",
                )
            )

        # 気分
        if avg_mood is not None and avg_mood <= 2.2:
            concerns.append(f"気分の自己評価が平均{avg_mood}と低めの傾向があります")
            summary_parts.append("気分の低下傾向")

        # 成功体験にもとづく提案
        if success_days > 0:
            user_recs.append(
                UserRecommendation(
                    title="今日できたことを1つだけ記録する",
                    reason="できたことの記録は自己効力感につながりやすいためです",
                    action="今日の日報に「できたこと」を1つだけ書きましょう",
                    amount="1つだけ",
                    alternative="思いつかない日は「日報を開いた」ことをできたことにして構いません",
                )
            )

        # データ量
        if report_count < 7:
            limitations.append(f"記録期間が{report_count}日分のため長期傾向は判断できません")
        if not context.get("staff_reports"):
            limitations.append("期間内のスタッフ記録がないため、支援場面の情報は反映されていません")

        if not summary_parts:
            summary_parts.append("大きな変化は見られず、安定した傾向")
        if not staff_recs:
            staff_recs.append(
                StaffRecommendation(
                    title="現状の維持と見守り",
                    reason="スコア・記録に大きな変化が見られないため",
                    action="現在の支援を継続し、本人の得意な活動を増やす機会を検討する",
                    priority="low",
                    observed_facts=[f"期間中の日報入力: {report_count}日分"],
                    hypothesis="現在の生活リズムが本人に合っている可能性があります",
                    questions=["最近、やってみたいことはありますか"],
                    avoid="変化がないことを問題として指摘することは避ける",
                    next_check_date="1週間後",
                )
            )
        if not user_recs:
            user_recs.append(
                UserRecommendation(
                    title="明日の最初の作業を1つメモする",
                    reason="次の行動が決まっていると朝の取りかかりが楽になるためです",
                    action="今日の終わりに、明日最初にやることを1つだけメモしましょう",
                    amount="1つだけ",
                    alternative="メモが難しい場合は、頭の中で1つ決めるだけでも構いません",
                )
            )

        scores = context.get("scores", [])
        trend = "スコアの推移データはまだ十分ではありません。"
        if len(scores) >= 2:
            first, last = scores[0], scores[-1]
            if first.get("mental") is not None and last.get("mental") is not None:
                diff = last["mental"] - first["mental"]
                if diff <= -10:
                    trend = f"メンタルスコアが期間内で{abs(diff)}点低下している傾向があります。要因の確認が必要です。"
                elif diff >= 10:
                    trend = f"メンタルスコアが期間内で{diff}点上昇している傾向があります。"
                else:
                    trend = "主要スコアは期間内で大きな変動なく推移している傾向があります。"

        risk_flags: list[RiskFlag] = []
        if avg_stress is not None and avg_stress >= 4.5:
            risk_flags.append(
                RiskFlag(type="stress_high", detail="ストレス評価が高い状態が続いている可能性があります。スタッフによる確認が必要です")
            )

        return AiAnalysisResult(
            summary="。".join(summary_parts) + "が見られます。" if concerns else "。".join(summary_parts) + "です。",
            strengths=strengths or ["日報の入力に取り組めています"],
            concerns=concerns,
            trend_analysis=trend,
            maslow_analysis=self._maslow(avg_sleep, avg_stress),
            adler_analysis="できたことの記録を続けている点は貢献感・自己受容につながる行動と考えられます。評価ではなく「勇気づけ」の声かけが有効な可能性があります。",
            perma_analysis=self._perma(avg_mood, success_days),
            abc_analysis="きっかけ（A）→行動（B）→結果（C）の記録がそろうと、負担が生じる場面の特定に役立ちます。困ったことが起きた前後の状況を記録できると分析精度が上がります。",
            choice_theory_analysis="基本的欲求のうち「達成」「所属」に関する記録が中心です。楽しみに関する活動の記録が増えると、より正確な把握ができる可能性があります。",
            behavioral_economics_analysis="大きな目標より「10分だけ」「1つだけ」の小さな行動目標（ナッジ）が習慣形成に有効と考えられます。実行意図（いつ・どこで・何を）を決めると実行率が上がる傾向があります。",
            staff_recommendations=staff_recs[:5],
            user_recommendations=user_recs[:3],
            questions_for_staff=[r.questions[0] for r in staff_recs if r.questions][:3],
            risk_flags=risk_flags,
            confidence=0.6 if report_count >= 7 else 0.4,
            data_limitations=limitations or ["本結果はモックAIによる参考情報です"],
        )

    def _maslow(self, avg_sleep: float | None, avg_stress: float | None) -> str:
        if avg_sleep is not None and avg_sleep < 6:
            return "生理的欲求（睡眠）が十分に満たされていない可能性があります。まず睡眠の安定を優先した支援が有効と考えられます。"
        if avg_stress is not None and avg_stress >= 3.5:
            return "安全欲求（安心できる環境）に関する負担がある可能性があります。安心して過ごせる場面を増やす支援の検討が必要です。"
        return "生理的欲求・安全欲求は概ね満たされている傾向があります。所属・承認につながる活動（役割のある作業など）の充実が次の段階として考えられます。"

    def _perma(self, avg_mood: float | None, success_days: int) -> str:
        parts = []
        if avg_mood is not None:
            parts.append(f"P（前向きな感情）は気分平均{avg_mood}で推移しています")
        if success_days > 0:
            parts.append(f"A（達成）は成功体験の記録が{success_days}日分あり、強みとなっています")
        else:
            parts.append("A（達成）に関する記録が少なく、小さな達成の記録を促すことが有効と考えられます")
        return "。".join(parts) + "。"

    def generate_support_plan(self, context: dict[str, Any]) -> SupportPlanDraft:
        stats = context.get("stats", {})
        avg_sleep = stats.get("avg_sleep_recent")
        avg_stress = stats.get("avg_stress_recent")
        success_days = stats.get("success_experience_days", 0)

        issues = []
        if avg_sleep is not None and avg_sleep < 6:
            issues.append(f"平均睡眠時間が{avg_sleep}時間と短い傾向")
        if avg_stress is not None and avg_stress >= 3.5:
            issues.append(f"ストレス自己評価が平均{avg_stress}と高めの傾向")
        if success_days < 3:
            issues.append("成功体験の記録が少ない傾向")
        if not issues:
            issues.append("大きな課題は確認されていないが、生活リズムの維持が必要")

        short_goals = ["1日1回、できたことを日報に記録する（4週間継続）"]
        if avg_sleep is not None and avg_sleep < 6:
            short_goals.insert(0, "睡眠時間を平均6時間以上にする（4週間で達成）")
        if avg_stress is not None and avg_stress >= 3.5:
            short_goals.append("週1回、負担に感じたことをスタッフに話す機会を持つ")

        return SupportPlanDraft(
            title="生活リズムと自己効力感の安定に向けた支援計画（下書き）",
            current_issues="、".join(issues) + "が記録から確認されています。",
            strengths=(
                f"日報の入力を継続できている点、成功体験を{success_days}日分記録できている点が強みです。"
                if success_days
                else "日報の入力に取り組めている点が強みです。"
            ),
            user_preferences="（本人の希望をスタッフが面談で確認のうえ記入してください）",
            background_hypothesis="生活リズムの乱れがストレス・疲労感に影響している可能性があります（仮説であり、本人への確認が必要です）。",
            long_term_goal="生活リズムを整え、安心して日中活動へ参加できる状態を維持する（6か月）",
            short_term_goals=short_goals,
            support_methods=[
                "生活リズム表を用いた週1回の振り返り面談",
                "勇気づけを中心とした声かけ（結果ではなく取り組みに注目する）",
                "成功体験の記録を一緒に振り返る時間を設ける",
            ],
            home_actions=["決まった時間に就寝準備を始める", "朝食が難しい日は飲み物かバナナのどちらか1つを選ぶ"],
            office_actions=["声かけによる成功体験の共有", "グループ活動への参加機会の提供"],
            user_actions=["日報を1日1回入力する", "明日の目標を1つ決める", "できたことを1つ記録する"],
            evaluation_metrics=["睡眠スコアの推移", "日報入力率", "短期目標の達成度", "面談での本人の評価"],
            notes="本計画はAIが生成した下書きです。スタッフが本人の意向を確認し、編集・承認してから使用してください。",
        )
