"""ウェルビーイングカードのマスタ定義。

NTT「わたしたちのウェルビーイングカード」スタンダード版32種（2024年）をもとにしている。
https://socialwellbeing.ilab.ntt.co.jp/tool_measure_wellbeingcard.html

カテゴリはカードの配置に基づく3分類:
- self: じぶんのこと
- people: ひととのつながり
- world: 社会や世界とのつながり
"""

CARDS: list[dict[str, str]] = [
    # --- じぶんのこと ---
    {"id": "immersion", "label": "熱中・没頭", "category": "self", "description": "時間を忘れて何かに打ち込むこと"},
    {"id": "achievement", "label": "達成", "category": "self", "description": "目標ややりたいことをやりとげること"},
    {"id": "self_determination", "label": "自己決定", "category": "self", "description": "自分のことを自分で決めること"},
    {"id": "challenge", "label": "挑戦", "category": "self", "description": "新しいことにチャレンジすること"},
    {"id": "growth", "label": "成長", "category": "self", "description": "できることが増えていくこと"},
    {"id": "hope", "label": "希望", "category": "self", "description": "これからに明るい見通しをもてること"},
    {"id": "self_awareness", "label": "自己への気づき", "category": "self", "description": "自分の気持ちや状態に気づくこと"},
    {"id": "relaxation", "label": "緊張からの解放", "category": "self", "description": "ほっとして、リラックスすること"},
    {"id": "mindfulness", "label": "マインドフルネス", "category": "self", "description": "今この瞬間を落ち着いて感じること"},
    {"id": "everyday", "label": "日常", "category": "self", "description": "いつもどおりの毎日を過ごせること"},
    # --- ひととのつながり ---
    {"id": "relationship_building", "label": "関係づくり", "category": "people", "description": "新しい人とのつながりをつくること"},
    {"id": "respect_values", "label": "価値観の理解と尊重", "category": "people", "description": "おたがいの考え方を大切にすること"},
    {"id": "admiration", "label": "あこがれ・尊敬", "category": "people", "description": "あこがれる人・尊敬できる人がいること"},
    {"id": "close_relationship", "label": "親しい関係", "category": "people", "description": "気心の知れた人と過ごすこと"},
    {"id": "love", "label": "愛", "category": "people", "description": "大切な人を想い、想われること"},
    {"id": "support_oshi", "label": "応援・推し", "category": "people", "description": "誰かや何かを応援すること"},
    {"id": "acceptance", "label": "受容・承認", "category": "people", "description": "ありのままを受け入れてもらえること"},
    {"id": "gratitude", "label": "感謝", "category": "people", "description": "ありがとうを感じること・伝えること"},
    {"id": "trust", "label": "信頼", "category": "people", "description": "信じられる人がいること"},
    {"id": "celebration", "label": "祝福", "category": "people", "description": "おめでとうを伝え合うこと"},
    # --- 社会や世界とのつながり ---
    {"id": "compassion", "label": "思いやり", "category": "world", "description": "相手の気持ちを考えて行動すること"},
    {"id": "cooperation", "label": "協調", "category": "world", "description": "まわりと力を合わせること"},
    {"id": "order", "label": "秩序", "category": "world", "description": "きまりやルールが守られた安心感"},
    {"id": "co_creation", "label": "共創", "category": "world", "description": "みんなで一緒に何かをつくること"},
    {"id": "diversity", "label": "多様性", "category": "world", "description": "いろいろな人や考え方があること"},
    {"id": "social_contribution", "label": "社会貢献", "category": "world", "description": "社会や誰かの役に立つこと"},
    {"id": "connection_life", "label": "生命とのつながり", "category": "world", "description": "生きもの・いのちとのつながりを感じること"},
    {"id": "connection_time", "label": "時間を越えたつながり", "category": "world", "description": "過去や未来とのつながりを感じること"},
    {"id": "prayer", "label": "あらゆるものへの祈り", "category": "world", "description": "大切なものへ祈り、願うこと"},
    {"id": "connection_nature", "label": "自然とのつながり", "category": "world", "description": "自然にふれて心が動くこと"},
    {"id": "en", "label": "縁", "category": "world", "description": "めぐりあわせ・ご縁を感じること"},
    {"id": "peace", "label": "平和", "category": "world", "description": "おだやかで安心できる世界であること"},
]

CARD_IDS: set[str] = {c["id"] for c in CARDS}
CARD_LABELS: dict[str, str] = {c["id"]: c["label"] for c in CARDS}

CATEGORY_LABELS = {
    "self": "じぶんのこと",
    "people": "ひととのつながり",
    "world": "社会や世界とのつながり",
}
