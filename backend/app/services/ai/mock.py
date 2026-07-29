"""モックAI。APIキーなしでもアプリ全体を動作確認できる。

固定文ではなく、入力データ（睡眠・ストレス・成功体験・記録件数）に
応じて分岐した結果を返す。
"""

from typing import Any

from app.schemas.ai import (
    AiAnalysisResult,
    MonthlyReportResult,
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
        reports = context.get("daily_reports", [])
        social_values = [r["social_level"] for r in reports if r.get("social_level") is not None]
        avg_social = round(sum(social_values) / len(social_values), 1) if social_values else None
        difficulty_days = sum(1 for r in reports if (r.get("difficulty") or "").strip())

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
            adler_analysis=self._adler(success_days, avg_social),
            perma_analysis=self._perma(avg_mood, success_days),
            abc_analysis=self._abc(difficulty_days, success_days),
            choice_theory_analysis=self._choice_theory(avg_social, success_days, avg_mood),
            behavioral_economics_analysis=self._behavioral_economics(report_count, success_days),
            staff_recommendations=staff_recs[:5],
            user_recommendations=user_recs[:3],
            questions_for_staff=[r.questions[0] for r in staff_recs if r.questions][:3],
            risk_flags=risk_flags,
            confidence=0.6 if report_count >= 7 else 0.4,
            data_limitations=limitations or ["本結果はモックAIによる参考情報です"],
        )

    # --- 6つの理論による分析（各100文字程度） ---

    def _maslow(self, avg_sleep: float | None, avg_stress: float | None) -> str:
        """マズローの5段階欲求: どの段階の欲求が満たされていないかを見る"""
        if avg_sleep is not None and avg_sleep < 6:
            return (
                f"第1段階の生理的欲求に課題があります。平均睡眠{avg_sleep}時間と不足しており、"
                "上位の欲求より先に休息の確保を優先する支援が有効と考えられます。"
            )
        if avg_stress is not None and avg_stress >= 3.5:
            return (
                f"第2段階の安全欲求に負担が見られます。ストレス平均{avg_stress}と高めで、"
                "安心して過ごせる場面を増やすことが次の段階への土台になります。"
            )
        return (
            "第1・2段階の生理的欲求と安全欲求は概ね満たされている傾向です。"
            "第3・4段階の所属・承認欲求に向け、役割のある作業や称賛の機会が有効です。"
        )

    def _adler(self, success_days: int, avg_social: float | None) -> str:
        """アドラー心理学: 勇気づけ・共同体感覚・貢献感"""
        if success_days >= 3:
            return (
                f"できたことを{success_days}日分記録できており、自己受容が育っています。"
                "結果ではなく取り組みに注目した勇気づけで、さらに貢献感を高められます。"
            )
        if avg_social is not None and avg_social <= 2.5:
            return (
                f"人との交流が平均{avg_social}と少なめで、共同体感覚を育てる機会が限られています。"
                "誰かの役に立つ小さな役割を任せることが有効と考えられます。"
            )
        return (
            "他者との関わりの中で役割を持てている傾向です。"
            "評価ではなく勇気づけの声かけを続けることで、課題に自ら向き合う力が育ちます。"
        )

    def _perma(self, avg_mood: float | None, success_days: int) -> str:
        """ポジティブ心理学(PERMA): 幸福の5要素"""
        mood_part = f"P(前向きな感情)は気分平均{avg_mood}" if avg_mood is not None else "P(前向きな感情)は記録が不足"
        if success_days >= 3:
            return (
                f"{mood_part}で推移し、A(達成)は成功体験{success_days}日分と強みです。"
                "R(関係性)とM(意味)を高める機会をつくると幸福度全体が上がります。"
            )
        return (
            f"{mood_part}で推移しています。A(達成)の記録が少ないため、"
            "小さなできたことを言語化して残す習慣が幸福度の底上げにつながります。"
        )

    def _abc(self, difficulty_days: int, success_days: int) -> str:
        """ABA(応用行動分析): A(先行事象)→B(行動)→C(結果)"""
        if difficulty_days >= 3:
            return (
                f"困りごとの記録が{difficulty_days}日分あります。その直前の状況(A)を一緒に確認すると、"
                "負担が生じる場面の共通点が見え、環境調整による予防が可能になります。"
            )
        if success_days > 0:
            return (
                f"うまくいった行動(B)が{success_days}日分記録されています。"
                "その直後に称賛(C)を返すことで望ましい行動が強化され、定着しやすくなります。"
            )
        return (
            "きっかけ(A)→行動(B)→結果(C)の記録がそろうと分析精度が上がります。"
            "できごとの前後の状況をあわせて記録できるよう促すことが有効です。"
        )

    def _choice_theory(self, avg_social: float | None, success_days: int, avg_mood: float | None) -> str:
        """選択理論心理学: 5つの基本的欲求(生存・愛所属・力・自由・楽しみ)"""
        if avg_social is not None and avg_social <= 2.5:
            return (
                f"「愛・所属」の欲求が満たされにくい状態です(交流平均{avg_social})。"
                "本人が選べる形で人と関わる場を用意すると、内側からの動機が働きやすくなります。"
            )
        if success_days >= 3:
            return (
                "「力(達成)」の欲求が満たされています。"
                "次は「楽しみ」「自由」の欲求に注目し、自分で選べる活動を増やすと満足感が広がります。"
            )
        return (
            "「力(達成)」「愛・所属」に関する記録が中心です。"
            "外からの指示ではなく本人が選ぶ場面を増やすことが、行動の継続につながります。"
        )

    def _behavioral_economics(self, report_count: int, success_days: int) -> str:
        """行動経済学: ナッジ・現在バイアス・習慣化"""
        if report_count >= 14:
            return (
                f"{report_count}日分の記録が続いており、習慣化ができています。"
                "現状維持バイアスが良い方向に働くよう、今の記録の型は変えずに保つことが有効です。"
            )
        return (
            "人は先の利益より目先の負担を重く感じます(現在バイアス)。"
            "「10分だけ」「1つだけ」の小さな行動目標(ナッジ)と、いつ・どこでを決める工夫が有効です。"
        )

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

    def generate_monthly_report(self, context: dict[str, Any]) -> MonthlyReportResult:
        from app.services.ai.monthly import generate_monthly_report_mock

        return generate_monthly_report_mock(context)
