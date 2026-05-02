from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from note.natural_blog_types import DiscourseSectionPlan, NaturalStyleProfile

_TERM_TOKEN_RE = re.compile(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,24}")
_STOP_TERMS = {
    "こと",
    "ため",
    "よう",
    "もの",
    "これ",
    "それ",
    "今回",
    "記事",
    "読者",
    "担当者",
    "方法",
    "内容",
    "情報",
    "理解",
    "整理",
    "紹介",
    "解説",
    "実践",
    "運用",
}

_BRANDING_ABSTRACT_TERMS = {
    "価値",
    "伝える",
    "ブランド",
    "記事",
    "運用",
    "迷い",
    "減らす",
    "機能",
    "多さ",
}

_BRANDING_CONTEXT_MARKERS = (
    "小規模",
    "中堅",
    "大手",
    "SaaS",
    "BtoB",
    "BtoC",
    "導入初期",
    "複数拠点",
    "営業",
    "サポート",
    "カスタマーサクセス",
    "CS",
    "導入担当",
    "情シス",
    "DX",
    "デジタル化",
    "電子化",
    "アナログ",
    "アナログデータ",
    "紙",
    "帳票",
    "バックオフィス",
)
_COMPANY_INTRO_CORE_DEFAULTS = [
    "会社の輪郭",
    "事業内容",
    "会社の輪郭を結ぶ",
]
_COMPANY_INTRO_BUCKET_DEFAULTS: Dict[str, str] = {
    "overview": "事業内容",
    "strength": "強み",
    "history": "歩み",
}
_COMPANY_INTRO_SOURCE_SLOT_ORDER = ("overview", "strength", "history")
_COMPANY_INTRO_SLOT_SPECS: Dict[str, Dict[str, str]] = {
    "outline": {
        "heading": "会社の輪郭を最初に置く",
        "intent": "hook",
        "topic_seed": "会社の輪郭",
        "bridge_hint": "導入で、会社として最初に伝える輪郭を短く置く",
        "reader_question": "まずどんな会社か",
    },
    "overview": {
        "heading": "どんな事業を担っているか",
        "intent": "value",
        "topic_seed": "事業内容",
        "bridge_hint": "次に事業内容を具体化し、何を担う会社かが伝わるようにする",
        "reader_question": "何をしている会社か",
    },
    "strength": {
        "heading": "支えている強み",
        "intent": "practice",
        "topic_seed": "強み",
        "bridge_hint": "次に強みを事実ベースで置き、抽象的な価値語だけに寄せない",
        "reader_question": "どんな強みがあるか",
    },
    "history": {
        "heading": "歩みから見える姿勢",
        "intent": "reflection",
        "topic_seed": "歩み",
        "bridge_hint": "次に歩みを通して、今の姿勢がどう形づくられたかを示す",
        "reader_question": "どんな歩みをたどってきたか",
    },
    "current_value": {
        "heading": "いま提供している価値",
        "intent": "decision",
        "topic_seed": "現在の提供価値",
        "bridge_hint": "次に現在の提供価値を整理し、読後の理解を具体化する",
        "reader_question": "今どんな価値を提供しているか",
    },
    "closing": {
        "heading": "会社の輪郭をあらためて結ぶ",
        "intent": "closing",
        "topic_seed": "会社の輪郭を結ぶ",
        "bridge_hint": "本文の要点をまとめ直すだけで終えず、会社として何を担うかが自然に残る形で結ぶ",
        "reader_question": "読み終えたときにどんな輪郭が残るか",
    },
}
_RED_BRIDGE_PHRASES = (
    "前の段落で触れたように",
    "前の節で触れたように",
    "ここまで読んで",
    "ここまでお読みいただいて",
    "その感覚はとても自然です",
)

_HEADING_POOLS: Dict[str, List[tuple[str, str]]] = {
    "announcement": [
        ("変更の背景と要点", "context"),
        ("今回の変更で押さえたいこと", "clarify"),
        ("現場での影響と確認ポイント", "impact"),
        ("運用時に迷いやすい点", "caution"),
        ("次に取るべき行動", "closing"),
    ],
    "industry_analysis": [
        ("市場の前提と論点", "hook"),
        ("いま起きている構造変化", "structure"),
        ("主要プレイヤーの差分", "comparison"),
        ("意思決定で見るべき指標", "decision"),
        ("直近で起こりやすいリスク", "caution"),
        ("次の一手をどう考えるか", "closing"),
    ],
    "case_study": [
        ("最初に見えていた課題", "hook"),
        ("どこで迷いが生まれたか", "problem"),
        ("どう進め方を組み替えたか", "practice"),
        ("途中で効いた工夫", "decision"),
        ("結果として何が変わったか", "change"),
        ("どの条件なら再現できるか", "condition"),
    ],
    "comparative_review": [
        ("比較の前提条件をそろえる", "hook"),
        ("評価軸を先に決める", "criteria"),
        ("候補ごとの強みと弱み", "comparison"),
        ("用途別に向く選び方", "fit"),
        ("選ぶ前に確認したい点", "caution"),
        ("結論とおすすめの分け方", "closing"),
    ],
    "daily_story": [
        ("その日に引っかかったこと", "hook"),
        ("最初に感じた違和感", "scene"),
        ("試しながら見えた変化", "change"),
        ("あとから気づいたこと", "reflection"),
        ("いま振り返って思うこと", "closing"),
        ("同じ状況の人に伝えたいこと", "action"),
    ],
    "branding": [
        ("私たちが向き合っている課題", "hook"),
        ("価値をどう言葉にしているか", "value"),
        ("現場で続けている工夫", "practice"),
        ("判断の基準と優先順位", "decision"),
        ("これから取り組むこと", "closing"),
        ("読者と共有したい視点", "reflection"),
        ("次の一歩に変えるには", "action"),
    ],
    "company_introduction": [
        ("会社の輪郭を最初に置く", "hook"),
        ("どんな事業を担っているか", "value"),
        ("支えている強み", "practice"),
        ("歩みから見える姿勢", "reflection"),
        ("いま提供している価値", "decision"),
        ("会社の輪郭をあらためて結ぶ", "closing"),
    ],
    "balanced": [
        ("背景と論点整理", "hook"),
        ("現場で起きやすい課題", "problem"),
        ("判断の軸をどう持つか", "decision"),
        ("実務で使える進め方", "practice"),
        ("運用時の注意点", "caution"),
        ("改善につなげる見方", "reflection"),
        ("まとめと次の一歩", "closing"),
    ],
}

_CASE_STUDY_INTENT_FOCUS: Dict[str, Dict[str, Any]] = {
    "hook": {
        "default_topic_seed": "課題",
        "required_terms": ["課題", "最初にどこで止まったか"],
        "keywords": ("課題", "初動", "つまず", "止ま", "引っかか"),
    },
    "problem": {
        "default_topic_seed": "迷いが生まれた場面",
        "required_terms": ["迷いが生まれた場面", "役割の境目"],
        "keywords": ("迷", "詰ま", "止ま", "境界", "役割", "順番", "共有"),
    },
    "practice": {
        "default_topic_seed": "進め方の組み替え",
        "required_terms": ["どう直したか", "進め方"],
        "keywords": ("直し", "見直", "組み替", "進め方", "導線", "改善"),
    },
    "decision": {
        "default_topic_seed": "途中で効いた工夫",
        "required_terms": ["途中で効いた工夫", "判断の線引き"],
        "keywords": ("工夫", "効い", "判断", "線引", "途中", "宿題"),
    },
    "change": {
        "default_topic_seed": "変化した状態",
        "required_terms": ["何が変わったか", "変化した状態"],
        "keywords": ("変わ", "変化", "改善", "減っ", "増え", "揃", "止まり方", "結果"),
    },
    "condition": {
        "default_topic_seed": "再現条件",
        "required_terms": ["再現条件", "前提", "限界"],
        "keywords": ("条件", "再現", "前提", "限界", "向く", "向か", "例外"),
    },
}

_COMPARATIVE_REVIEW_INTENT_FOCUS: Dict[str, Dict[str, Any]] = {
    "hook": {
        "default_topic_seed": "比較の前提条件",
        "required_terms": ["比較条件", "前提"],
        "keywords": ("比較条件", "前提", "対象", "揃", "同条件", "環境"),
    },
    "criteria": {
        "default_topic_seed": "評価軸",
        "required_terms": ["評価軸", "判断基準"],
        "keywords": ("評価軸", "比較軸", "観点", "基準", "判断基準", "見るポイント"),
    },
    "comparison": {
        "default_topic_seed": "候補差分",
        "required_terms": ["差分", "強み", "弱み"],
        "keywords": ("強み", "弱み", "差分", "違い", "メリット", "デメリット", "比較"),
    },
    "fit": {
        "default_topic_seed": "用途別の向き不向き",
        "required_terms": ["用途別", "向くケース", "向かないケース"],
        "keywords": ("用途", "向く", "向か", "合う", "選び方", "ケース", "利用場面"),
    },
    "caution": {
        "default_topic_seed": "確認事項",
        "required_terms": ["確認事項", "前提", "例外"],
        "keywords": ("確認", "前提", "例外", "制約", "コスト", "移行", "注意"),
    },
    "closing": {
        "default_topic_seed": "用途別の結論",
        "required_terms": ["結論", "おすすめの分け方"],
        "keywords": ("結論", "おすすめ", "分け方", "選ぶ", "判断", "用途別"),
    },
}

_CASE_STUDY_REQUIRED_FIRST_INTENTS = {"condition"}
_COMPARATIVE_REVIEW_REQUIRED_FIRST_INTENTS = {
    "hook",
    "criteria",
    "comparison",
    "fit",
    "caution",
    "closing",
}

_COMPARATIVE_REVIEW_GENERIC_TERMS = {
    "比較条件",
    "前提",
    "比較の前提条件をそろえる",
    "評価軸",
    "判断基準",
    "評価軸を先に決める",
    "差分",
    "強み",
    "弱み",
    "候補ごとの強みと弱み",
    "用途別",
    "向くケース",
    "向かないケース",
    "用途別に向く選び方",
    "確認事項",
    "選ぶ前に確認したい点",
    "結論",
    "おすすめの分け方",
    "結論とおすすめの分け方",
}

_ANCHOR_BUDGETS: Dict[str, Dict[str, int]] = {
    "note_4000_branding": {"must_cover": 2, "related": 1, "question": 0, "extra": 1, "topic": 0, "order": 0},
    "note_4000_industry_analysis": {"must_cover": 1, "related": 1, "question": 0, "extra": 1, "topic": 0, "order": 1},
    "note_4000_case_study": {"must_cover": 2, "related": 1, "question": 1, "extra": 1, "topic": 0, "order": 0},
    "note_4000_comparative_review": {"must_cover": 2, "related": 2, "question": 1, "extra": 1, "topic": 0, "order": 0},
    "default": {"must_cover": 2, "related": 1, "question": 1, "extra": 1, "topic": 1, "order": 0},
}

_KOTODESU_POLICIES: Dict[str, Dict[str, str]] = {
    "note_4000_industry_analysis": {
        "decision": "この節では『ことです』は 0〜1回までに抑え、示唆や結論を名詞化せず判断文として書く",
        "closing": "この節では『ことです』は 0〜1回までに抑え、示唆や結論を名詞化せず判断文として書く",
    }
}

_INTENT_LOCAL_RULES: Dict[str, Dict[str, str]] = {
    "note_4000_case_study": {
        "change": "この節では結果を抽象語で総括せず、何がどのように変わったかを状態変化の文で先に置く",
        "condition": "この節では再現条件、前提、限界を分けて書き、成功談の余韻だけで閉じない",
        "closing": "この節では本文の要約だけで閉じず、最後にそのまま試せる一歩か適用条件を具体文で置き、『なります』で締めない",
    },
    "note_4000_comparative_review": {
        "hook": "この節では結論やおすすめを先出しせず、比較対象と前提条件だけをそろえる",
        "criteria": "この節では評価軸だけを定義し、途中で別の評価軸へすり替えない",
        "comparison": (
            "この節では候補差分を書く。一律の優劣や単独推奨に流さない。"
            "文を述語まで書き切り、『ことが。』『ため。』『〜ではなく。』『〜なら。』『〜は。』のような切れ文で終えない"
        ),
        "fit": (
            "この節では用途別の向き不向きを分けて書き、万人向けの断定にしない。"
            "『誰にでも最適』『一社で決まり』のような万能断定にしない"
        ),
        "caution": (
            "この節では移行コスト、前提、例外、確認事項を置き、比較軸を増やしすぎない。"
            "文を述語まで書き切り、『ことが。』『ため。』『〜ではなく。』『〜なら。』『〜は。』のような切れ文で終えない"
        ),
        "closing": (
            "この節では一律の優劣で結ばず、用途別に結論を分けて締める。"
            "『誰にでも最適』『一社で決まり』のような万能断定にしない。"
            "文を述語まで書き切り、『ことが。』『ため。』『〜ではなく。』『〜なら。』『〜は。』のような切れ文で終えない"
        ),
    },
}

_ARTICLE_SPECIFIC_LINES: Dict[str, str] = {
    "note_4000_branding": "- ブランド記事として、価値が立ち上がる背景、現場の工夫、読者にとっての意味を順に置く\n",
    "note_4000_industry_analysis": (
        "- 業界分析記事として、市場の前提、構造変化、主要差分、意思決定への示唆を混ぜずに書く\n"
        "- 差分や示唆は『ことです』で名詞化せず、何が起きているかを文として言い切る\n"
    ),
    "note_4000_comparative_review": (
        "- 比較レビューとして、この節に割り当てた比較論点だけを扱い、別の節の役割を先回りしない\n"
        "- 助詞や接続の途中で句点を打たず、句点は述語のあとに置く。"
        "『〜でも。』『〜が。』『〜で。』『〜と。』『〜なら。』『〜のは。』『〜は。』『〜ではなく。』『〜ため。』のような切れ方を残さない\n"
        "- 『誰にでも最適』『万人向けの正解』『一社で決まり』のような単独推奨や万能断定を置かない\n"
    ),
    "note_4000_daily": "- 日常記事として、観察した出来事、そこで揺れた感覚、あとから出てきた学びの順で書く\n",
    "note_4000_case_study": (
        "- 事例記事として、課題、進め方、工夫、結果、再現条件を混ぜずに書く\n"
        "- 結果や学びは『ことです』でまとめず、何をしたか・何が分かったかで閉じる\n"
    ),
}

_FACT_SLOT_PROMPT_MAP: Dict[str, str] = {
    "change": "この節は変更点そのものを先に明示する",
    "who_when": "この節は対象者と開始時期を混ぜずに示す",
    "impact": "この節は利用者への影響だけに絞る",
    "check": "この節は確認事項と手続きの要点を整理し、依頼文を重ねない",
    "caution": "この節は移行時の注意点を具体化する",
    "action": "この節は公式情報の確認先と次の行動に着地し、依頼文は末尾の1文までに抑える",
}

_ENDING_LINES: Dict[str, str] = {
    "brand_narrative_mix": "文末は です・ます を軸にしつつ、でした・と感じます・と捉えています を少量混ぜる。ことです・なります・ください の連打は避ける",
    "analytic_formal_mix": "文末は です・ます を軸にし、あります・でしょう・と考えられます を少量混ぜる。なります・ことです の偏りは避ける",
    "comparison_formal_mix": "文末は です・ます を軸にし、向いています・考えられます を交ぜて単調さを避ける",
    "case_process_mix": "文末は です・ます を軸にし、でした・分かりました・できました・見えてきました を少量混ぜる。なります・ことです・ください の偏りは避ける",
    "reflective_mix": "文末は です・ます を軸にし、でした・と思います を交ぜて内省の揺れを残す",
    "notice_formal": "文末は です・ます・でした・ました を中心にし、揺らぎより明確さを優先する。ください は最終の行動案内に寄せる",
    "explanatory_mix": "文末は です・ます を軸にし、でしょう・と考えます を少量混ぜて説明調の単調さを避ける",
    "balanced": "文末は です・ます を軸にしつつ、同じ終わり方を続けない",
}

_ENDING_GUARD_LINES: Dict[str, str] = {
    "brand_narrative_mix": "主文の語尾は です・ます・でした・と感じます・と捉えています を回し、ことです・なります・ください を節内で続けない",
    "analytic_formal_mix": "主文の語尾は です・ます・あります・考えられます・でしょう を回し、なります・ことです を締め文で使わない",
    "comparison_formal_mix": "主文の語尾は です・ます・向いています・考えられます を回し、同じ判断文を連続させない",
    "case_process_mix": "主文の語尾は です・ます・でした・分かりました・できました・見えてきました を回し、なります・ことです・ください を上位の語尾にしない",
    "reflective_mix": "主文の語尾は です・ます・でした・と思います を回し、同じ内省語尾を続けない",
    "notice_formal": "主文の語尾は です・ます・でした・ました を中心にし、案内文で曖昧な言い回しを増やさない。依頼文は action 節の最終1文に寄せ、それ以外は事実文で閉じる",
    "explanatory_mix": "主文の語尾は です・ます・でしょう・と考えます を回し、説明文の同型反復を避ける",
    "balanced": "主文の語尾を固定せず、同じ終わり方を続けない",
}


def _infer_direction_family(*, article_type: str, base_template: str) -> str:
    if (
        article_type in {"branding", "company_introduction", "product_introduction"}
        or base_template in {"branding", "company_introduction"}
    ):
        return "trust_intro"
    if article_type in {"explanatory_article", "industry_analysis"}:
        return "explain_analysis"
    return ""


def _build_reference_realization_policy(
    *,
    direction_family: str,
    article_type: str,
    base_template: str,
    intent: str,
    section_index: int,
    section_count: int,
) -> Dict[str, Any]:
    if not direction_family:
        return {}

    closing_like = section_index == max(section_count - 1, 0) or intent == "closing"
    if direction_family == "trust_intro":
        company_intro_like = article_type == "company_introduction" or base_template == "company_introduction"
        if section_index == 0:
            speaker_reference_policy = "company_name_once"
            subject_reintroduction_policy = "lead_only"
        elif closing_like:
            speaker_reference_policy = "watashitachi_preferred"
            subject_reintroduction_policy = "closing_reanchor"
        elif company_intro_like and intent in {"value", "practice", "decision"}:
            speaker_reference_policy = "tousha_preferred"
            subject_reintroduction_policy = "section_shift_only"
        else:
            speaker_reference_policy = "subject_omission_preferred"
            subject_reintroduction_policy = "section_shift_only"
        return {
            "direction_family": direction_family,
            "speaker_reference_policy": speaker_reference_policy,
            "subject_reintroduction_policy": subject_reintroduction_policy,
            "proper_noun_repeat_cap": 1,
        }

    if direction_family == "explain_analysis":
        return {
            "direction_family": direction_family,
            "speaker_reference_policy": "no_first_person",
            "subject_reintroduction_policy": "closing_reanchor" if closing_like else "section_shift_only",
            "proper_noun_repeat_cap": 1,
        }

    return {}


def _reference_realization_prompt_hint(section: DiscourseSectionPlan) -> str:
    speaker_reference_policy = str(getattr(section, "speaker_reference_policy", "") or "").strip()
    subject_reintroduction_policy = str(getattr(section, "subject_reintroduction_policy", "") or "").strip()
    proper_noun_repeat_cap = getattr(section, "proper_noun_repeat_cap", None)

    speaker_hint = {
        "company_name_once": "会社名は初出か節の切り替わりだけに置き、段落頭で連打しない",
        "watashitachi_preferred": "会社名を連打せず、流れが続く文では『私たち』か省略へ寄せる",
        "tousha_preferred": "会社名の反復を避け、必要な場面だけ『当社』を使う",
        "subject_omission_preferred": "話題が続く間は主語を言い直さず、省略を優先する",
        "no_first_person": "一人称を出さず、対象や論点を主語にする",
    }.get(speaker_reference_policy, "")
    reintroduction_hint = {
        "lead_only": "主語の再導入は導入の初出までに留める",
        "section_shift_only": "主語は話題や対象が切り替わる場面だけ戻す",
        "closing_reanchor": "結びでだけ主語を軽く戻してよい",
    }.get(subject_reintroduction_policy, "")

    parts = [hint for hint in [speaker_hint, reintroduction_hint] if hint]
    if isinstance(proper_noun_repeat_cap, int) and proper_noun_repeat_cap >= 0:
        parts.append(f"固有名詞反復は同一節で{proper_noun_repeat_cap}回まで")
    return " / ".join(parts)


_STYLE_PROFILE_DEFAULTS: Dict[str, Any] = {
    "profile_name": "note_4000_balanced",
    "linebreak_profile": "default_balanced",
    "article_tone": "reader_first",
    "paragraph_min": 2,
    "paragraph_max": 3,
    "sentence_length_mix": "short_medium_long",
    "opening_variation_target": "high",
    "information_density": "balanced",
    "punctuation_profile": "balanced_japanese",
    "subject_omission_policy": "balanced",
    "paragraph_break_policy": "topic_or_role_shift",
    "ending_distribution_hint": "balanced",
    "preferred_endings": ["です。", "ます。", "でしょう。", "ですね。"],
    "prompt_rules": [
        "読者に語りかける一人の書き手として書く",
        "文の長さに強弱をつける",
        "重要語は言い換えすぎず一貫して使う",
        "主語は必要なときだけ置く",
        "箇条書きではなく自然な段落で進める",
    ],
}

_STYLE_PROFILE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "branding": {
        "profile_name": "note_4000_branding",
        "linebreak_profile": "branding_story",
        "article_tone": "value_narrative",
        "paragraph_max": 4,
        "sentence_length_mix": "medium_long_with_short_breaks",
        "opening_variation_target": "very_high",
        "information_density": "value_evidence",
        "punctuation_profile": "expressive_japanese",
        "subject_omission_policy": "light_corporate_anchor",
        "paragraph_break_policy": "value_or_scene_shift",
        "ending_distribution_hint": "brand_narrative_mix",
        "preferred_endings": ["です。", "ます。", "でした。", "と感じます。", "と捉えています。"],
        "prompt_rules": [
            "宣伝文ではなく、価値が必要になる背景と判断理由を書く",
            "現場の工夫や言葉選びを入れ、抽象的な理念だけで終わらせない",
        ],
    },
    "industry_analysis": {
        "profile_name": "note_4000_industry_analysis",
        "linebreak_profile": "industry_analysis",
        "article_tone": "market_structural",
        "sentence_length_mix": "medium_long_with_short_breaks",
        "opening_variation_target": "high",
        "information_density": "market_structure",
        "punctuation_profile": "balanced_japanese",
        "subject_omission_policy": "explicit_when_scope_changes",
        "paragraph_break_policy": "structure_or_metric_shift",
        "ending_distribution_hint": "analytic_formal_mix",
        "preferred_endings": ["です。", "ます。", "あります。", "考えられます。", "でしょう。"],
        "prompt_rules": [
            "市場全体の構造変化と、その背景にある要因を分けて書く",
            "単なる感想ではなく、差分と示唆を意思決定につながる形で置く",
        ],
    },
    "comparative_review": {
        "profile_name": "note_4000_comparative_review",
        "linebreak_profile": "comparative_review",
        "article_tone": "criteria_driven",
        "sentence_length_mix": "short_medium_long",
        "opening_variation_target": "high",
        "information_density": "criteria_then_fit",
        "punctuation_profile": "compact_japanese",
        "subject_omission_policy": "explicit_when_comparing_entities",
        "paragraph_break_policy": "criteria_or_usecase_shift",
        "ending_distribution_hint": "comparison_formal_mix",
        "preferred_endings": ["です。", "ます。", "向いています。", "考えられます。", "見えてきます。"],
        "prompt_rules": [
            "比較条件を先にそろえ、途中で評価軸をずらさない",
            "優劣の断定より、用途ごとの向き不向きを明確にする",
            "万人向け・誰にでも最適・一択のような万能断定を避ける",
        ],
    },
    "case_study": {
        "profile_name": "note_4000_case_study",
        "linebreak_profile": "case_study",
        "article_tone": "process_result",
        "sentence_length_mix": "short_medium_long",
        "opening_variation_target": "high",
        "information_density": "process_result",
        "punctuation_profile": "balanced_japanese",
        "subject_omission_policy": "balanced_process_subjects",
        "paragraph_break_policy": "phase_shift",
        "ending_distribution_hint": "case_process_mix",
        "preferred_endings": ["です。", "ます。", "でした。", "分かりました。", "できました。", "見えてきました。"],
        "prompt_rules": [
            "課題、進め方、工夫、結果の順を崩さずに書く",
            "成功談として盛らず、再現条件と限界を残す",
        ],
    },
    "daily_story": {
        "profile_name": "note_4000_daily",
        "linebreak_profile": "daily_reflective",
        "article_tone": "first_person_reflective",
        "paragraph_max": 4,
        "sentence_length_mix": "medium_long_with_short_breaks",
        "opening_variation_target": "very_high",
        "information_density": "scene_then_insight",
        "punctuation_profile": "reflective_japanese",
        "subject_omission_policy": "allow_implicit_first_person",
        "paragraph_break_policy": "scene_or_feeling_shift",
        "ending_distribution_hint": "reflective_mix",
        "preferred_endings": ["です。", "ます。", "でした。", "と思います。", "気がしました。"],
        "prompt_rules": [
            "出来事の観察から入り、あとで意味や学びを置く",
            "感情は小さく揺らしてよいが、出来事を大げさに脚色しない",
        ],
    },
    "announcement": {
        "profile_name": "note_4000_clear",
        "linebreak_profile": "announcement_compact",
        "article_tone": "brief_clear",
        "sentence_length_mix": "short_medium",
        "opening_variation_target": "medium",
        "information_density": "fact_dense",
        "punctuation_profile": "compact_japanese",
        "subject_omission_policy": "explicit_when_scope_changes",
        "paragraph_break_policy": "fact_or_action_shift",
        "ending_distribution_hint": "notice_formal",
        "preferred_endings": ["です。", "ます。", "でした。", "ました。"],
        "prompt_rules": [
            "案内文として簡潔かつ正確に書く",
            "感情の代弁や共感の誘導を入れない",
            "確認できる変更点・対象・時期・影響を優先する",
            "推測や励ましで話を広げず、事実ベースで述べる",
            "1文1情報を意識し、言い換えで膨らませない",
        ],
        "banned_openings_extra": ["だからこそ", "大切なのは", "まずは", "当然のことです"],
        "reset_prompt_rules": True,
    },
    "explanatory": {
        "profile_name": "note_4000_explanatory",
        "linebreak_profile": "analysis_balanced",
        "article_tone": "explanatory",
        "sentence_length_mix": "short_medium_long",
        "opening_variation_target": "high",
        "information_density": "example_linked",
        "punctuation_profile": "balanced_japanese",
        "subject_omission_policy": "balanced",
        "paragraph_break_policy": "example_or_reason_shift",
        "ending_distribution_hint": "explanatory_mix",
        "preferred_endings": ["です。", "ます。", "でしょう。", "と考えます。", "見えてきます。"],
    },
}

_EXAMPLE_GROUNDED_PROFILES = {
    "note_4000_branding",
    "note_4000_case_study",
    "note_4000_explanatory",
    "note_4000_industry_analysis",
    "note_4000_comparative_review",
}

_LEGAL_GUARD_KEYWORDS = (
    "法令",
    "条文",
    "景表法",
    "薬機法",
    "特商法",
    "個人情報保護法",
    "ガイドライン",
    "判例",
    "利用規約",
)


def _dedupe_keep_order(items: Iterable[str], limit: int = 8) -> List[str]:
    unique: List[str] = []
    for item in items:
        normalized = str(item or "").strip()
        if not normalized or normalized in unique:
            continue
        unique.append(normalized)
        if len(unique) >= limit:
            break
    return unique


def _extract_terms(text: str, limit: int = 10) -> List[str]:
    candidates: List[str] = []
    for token in _TERM_TOKEN_RE.findall(text or ""):
        normalized = token.strip()
        if len(normalized) <= 1 or normalized in _STOP_TERMS:
            continue
        if normalized.isdigit():
            continue
        candidates.append(normalized)
    return _dedupe_keep_order(candidates, limit=limit)


def _build_instruction_brief(
    user_instruction: str,
    *,
    topic_seed: str,
    must_cover: Sequence[str],
    article_profile: str = "",
) -> str:
    normalized_instruction = _normalize_focus_item(user_instruction or "")
    instruction_terms = _extract_terms(normalized_instruction, limit=5)
    if article_profile == "note_4000_branding":
        instruction_terms = _extract_branding_context_terms(user_instruction) or [
            term for term in instruction_terms if term not in _BRANDING_ABSTRACT_TERMS
        ][:2]
    if article_profile == "note_4000_case_study":
        instruction_terms = [term for term in instruction_terms if len(term) <= 18]
        instruction_terms = instruction_terms[:2]
    preferred = _build_prompt_anchor_terms(
        must_cover=must_cover,
        topic_seed=topic_seed,
        related_terms=[],
        reader_question="",
        article_profile=article_profile,
        extra_terms=instruction_terms,
        limit=3,
    )
    if not preferred:
        return "読者に伝わる具体性を優先する"
    return "、".join(preferred) + " を具体化する"


def _extract_branding_context_terms(text: str) -> List[str]:
    value = str(text or "").strip()
    if not value:
        return []
    markers = [marker for marker in _BRANDING_CONTEXT_MARKERS if marker in value]
    return _dedupe_keep_order(markers, limit=4)


def _compress_branding_topic_terms(
    *,
    must_cover_items: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    user_prompt: str,
) -> List[str]:
    compact_terms: List[str] = []
    for item in must_cover_items:
        normalized = str(item or "").strip()
        if normalized:
            compact_terms.append(normalized)
    raw_terms = [
        *[str(item or "").strip() for item in user_instruction_terms],
        *_extract_branding_context_terms(thesis),
        *_extract_branding_context_terms(user_prompt),
    ]
    for term in raw_terms:
        compact = str(term or "").strip()
        if not compact or compact in _BRANDING_ABSTRACT_TERMS:
            continue
        if len(compact) > 18:
            continue
        compact_terms.append(compact)
    if not compact_terms:
        compact_terms.extend(_extract_branding_context_terms(user_prompt))
    return _dedupe_keep_order(compact_terms, limit=10)


def _company_intro_source_buckets(source_grounding_items: Sequence[Mapping[str, Any]] | None) -> List[str]:
    present_buckets: set[str] = set()
    for item in list(source_grounding_items or []):
        bucket = str(item.get("bucket") or "").strip().lower()
        if bucket in _COMPANY_INTRO_BUCKET_DEFAULTS:
            present_buckets.add(bucket)
    return [bucket for bucket in _COMPANY_INTRO_SOURCE_SLOT_ORDER if bucket in present_buckets]


def _build_company_intro_topic_terms(
    *,
    must_cover_items: Sequence[str],
    topic_terms: Sequence[str],
    source_grounding_items: Sequence[Mapping[str, Any]] | None,
) -> List[str]:
    source_buckets = _company_intro_source_buckets(source_grounding_items)
    if source_buckets:
        prefix_terms = [
            "会社の輪郭",
            *[_COMPANY_INTRO_BUCKET_DEFAULTS[bucket] for bucket in source_buckets],
        ]
    elif list(source_grounding_items or []):
        prefix_terms = ["会社の輪郭"]
    else:
        prefix_terms = list(_COMPANY_INTRO_CORE_DEFAULTS[:-1])
    return _dedupe_keep_order(
        [*prefix_terms, *must_cover_items, *topic_terms, _COMPANY_INTRO_CORE_DEFAULTS[-1]],
        limit=16,
    )


def _fit_slot_order_to_section_count(slot_order: Sequence[str], section_count: int) -> List[str]:
    ordered = [str(slot or "").strip() for slot in slot_order if str(slot or "").strip()]
    if not ordered:
        return []
    section_count = max(3, int(section_count or len(ordered)))
    if section_count <= len(ordered):
        if section_count == len(ordered):
            return list(ordered)
        middle_needed = max(0, section_count - 2)
        return [ordered[0], *ordered[1:1 + middle_needed], ordered[-1]]
    fitted = list(ordered)
    while len(fitted) < section_count:
        fitted.insert(-1, fitted[-2] if len(fitted) >= 2 else fitted[-1])
    return fitted[:section_count]


def _build_company_intro_slot_order(
    *,
    section_count: int,
    source_grounding_items: Sequence[Mapping[str, Any]] | None,
    prefer_current_first: bool = False,
) -> List[str]:
    source_buckets = _company_intro_source_buckets(source_grounding_items)
    if source_buckets:
        ordered_buckets = [
            bucket for bucket in _COMPANY_INTRO_SOURCE_SLOT_ORDER if bucket in source_buckets
        ]
        if prefer_current_first and "overview" in ordered_buckets and len(ordered_buckets) >= 2:
            return [*ordered_buckets, "closing"]
        return [
            "outline",
            *ordered_buckets,
            "closing",
        ]
    if list(source_grounding_items or []):
        return ["outline", "closing"]
    return _fit_slot_order_to_section_count(
        ["outline", "overview", "strength", "history", "current_value", "closing"],
        section_count,
    )


def _announcement_fact_slot_for_index(idx: int) -> str:
    slots = ["change", "who_when", "impact", "check", "caution", "action"]
    return slots[min(idx, len(slots) - 1)]


_ANNOUNCEMENT_SLOT_DEFAULTS: Dict[str, str] = {
    "change": "変更点",
    "who_when": "対象者と開始時期",
    "impact": "利用者への影響",
    "check": "確認事項",
    "caution": "移行時の注意点",
    "action": "公式情報で確認すべき項目",
}

_ANNOUNCEMENT_SLOT_PATTERNS: Dict[str, re.Pattern[str]] = {
    "change": re.compile(r"(変更|変わ|開始|提供開始|新サービス|更新|切り替え|フロー)"),
    "who_when": re.compile(r"(\d{4}年\d{1,2}月\d{1,2}日|対象|既存顧客|開始時期)"),
    "impact": re.compile(r"(影響|変更される|利用環境|契約条件|画面仕様|権限設定)"),
    "check": re.compile(r"(確認|手続き|申込|フォーム|入力内容|ご確認)"),
    "caution": re.compile(r"(注意|遅延|未申込|誤り|支障|移行)"),
    "action": re.compile(r"(公式|案内|お問い合わせ|確認してください|お手続き|申し込み|専用ページ)"),
}


def _announcement_meta_fragment(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return True
    if re.search(r"(一般読者|読者全般|利用者全般|対象者全般|初心者|担当者)$", value):
        return True
    return any(
        marker in value
        for marker in (
            "視点",
            "自分ごと化",
            "どう活用",
            "どう説明",
            "判断しやすくなる",
            "次の一歩",
        )
    )


def _normalize_announcement_fragment(text: str) -> str:
    value = str(text or "").strip(" 　、。")
    value = re.sub(r"(を含める|を明確にする|を整理する|を確認する|に触れる)$", "", value)
    return value.strip(" 　、。")


def _collect_announcement_candidates(
    *,
    must_cover_items: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    user_prompt: str,
) -> List[str]:
    candidates: List[str] = []
    for item in must_cover_items:
        value = str(item or "").strip()
        if value and value not in candidates:
            candidates.append(value)
    raw_fragments: List[str] = []
    for source in [*user_instruction_terms, thesis, user_prompt]:
        for fragment in re.split(r"[。！？\n、,/／]+", str(source or "")):
            compact = _normalize_announcement_fragment(fragment)
            if not compact or len(compact) > 24 or _announcement_meta_fragment(compact):
                continue
            raw_fragments.append(compact)
    term_fragments = [
        term
        for term in [
            *_extract_terms(thesis, limit=4),
            *_extract_terms(user_prompt, limit=8),
        ]
        if term and len(term) <= 20 and not _announcement_meta_fragment(term)
    ]
    return _dedupe_keep_order([*candidates, *raw_fragments, *term_fragments], limit=20)


def _match_announcement_slot_candidate(slot: str, candidates: Sequence[str]) -> str:
    pattern = _ANNOUNCEMENT_SLOT_PATTERNS.get(slot)
    if pattern:
        for candidate in candidates:
            value = str(candidate or "").strip()
            if not value or not pattern.search(value):
                continue
            if slot == "impact" and any(
                conflict.search(value)
                for conflict in (
                    _ANNOUNCEMENT_SLOT_PATTERNS["check"],
                    _ANNOUNCEMENT_SLOT_PATTERNS["caution"],
                    _ANNOUNCEMENT_SLOT_PATTERNS["action"],
                )
            ):
                continue
            return value
    return ""


def _select_announcement_slot_candidate(slot: str, candidates: Sequence[str]) -> str:
    matched = _match_announcement_slot_candidate(slot, candidates)
    if matched:
        return matched
    return _ANNOUNCEMENT_SLOT_DEFAULTS.get(slot, "確認事項")


def _resolve_heading_pool_key(article_type: str, base_template: str) -> str:
    article_type = str(article_type or "").strip().lower()
    base_template = str(base_template or "").strip().lower()
    if article_type == "announcement" or base_template == "announcement":
        return "announcement"
    if article_type == "company_introduction" or base_template == "company_introduction":
        return "company_introduction"
    if article_type == "industry_analysis":
        return "industry_analysis"
    if article_type == "case_study":
        return "case_study"
    if article_type == "comparative_review":
        return "comparative_review"
    if article_type in {"daily_story", "daily_happenings"}:
        return "daily_story"
    if article_type in {"branding", "corporate_culture"} or base_template == "branding":
        return "branding"
    return "balanced"


def _resolve_style_profile_key(article_type: str, focus: str) -> str:
    article_type = str(article_type or "").strip().lower()
    focus = str(focus or "").strip().lower()
    if article_type in {"branding", "corporate_culture"}:
        return "branding"
    if article_type == "industry_analysis":
        return "industry_analysis"
    if article_type == "comparative_review":
        return "comparative_review"
    if article_type == "case_study":
        return "case_study"
    if article_type in {"daily_story", "daily_happenings"}:
        return "daily_story"
    if article_type == "announcement":
        return "announcement"
    if article_type in {"ai", "explanatory_article"} or focus in {"analysis", "explanation"}:
        return "explanatory"
    return "balanced"


def _normalize_focus_item(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    if re.search(r"\d{4}年\d{1,2}月\d{1,2}日", value):
        return value[:40]
    if any(marker in value for marker in ("公式サイトの専用ページ", "既存顧客", "対象", "申し込み", "開始時期")):
        return value[:40]
    terms = _extract_terms(value, limit=4)
    if not terms:
        return value[:24]
    if len(value) <= 18 and len(terms) <= 2:
        return value
    return "、".join(terms[:3])


def _example_grounding_line(style_profile: NaturalStyleProfile) -> str:
    if style_profile.profile_name not in _EXAMPLE_GROUNDED_PROFILES:
        return ""
    return (
        "例や事例を書くなら、日本企業でありそうな匿名の合成事例として書き、"
        "業種・会社規模・部門・現場の摩擦・変更前後のうち2つ以上を入れる。"
        "sourceにない実在企業名・自治体名・サービス名・正確な数値は作らない"
    )


def _needs_legal_citation_guard(section: DiscourseSectionPlan, user_instruction: str) -> bool:
    joined = " ".join(
        [
            str(section.heading or ""),
            str(section.topic_seed or ""),
            str(section.reader_question or ""),
            str(user_instruction or ""),
            *[str(item or "") for item in section.must_cover],
            *[str(item or "") for item in section.related_terms],
        ]
    )
    return any(keyword in joined for keyword in _LEGAL_GUARD_KEYWORDS)


def _legal_citation_guard_line() -> str:
    return (
        "法令名・条文番号・ガイドライン名・判例名は、入力やsourceで確認できるものだけを書く。"
        "確認できない exact 引用は『関連法令』『公的ガイドライン』などの一般表現に落とし、"
        "推測で第◯条や固有名を補わない。入力で法令名だけが与えられている場合も、"
        "正式名称や条文番号へ勝手に展開しない"
    )


def _normalized_term_key(text: str) -> str:
    normalized = _normalize_focus_item(text)
    return re.sub(r"\s+", "", normalized)


def _build_prompt_anchor_terms(
    *,
    must_cover: Sequence[str],
    topic_seed: str,
    related_terms: Sequence[str],
    reader_question: str,
    article_profile: str,
    extra_terms: Sequence[str] | None = None,
    limit: int = 4,
) -> List[str]:
    topic_key = _normalized_term_key(topic_seed)
    must_cover_terms: List[str] = []
    for item in must_cover:
        must_cover_terms.extend(_extract_terms(_normalize_focus_item(str(item or "")), limit=3))
    related_focus: List[str] = []
    for item in related_terms:
        related_focus.extend(_extract_terms(_normalize_focus_item(str(item or "")), limit=2))
    question_terms = _extract_terms(reader_question or "", limit=3)
    topic_terms = _extract_terms(_normalize_focus_item(topic_seed), limit=3)
    extra_focus: List[str] = []
    for item in extra_terms or []:
        if _normalized_term_key(str(item or "")) == topic_key:
            continue
        extra_focus.extend(_extract_terms(_normalize_focus_item(str(item or "")), limit=2))
    budget = _ANCHOR_BUDGETS.get(article_profile, _ANCHOR_BUDGETS["default"])
    preferred = [
        *must_cover_terms[: int(budget.get("must_cover", 0))],
        *topic_terms[: int(budget.get("topic", 0))],
        *related_focus[: int(budget.get("related", 0))],
        *question_terms[: int(budget.get("question", 0))],
        *extra_focus[: int(budget.get("extra", 0))],
    ]
    if len(preferred) < min(2, limit):
        preferred.extend(topic_terms[:1])
    if int(budget.get("order", 0)) == 1:
        preferred = [
            *must_cover_terms[: int(budget.get("must_cover", 0))],
            *related_focus[: int(budget.get("related", 0))],
            *extra_focus[: int(budget.get("extra", 0))],
            *question_terms[: int(budget.get("question", 0))],
            *topic_terms[: int(budget.get("topic", 0))],
        ]
        if len(preferred) < min(2, limit):
            preferred.extend(topic_terms[:1])
    return _dedupe_keep_order(preferred, limit=limit)


def _build_heading_sequence(
    *,
    article_type: str,
    base_template: str,
    section_count: int,
) -> List[tuple[str, str]]:
    section_count = max(5, min(7, int(section_count or 6)))
    pool = list(_HEADING_POOLS[_resolve_heading_pool_key(article_type, base_template)])
    if article_type in {"case_study", "comparative_review"}:
        section_count = min(len(pool), section_count)
    if section_count <= len(pool):
        if section_count == len(pool):
            return pool[:section_count]
        middle_needed = max(0, section_count - 2)
        return [pool[0], *pool[1:1 + middle_needed], pool[-1]]
    sequence = list(pool)
    while len(sequence) < section_count:
        sequence.insert(-1, (f"実務補足 {len(sequence) - 3}", "practice"))
    return sequence[:section_count]


def _compress_case_study_topic_terms(
    *,
    must_cover_items: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    user_prompt: str,
) -> List[str]:
    compact_prompt_terms = _extract_terms(_normalize_focus_item(user_prompt), limit=4)
    compact_thesis_terms = _extract_terms(_normalize_focus_item(thesis), limit=4)
    raw_terms = [
        *must_cover_items,
        *[str(item or "").strip() for item in user_instruction_terms],
        *compact_thesis_terms,
        *compact_prompt_terms,
    ]
    filtered: List[str] = []
    for term in raw_terms:
        compact = str(term or "").strip()
        if not compact:
            continue
        if len(compact) > 18:
            continue
        filtered.append(compact)
    return _dedupe_keep_order(filtered, limit=12)


_GENERAL_TOPIC_META_RE = re.compile(r"(記事|ブログ|投稿|解説記事|含める|判断材|として整理)")
_COMPARATIVE_REVIEW_META_RE = re.compile(r"(記事|ブログ|投稿|まとめ|紹介|比較レビュー)")


def _extract_general_prompt_focus_candidates(text: str) -> List[str]:
    value = str(text or "").strip()
    if not value:
        return []
    first_clause = re.split(r"[。！？\n]", value, maxsplit=1)[0].strip(" 　、。")
    candidates: List[str] = []
    for marker in ("を", "で", "から", "について", "の"):
        if marker not in first_clause:
            continue
        head = first_clause.split(marker, 1)[0].strip(" 　、。")
        if 2 <= len(head) <= 18 and head not in candidates:
            candidates.append(head)
    for term in _extract_terms(first_clause, limit=8):
        if term not in candidates:
            candidates.append(term)
    return candidates


def _compress_general_topic_terms(
    *,
    must_cover_items: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    user_prompt: str,
) -> List[str]:
    raw_terms = [
        *must_cover_items,
        *[str(item or "").strip() for item in user_instruction_terms],
        *_extract_general_prompt_focus_candidates(thesis),
        *_extract_general_prompt_focus_candidates(user_prompt),
    ]
    filtered: List[str] = []
    for term in raw_terms:
        compact = str(term or "").strip()
        if not compact:
            continue
        if len(compact) > 18:
            continue
        if _GENERAL_TOPIC_META_RE.search(compact):
            continue
        filtered.append(compact)
    return _dedupe_keep_order(filtered, limit=14)


def _compress_comparative_review_topic_terms(
    *,
    must_cover_items: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    user_prompt: str,
) -> List[str]:
    compact_prompt_terms = _extract_terms(_normalize_focus_item(user_prompt), limit=4)
    compact_thesis_terms = _extract_terms(_normalize_focus_item(thesis), limit=4)
    raw_terms = [
        *must_cover_items,
        *[str(item or "").strip() for item in user_instruction_terms],
        *compact_thesis_terms,
        *compact_prompt_terms,
    ]
    filtered: List[str] = []
    for term in raw_terms:
        compact = str(term or "").strip()
        if not compact:
            continue
        if len(compact) > 18:
            continue
        if _COMPARATIVE_REVIEW_META_RE.search(compact):
            continue
        filtered.append(compact)
    return _dedupe_keep_order(filtered, limit=14)


def _pick_term_with_keywords(candidates: Sequence[str], keywords: Sequence[str]) -> str:
    normalized = _normalize_prompt_contract_items(candidates, limit=6)
    if not normalized:
        return ""
    for candidate in normalized:
        if any(keyword in candidate for keyword in keywords):
            return candidate
    return normalized[0]


def _pick_focus_carry_term(
    focus: Mapping[str, Any] | None,
    *,
    keywords: Sequence[str],
    prefer_non_generic: bool = False,
    forbidden_keywords: Sequence[str] = (),
) -> str:
    if not isinstance(focus, Mapping):
        return ""
    candidates = [
        *list(focus.get("must_cover") or []),
        *list(focus.get("related_terms") or []),
        str(focus.get("topic_seed") or ""),
    ]
    if prefer_non_generic:
        specific = _pick_non_generic_comparative_term(
            candidates,
            forbidden_keywords=forbidden_keywords,
        )
        if specific:
            return specific
    return _pick_term_with_keywords(candidates, keywords)


def _pick_non_generic_comparative_term(
    candidates: Sequence[str],
    *,
    blocked: Sequence[str] = (),
    forbidden_keywords: Sequence[str] = (),
) -> str:
    blocked_terms = set(_normalize_prompt_contract_items(blocked, limit=12))
    for candidate in _normalize_prompt_contract_items(candidates, limit=8):
        if candidate in blocked_terms:
            continue
        if candidate in _COMPARATIVE_REVIEW_GENERIC_TERMS:
            continue
        if forbidden_keywords and any(keyword in candidate for keyword in forbidden_keywords):
            continue
        return candidate
    return ""


def _match_case_study_terms(intent: str, candidates: Sequence[str], *, limit: int = 3) -> List[str]:
    profile = _CASE_STUDY_INTENT_FOCUS.get(intent, {})
    keywords = tuple(profile.get("keywords") or ())
    matched: List[str] = []
    for candidate in candidates:
        normalized = _normalize_focus_item(candidate or "")
        if not normalized:
            continue
        if any(keyword in normalized for keyword in keywords):
            matched.append(normalized)
    return _dedupe_keep_order(matched, limit=limit)


def _build_case_study_focus_bundle(
    *,
    intent: str,
    heading: str,
    must_cover_items: Sequence[str],
    topic_terms: Sequence[str],
) -> Dict[str, List[str] | str]:
    profile = dict(_CASE_STUDY_INTENT_FOCUS.get(intent, {}) or {})
    default_topic_seed = str(profile.get("default_topic_seed") or heading or "課題")
    required_terms = [str(item or "").strip() for item in profile.get("required_terms", []) if str(item or "").strip()]
    candidates = [heading, *must_cover_items, *topic_terms]
    matched = _match_case_study_terms(intent, candidates, limit=3)
    required_first = intent in _CASE_STUDY_REQUIRED_FIRST_INTENTS
    topic_seed_candidates = [*required_terms, *matched] if required_first else list(matched)
    topic_seed = next((item for item in topic_seed_candidates if str(item or "").strip()), default_topic_seed)
    must_cover = _dedupe_keep_order(
        [*required_terms, *matched] if required_first else [*matched[:2], *required_terms],
        limit=3,
    )
    related_terms = _dedupe_keep_order(
        [
            topic_seed,
            *must_cover,
            *topic_terms[:2],
        ],
        limit=4,
    )
    return {
        "topic_seed": topic_seed,
        "must_cover": must_cover,
        "related_terms": related_terms,
    }


def _match_comparative_review_terms(intent: str, candidates: Sequence[str], *, limit: int = 3) -> List[str]:
    profile = _COMPARATIVE_REVIEW_INTENT_FOCUS.get(intent, {})
    keywords = tuple(profile.get("keywords") or ())
    matched: List[str] = []
    for candidate in candidates:
        normalized = _normalize_focus_item(candidate or "")
        if not normalized:
            continue
        if any(keyword in normalized for keyword in keywords):
            matched.append(normalized)
    return _dedupe_keep_order(matched, limit=limit)


def _build_comparative_review_focus_bundle(
    *,
    intent: str,
    heading: str,
    must_cover_items: Sequence[str],
    topic_terms: Sequence[str],
) -> Dict[str, List[str] | str]:
    profile = dict(_COMPARATIVE_REVIEW_INTENT_FOCUS.get(intent, {}) or {})
    default_topic_seed = str(profile.get("default_topic_seed") or heading or "比較条件")
    required_terms = [str(item or "").strip() for item in profile.get("required_terms", []) if str(item or "").strip()]
    candidates = [heading, *must_cover_items, *topic_terms]
    matched = _match_comparative_review_terms(intent, candidates, limit=3)
    required_first = intent in _COMPARATIVE_REVIEW_REQUIRED_FIRST_INTENTS
    topic_seed_candidates = [*required_terms, *matched] if required_first else list(matched)
    topic_seed = next((item for item in topic_seed_candidates if str(item or "").strip()), default_topic_seed)
    must_cover = _dedupe_keep_order(
        [*required_terms, *matched] if required_first else [*matched[:2], *required_terms],
        limit=3,
    )
    related_terms = _dedupe_keep_order(
        [
            topic_seed,
            *must_cover,
            *(
                [
                    _pick_non_generic_comparative_term(
                        topic_terms,
                        blocked=[heading, topic_seed, *must_cover, *matched],
                        forbidden_keywords=("用途", "向く", "向か"),
                    )
                ]
                if intent in {"criteria", "comparison", "fit"}
                else []
            ),
        ],
        limit=4,
    )
    return {
        "topic_seed": topic_seed,
        "must_cover": must_cover,
        "related_terms": related_terms,
    }


def _normalize_prompt_contract_items(values: Sequence[Any], *, limit: int = 4) -> List[str]:
    normalized: List[str] = []
    for item in values:
        value = _normalize_focus_item(str(item or "")) or str(item or "").strip()
        if not value or value in normalized:
            continue
        normalized.append(value)
        if len(normalized) >= limit:
            break
    return normalized


_OVERLITERAL_SECTION_INSTRUCTION_RE = re.compile(
    r"(含める|解説記事|業界分析|比較レビュー|日常記事|記事|ブログ|まとめ|(?:企業|会社|自社)(?:の)?紹介)"
)


def _is_overliteral_section_instruction(text: str, *, topic: str = "") -> bool:
    value = str(text or "").strip()
    raw_topic = str(topic or "").strip()
    if not value:
        return False
    if raw_topic and value == raw_topic and len(value) > 18:
        return True
    if len(value) > 32:
        return True
    if "。" in value and len(value) > 18:
        return True
    if _OVERLITERAL_SECTION_INSTRUCTION_RE.search(value):
        return True
    return False


def _resolve_local_section_instruction(section: DiscourseSectionPlan) -> str:
    candidates = _normalize_prompt_contract_items(
        [section.topic_seed, *list(section.must_cover or [])[:2]],
        limit=3,
    )
    if candidates:
        return candidates[0]
    return str(section.topic_seed or section.reader_question or "").strip()


def _collect_previous_section_terms(
    discourse_sections: Sequence[DiscourseSectionPlan],
    *,
    section_index: int,
    intents: Sequence[str],
    limit: int = 3,
) -> List[str]:
    intent_keys = {str(intent or "").strip().lower() for intent in intents if str(intent or "").strip()}
    if not intent_keys or section_index <= 0:
        return []
    collected: List[str] = []
    for previous in reversed(list(discourse_sections[:section_index])):
        if str(previous.intent or "").strip().lower() not in intent_keys:
            continue
        candidates = [
            previous.topic_seed,
            previous.reader_question,
            *list(previous.must_cover or []),
            *list(previous.related_terms or []),
        ]
        for candidate in _normalize_prompt_contract_items(candidates, limit=6):
            if candidate not in collected:
                collected.append(candidate)
            if len(collected) >= limit:
                return collected
    return collected


def _resolve_note4000_section_user_instruction(
    *,
    section: DiscourseSectionPlan,
    topic: str,
    article_type: str,
    topic_statement: str,
    narrative_axis: str,
    focus_bundle: Mapping[str, Any],
    source_grounding_required: bool,
    prompt_context_items: Sequence[str],
) -> str:
    main_focus = str(focus_bundle.get("main_focus") or "").strip()
    local_instruction = _resolve_local_section_instruction(section)
    if article_type == "announcement":
        if str(section.fact_slot or "").strip().lower() not in {"", "change"} and local_instruction:
            return local_instruction
        for candidate in [
            main_focus,
            topic_statement,
            re.split(r"[。！？\n]", str(topic or ""), maxsplit=1)[0],
            local_instruction,
        ]:
            value = str(candidate or "").strip()
            if value:
                return value
        return str(topic or "").strip()
    if article_type == "comparative_review":
        if local_instruction:
            return local_instruction
        for candidate in [main_focus, topic_statement, narrative_axis]:
            value = str(candidate or "").strip()
            if value and not _is_overliteral_section_instruction(value, topic=topic):
                return value
        return str(topic or "").strip()
    if article_type in {"explanatory_article", "daily_story", "industry_analysis"}:
        if local_instruction:
            return local_instruction
        for candidate in [main_focus, topic_statement, narrative_axis]:
            value = str(candidate or "").strip()
            if value and not _is_overliteral_section_instruction(value, topic=topic):
                return value
        return str(topic or "").strip()
    if article_type == "case_study":
        if local_instruction:
            return local_instruction
        for candidate in [main_focus, topic_statement, narrative_axis]:
            value = str(candidate or "").strip()
            if value:
                return value
        return str(topic or "").strip()
    if article_type != "branding" or not source_grounding_required:
        return str(topic or "").strip()
    if local_instruction and not _is_overliteral_section_instruction(local_instruction, topic=topic):
        return local_instruction
    parts: List[str] = []
    for candidate in [main_focus, topic_statement, *list(prompt_context_items or [])[:2]]:
        value = str(candidate or "").strip()
        if value and value not in parts and not _is_overliteral_section_instruction(value, topic=topic):
            parts.append(value)
    if parts:
        return "。".join(parts)
    if local_instruction:
        return local_instruction
    return str(topic or "").strip()


def _reader_question_anchor_terms(reader_question: str, *, limit: int = 2) -> List[str]:
    compact = _normalize_focus_item(str(reader_question or ""))
    if not compact or _is_overliteral_section_instruction(compact):
        return []
    return _extract_terms(compact, limit=limit)


def _resolve_note4000_section_instruction_anchor_terms(
    *,
    section: DiscourseSectionPlan,
    article_type: str,
    section_index: int,
    discourse_sections: Sequence[DiscourseSectionPlan],
    source_grounding_required: bool,
    prompt_context_items: Sequence[str],
) -> List[str]:
    anchors = _normalize_prompt_contract_items(section.must_cover, limit=4)
    if article_type == "case_study":
        if section.intent == "change":
            anchors = _normalize_prompt_contract_items(
                [
                    "何が変わったか",
                    "変化した状態",
                    *anchors,
                    section.topic_seed,
                    *_reader_question_anchor_terms(section.reader_question, limit=2),
                ],
                limit=4,
            )
        elif section.intent == "condition":
            anchors = _normalize_prompt_contract_items(
                [
                    "再現条件",
                    "前提",
                    "限界",
                    *anchors,
                    *_collect_previous_section_terms(
                        discourse_sections,
                        section_index=section_index,
                        intents=("change",),
                        limit=1,
                    ),
                    section.topic_seed,
                    *_reader_question_anchor_terms(section.reader_question, limit=2),
                ],
                limit=4,
            )
        else:
            anchors = _normalize_prompt_contract_items(
                [
                    *anchors,
                    section.topic_seed,
                    *_reader_question_anchor_terms(section.reader_question, limit=2),
                ],
                limit=4,
            )
    elif article_type == "comparative_review":
        local_must_cover = [
            item
            for item in list(section.must_cover or [])
            if str(item or "").strip() and str(item or "").strip() != str(section.heading or "").strip()
        ]
        anchors = _normalize_prompt_contract_items(
            [
                *local_must_cover[:2],
                *_reader_question_anchor_terms(section.reader_question, limit=2),
                *list(section.related_terms or []),
                section.topic_seed,
            ],
            limit=4,
        )
    elif article_type == "branding" and source_grounding_required:
        anchors = _normalize_prompt_contract_items(
            [*anchors, *list(prompt_context_items or [])[:1]],
            limit=4,
        )
    return anchors


def resolve_note4000_section_prompt_contract(
    *,
    section: DiscourseSectionPlan,
    section_index: int,
    discourse_sections: Sequence[DiscourseSectionPlan],
    contract: Mapping[str, Any],
) -> Dict[str, Any]:
    focus_bundle = dict(contract.get("focus_bundle", {}) or {})
    prompt_context_items = _normalize_prompt_contract_items(
        contract.get("prompt_context_items", []) or [],
        limit=3,
    )
    article_type = str(contract.get("article_type") or "").strip().lower()
    return {
        "user_instruction": _resolve_note4000_section_user_instruction(
            section=section,
            topic=str(contract.get("topic") or ""),
            article_type=article_type,
            topic_statement=str(contract.get("topic_statement") or ""),
            narrative_axis=str(contract.get("narrative_axis") or ""),
            focus_bundle=focus_bundle,
            source_grounding_required=bool(contract.get("source_grounding_required")),
            prompt_context_items=prompt_context_items,
        ),
        "instruction_anchor_terms": _resolve_note4000_section_instruction_anchor_terms(
            section=section,
            article_type=article_type,
            section_index=section_index,
            discourse_sections=discourse_sections,
            source_grounding_required=bool(contract.get("source_grounding_required")),
            prompt_context_items=prompt_context_items,
        ),
    }


def _compress_industry_analysis_topic_terms(
    *,
    must_cover_items: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    user_prompt: str,
) -> List[str]:
    compact_prompt_terms = _extract_terms(_normalize_focus_item(user_prompt), limit=3)
    compact_thesis_terms = _extract_terms(_normalize_focus_item(thesis), limit=4)
    raw_terms = [
        *must_cover_items,
        *[str(item or "").strip() for item in user_instruction_terms],
        *compact_thesis_terms,
        *compact_prompt_terms,
    ]
    filtered: List[str] = []
    for term in raw_terms:
        compact = str(term or "").strip()
        if not compact:
            continue
        if len(compact) > 16:
            continue
        if re.search(r"(記事|投稿|ブログ|まとめ|整理)", compact):
            continue
        filtered.append(compact)
    return _dedupe_keep_order(filtered, limit=12)


def _kotodesu_policy_line(style_profile: NaturalStyleProfile, intent: str) -> str:
    profile = str(style_profile.profile_name or "")
    intent_key = str(intent or "").strip().lower()
    return _KOTODESU_POLICIES.get(profile, {}).get(intent_key, "")


def _intent_local_rule(
    style_profile: NaturalStyleProfile,
    intent: str,
    fact_slot: str = "",
) -> str:
    profile = str(style_profile.profile_name or "")
    intent_key = str(intent or "").strip().lower()
    return _INTENT_LOCAL_RULES.get(profile, {}).get(intent_key, "")


def build_note4000_style_profile(
    *,
    article_type: str,
    focus: str,
    tone_profile: str,
    style_profile: str,
    base_register: str,
) -> NaturalStyleProfile:
    article_type = str(article_type or "").strip().lower()
    focus = str(focus or "").strip().lower()
    style_profile = str(style_profile or "").strip().lower()
    base_register = str(base_register or "polite").strip().lower() or "polite"
    resolved_key = _resolve_style_profile_key(article_type, focus)
    config = dict(_STYLE_PROFILE_DEFAULTS)
    override = dict(_STYLE_PROFILE_OVERRIDES.get(resolved_key, {}))
    prompt_rules = list(config.pop("prompt_rules", []))
    override_prompt_rules = list(override.pop("prompt_rules", []))
    if override.pop("reset_prompt_rules", False):
        prompt_rules = override_prompt_rules
    else:
        prompt_rules.extend(override_prompt_rules)
    preferred_endings = list(config.pop("preferred_endings", []))
    preferred_endings_override = list(override.pop("preferred_endings", []))
    if preferred_endings_override:
        preferred_endings = preferred_endings_override
    config.update(override)
    article_tone = str(config["article_tone"])
    if style_profile == "casual":
        article_tone = "casual_reader"
    if style_profile == "casual":
        preferred_endings.extend(["だ。", "と思います。"])
    banned_openings = [
        "結論から言うと",
        "重要なのは",
        "今回は",
        "本記事では",
    ]
    banned_openings.extend(_STYLE_PROFILE_OVERRIDES.get(resolved_key, {}).get("banned_openings_extra", []))
    if tone_profile == "passionate":
        prompt_rules.append("勢いよりも具体性を優先し、煽りは避ける")
    return NaturalStyleProfile(
        profile_name=str(config["profile_name"]),
        article_tone=article_tone,
        base_register=base_register,
        linebreak_profile=str(config["linebreak_profile"]),
        paragraph_min=int(config["paragraph_min"]),
        paragraph_max=int(config["paragraph_max"]),
        sentence_length_mix=str(config["sentence_length_mix"]),
        opening_variation_target=str(config["opening_variation_target"]),
        information_density=str(config["information_density"]),
        punctuation_profile=str(config["punctuation_profile"]),
        subject_omission_policy=str(config["subject_omission_policy"]),
        paragraph_break_policy=str(config["paragraph_break_policy"]),
        ending_distribution_hint=str(config["ending_distribution_hint"]),
        preferred_endings=_dedupe_keep_order(preferred_endings, limit=6),
        prompt_rules=prompt_rules,
        banned_openings=banned_openings,
    )


def build_note4000_length_plan(
    *,
    length_mode: str,
    section_count: int,
    max_section_count: int | None = None,
) -> Dict[str, Any]:
    length_mode = str(length_mode or "adaptive").strip().lower() or "adaptive"
    targets_by_mode = {
        "adaptive": {"note_chars": 2600, "lead_chars": 140, "cta_chars": 90, "section_count": 5},
        "short": {"note_chars": 1800, "lead_chars": 120, "cta_chars": 80, "section_count": 4},
        "normal": {"note_chars": 4000, "lead_chars": 170, "cta_chars": 130, "section_count": 6},
        "long": {"note_chars": 4600, "lead_chars": 190, "cta_chars": 150, "section_count": 7},
    }
    base_targets = dict(targets_by_mode.get(length_mode, targets_by_mode["normal"]))
    min_sections = 4 if length_mode == "short" else 5
    section_count_target = max(min_sections, min(7, max(int(section_count or 0), int(base_targets["section_count"]))))
    if max_section_count is not None:
        section_count_target = max(min_sections, min(int(max_section_count), section_count_target))
    note_target_chars = int(base_targets["note_chars"])
    lead_target_chars = int(base_targets["lead_chars"])
    cta_target_chars = int(base_targets["cta_chars"])
    min_body_chars = 1200 if length_mode == "short" else 2400
    body_target_chars = max(min_body_chars, note_target_chars - lead_target_chars - cta_target_chars)
    weights_by_count: Dict[int, List[float]] = {
        4: [0.22, 0.30, 0.28, 0.20],
        5: [0.16, 0.22, 0.24, 0.22, 0.16],
        6: [0.14, 0.18, 0.20, 0.19, 0.17, 0.12],
        7: [0.12, 0.16, 0.18, 0.18, 0.16, 0.12, 0.08],
    }
    weights = weights_by_count.get(section_count_target, weights_by_count[6])
    sentence_ranges = {
        "adaptive": (3, 5),
        "short": (3, 5),
        "normal": (4, 6),
        "long": (4, 7),
    }
    sentence_min, sentence_max = sentence_ranges.get(length_mode, (4, 6))
    token_bounds = {
        "adaptive": (620, 960),
        "short": (540, 860),
        "normal": (700, 1080),
        "long": (820, 1240),
    }
    token_min, token_max = token_bounds.get(length_mode, (700, 1080))
    section_plans: List[Dict[str, int]] = []
    allocated = 0
    for idx, weight in enumerate(weights):
        if idx == len(weights) - 1:
            target_chars = max(280, body_target_chars - allocated)
        else:
            target_chars = max(280, int(round(body_target_chars * weight)))
            allocated += target_chars
        min_chars = max(220, int(target_chars * 0.72))
        max_chars = max(min_chars + 80, int(target_chars * 1.2))
        max_tokens = int(max(token_min, min(token_max, int(target_chars * 1.22))))
        section_plans.append(
            {
                "target_chars": target_chars,
                "min_chars": min_chars,
                "max_chars": max_chars,
                "max_tokens": max_tokens,
                "sentence_min": sentence_min,
                "sentence_max": sentence_max,
            }
        )
    return {
        "mode": length_mode,
        "planner": "note_4000",
        "targets": {
            "note_chars": note_target_chars,
            "lead_chars": lead_target_chars,
            "body_chars": body_target_chars,
            "cta_chars": cta_target_chars,
            "section_count_target": section_count_target,
        },
        "section_plans": section_plans,
        "sentence_range": {"min": sentence_min, "max": sentence_max},
        "actual": {},
    }


def build_note4000_discourse_plan(
    *,
    article_type: str,
    base_template: str,
    user_prompt: str,
    must_cover: Sequence[str],
    user_instruction_terms: Sequence[str],
    thesis: str,
    reader_question_candidates: Sequence[str],
    length_plan: Dict[str, Any],
    source_grounding_items: Sequence[Mapping[str, Any]] | None = None,
) -> List[DiscourseSectionPlan]:
    announcement_like = article_type == "announcement" or base_template == "announcement"
    company_intro_like = article_type == "company_introduction" or base_template == "company_introduction"
    company_intro_blank_prompt = company_intro_like and not str(user_prompt or "").strip()
    targets = dict(length_plan.get("targets", {}) or {})
    section_count = int(targets.get("section_count_target", 6) or 6)
    company_intro_slot_order: List[str] = []
    company_intro_reader_question_candidates: List[str] = []
    if company_intro_like:
        company_intro_slot_order = _build_company_intro_slot_order(
            section_count=section_count,
            source_grounding_items=source_grounding_items,
            prefer_current_first=company_intro_blank_prompt,
        )
        company_intro_reader_question_candidates = [
            _COMPANY_INTRO_SLOT_SPECS[slot_key]["reader_question"]
            for slot_key in company_intro_slot_order
        ]
        heading_sequence = [
            (
                _COMPANY_INTRO_SLOT_SPECS[slot_key]["heading"],
                _COMPANY_INTRO_SLOT_SPECS[slot_key]["intent"],
            )
            for slot_key in company_intro_slot_order
        ]
    else:
        heading_sequence = _build_heading_sequence(
            article_type=article_type,
            base_template=base_template,
            section_count=section_count,
        )
    must_cover_items = _dedupe_keep_order((_normalize_focus_item(str(item or "").strip()) for item in must_cover), limit=12)
    if article_type == "case_study":
        topic_terms = _compress_case_study_topic_terms(
            must_cover_items=must_cover_items,
            user_instruction_terms=user_instruction_terms,
            thesis=thesis,
            user_prompt=user_prompt,
        )
    elif article_type == "comparative_review":
        topic_terms = _compress_comparative_review_topic_terms(
            must_cover_items=must_cover_items,
            user_instruction_terms=user_instruction_terms,
            thesis=thesis,
            user_prompt=user_prompt,
        )
    elif article_type == "industry_analysis":
        topic_terms = _compress_industry_analysis_topic_terms(
            must_cover_items=must_cover_items,
            user_instruction_terms=user_instruction_terms,
            thesis=thesis,
            user_prompt=user_prompt,
        )
    elif (
        article_type in {"branding", "corporate_culture", "company_introduction"}
        or base_template in {"branding", "company_introduction"}
    ):
        topic_terms = _compress_branding_topic_terms(
            must_cover_items=must_cover_items,
            user_instruction_terms=user_instruction_terms,
            thesis=thesis,
            user_prompt=user_prompt,
        )
        if company_intro_like:
            topic_terms = _build_company_intro_topic_terms(
                must_cover_items=must_cover_items,
                topic_terms=topic_terms,
                source_grounding_items=source_grounding_items,
            )
    else:
        topic_terms = _compress_general_topic_terms(
            must_cover_items=must_cover_items,
            user_instruction_terms=user_instruction_terms,
            thesis=thesis,
            user_prompt=user_prompt,
        )
    if not topic_terms:
        if company_intro_like:
            topic_terms = _build_company_intro_topic_terms(
                must_cover_items=must_cover_items,
                topic_terms=[],
                source_grounding_items=source_grounding_items,
            )
        else:
            topic_terms = ["読者が判断しやすくなる視点", "現場で使える進め方", "次の一歩"]
    if announcement_like:
        announcement_candidates = _collect_announcement_candidates(
            must_cover_items=must_cover_items,
            user_instruction_terms=user_instruction_terms,
            thesis=thesis,
            user_prompt=user_prompt,
        )
        must_cover_items = [
            item
            for item in must_cover_items
            if item and not _announcement_meta_fragment(item)
        ]
        slot_order = ["change", "who_when", "impact", "check", "caution", "action"]
        slot_seed_map: Dict[str, str] = {}
        remaining_candidates = list(announcement_candidates)
        for slot in slot_order:
            selected = _select_announcement_slot_candidate(slot, remaining_candidates)
            slot_seed_map[slot] = selected
            if selected in remaining_candidates:
                remaining_candidates.remove(selected)
        slot_must_cover_map: Dict[str, str] = {}
        remaining_must_cover = list(must_cover_items)
        for slot in slot_order:
            matched_must_cover = _match_announcement_slot_candidate(slot, remaining_must_cover)
            slot_must_cover_map[slot] = matched_must_cover
            if matched_must_cover in remaining_must_cover:
                remaining_must_cover.remove(matched_must_cover)
        slot_extra_must_cover_map: Dict[str, List[str]] = {slot: [] for slot in slot_order}
        extra_slot_order = ["impact", "check", "caution", "action", "who_when", "change"]
        for item in remaining_must_cover:
            compact = str(item or "").strip()
            if not compact:
                continue
            for slot in extra_slot_order:
                if compact == str(slot_seed_map.get(slot) or "").strip():
                    continue
                if compact == str(slot_must_cover_map.get(slot) or "").strip():
                    continue
                if compact in slot_extra_must_cover_map[slot]:
                    continue
                slot_extra_must_cover_map[slot].append(compact)
                break
    section_plans = list(length_plan.get("section_plans", []) or [])
    discourse: List[DiscourseSectionPlan] = []
    direction_family = _infer_direction_family(article_type=article_type, base_template=base_template)
    case_change_focus: Dict[str, List[str] | str] | None = None
    comparative_criteria_focus: Dict[str, List[str] | str] | None = None
    comparative_comparison_focus: Dict[str, List[str] | str] | None = None
    comparative_fit_focus: Dict[str, List[str] | str] | None = None
    comparative_caution_focus: Dict[str, List[str] | str] | None = None
    for idx, (heading, intent) in enumerate(heading_sequence):
        section_length = section_plans[idx] if idx < len(section_plans) else {}
        case_study_focus: Dict[str, List[str] | str] | None = None
        comparative_focus: Dict[str, List[str] | str] | None = None
        if announcement_like:
            slot = _announcement_fact_slot_for_index(idx)
            slot_order = ["change", "who_when", "impact", "check", "caution", "action"]
            topic_seed = slot_seed_map.get(slot) or _ANNOUNCEMENT_SLOT_DEFAULTS.get(slot, "確認事項")
            matched_must_cover = slot_must_cover_map.get(slot, "")
            related_terms = _dedupe_keep_order(
                [
                    topic_seed,
                    matched_must_cover,
                    *[
                        slot_seed_map.get(next_slot, _ANNOUNCEMENT_SLOT_DEFAULTS.get(next_slot, "確認事項"))
                        for next_slot in slot_order[idx + 1: idx + 3]
                    ],
                ]
                or [topic_seed],
                limit=3,
            )
        elif company_intro_like:
            slot_key = (
                company_intro_slot_order[min(idx, len(company_intro_slot_order) - 1)]
                if company_intro_slot_order
                else "closing"
            )
            slot_spec = _COMPANY_INTRO_SLOT_SPECS.get(slot_key, _COMPANY_INTRO_SLOT_SPECS["closing"])
            slot_default_seed = (
                _normalize_focus_item(slot_spec.get("topic_seed"))
                or _normalize_focus_item(heading)
                or heading
                or _COMPANY_INTRO_CORE_DEFAULTS[-1]
            )
            fallback_seed = (
                topic_terms[-1]
                if slot_key == "closing" and topic_terms
                else (
                    topic_terms[-1]
                    if list(source_grounding_items or []) and topic_terms
                    else slot_default_seed
                )
            )
            preferred_slot_seed = ""
            if company_intro_blank_prompt and company_intro_slot_order[:1] != ["outline"] and slot_key != "closing":
                preferred_slot_seed = (
                    must_cover_items[idx]
                    if idx < len(must_cover_items)
                    else slot_default_seed
                )
            topic_seed = (
                topic_terms[-1]
                if slot_key == "closing" and topic_terms
                else preferred_slot_seed
                if preferred_slot_seed
                else topic_terms[idx]
                if idx < len(topic_terms)
                else fallback_seed
            )
            related_terms = _dedupe_keep_order(
                [
                    topic_seed,
                    *topic_terms[max(0, idx - 1): idx + 2],
                    *must_cover_items[:2],
                ],
                limit=4,
            )
        elif article_type == "case_study":
            case_study_focus = _build_case_study_focus_bundle(
                intent=intent,
                heading=heading,
                must_cover_items=must_cover_items,
                topic_terms=topic_terms,
            )
            topic_seed = str(case_study_focus.get("topic_seed") or heading)
            related_terms = list(case_study_focus.get("related_terms") or [])
            if intent == "condition" and case_change_focus:
                related_terms = _dedupe_keep_order(
                    [
                        str(case_change_focus.get("topic_seed") or ""),
                        *related_terms,
                    ],
                    limit=4,
                )
            else:
                related_terms = _dedupe_keep_order(related_terms, limit=4)
        elif article_type == "comparative_review":
            comparative_focus = _build_comparative_review_focus_bundle(
                intent=intent,
                heading=heading,
                must_cover_items=must_cover_items,
                topic_terms=topic_terms,
            )
            topic_seed = str(comparative_focus.get("topic_seed") or heading)
            related_terms = list(comparative_focus.get("related_terms") or [])
            carry_terms: List[str] = []
            criteria_carry = _pick_focus_carry_term(
                comparative_criteria_focus,
                keywords=("評価軸", "判断基準", "比較条件"),
                prefer_non_generic=True,
                forbidden_keywords=("用途", "向く", "向か", "比較条件", "そろえ", "評価軸", "判断基準"),
            )
            if intent == "comparison":
                if criteria_carry:
                    carry_terms.append(criteria_carry)
            elif intent == "fit":
                comparison_carry = _pick_focus_carry_term(
                    comparative_comparison_focus,
                    keywords=("差分", "強み", "弱み"),
                )
                for value in [comparison_carry, criteria_carry]:
                    if value and value not in carry_terms:
                        carry_terms.append(value)
            elif intent == "caution":
                fit_focus_candidates: List[str] = []
                if isinstance(comparative_fit_focus, Mapping):
                    fit_focus_candidates.extend(list(comparative_fit_focus.get("must_cover") or []))
                    fit_focus_candidates.extend(list(comparative_fit_focus.get("related_terms") or []))
                    fit_focus_candidates.append(str(comparative_fit_focus.get("topic_seed") or ""))
                fit_carry = ""
                for candidate in _normalize_prompt_contract_items(fit_focus_candidates, limit=8):
                    if candidate == "用途別":
                        continue
                    if any(keyword in candidate for keyword in ("向くケース", "向かないケース", "向く", "向か")):
                        fit_carry = candidate
                        break
                if not fit_carry:
                    fit_carry = _pick_focus_carry_term(
                        comparative_fit_focus,
                        keywords=("用途", "向く", "向か"),
                    )
                for value in [fit_carry, criteria_carry]:
                    if value and value not in carry_terms:
                        carry_terms.append(value)
            elif intent == "closing":
                criteria_focus_candidates: List[str] = []
                if isinstance(comparative_criteria_focus, Mapping):
                    criteria_focus_candidates.extend(list(comparative_criteria_focus.get("must_cover") or []))
                    criteria_focus_candidates.extend(list(comparative_criteria_focus.get("related_terms") or []))
                    criteria_focus_candidates.append(str(comparative_criteria_focus.get("topic_seed") or ""))
                specific_criteria_carry = _pick_non_generic_comparative_term(
                    criteria_focus_candidates,
                    blocked=["評価軸", "判断基準", "比較条件", "結論", "おすすめの分け方"],
                    forbidden_keywords=("用途", "向く", "向か", "比較条件", "そろえ", "評価軸", "判断基準"),
                )
                caution_carry = _pick_focus_carry_term(
                    comparative_caution_focus,
                    keywords=("前提", "例外", "移行コスト"),
                )
                fit_carry = _pick_focus_carry_term(
                    comparative_fit_focus,
                    keywords=("用途", "向く", "向か"),
                )
                for value in [caution_carry, specific_criteria_carry or fit_carry, criteria_carry]:
                    if value and value not in carry_terms:
                        carry_terms.append(value)
            if carry_terms:
                related_terms = _dedupe_keep_order(
                    [
                        *carry_terms,
                        *related_terms,
                    ],
                    limit=4,
                )
            else:
                related_terms = _dedupe_keep_order(related_terms, limit=4)
        elif article_type == "industry_analysis":
            topic_seed = topic_terms[idx] if idx < len(topic_terms) else topic_terms[min(len(topic_terms) - 1, idx % len(topic_terms))]
            related_terms = _dedupe_keep_order(
                [
                    topic_seed,
                    *topic_terms[idx + 1: idx + 2],
                    *must_cover_items[max(0, idx - 1): idx + 1],
                ],
                limit=3,
            )
        else:
            topic_seed = topic_terms[idx] if idx < len(topic_terms) else topic_terms[min(len(topic_terms) - 1, idx % len(topic_terms))]
            related_terms = _dedupe_keep_order(
                topic_terms[max(0, idx - 1): idx + 3],
                limit=4,
            )
        must_cover_for_section = []
        if announcement_like:
            slot = _announcement_fact_slot_for_index(idx)
            matched_must_cover = slot_must_cover_map.get(slot, "")
            if matched_must_cover:
                must_cover_for_section.append(matched_must_cover)
            must_cover_for_section.extend(list(slot_extra_must_cover_map.get(slot) or []))
        elif article_type == "case_study":
            must_cover_for_section.extend(list((case_study_focus or {}).get("must_cover") or []))
        elif article_type == "comparative_review":
            must_cover_for_section.extend(list((comparative_focus or {}).get("must_cover") or []))
        elif idx < len(must_cover_items):
            must_cover_for_section.append(must_cover_items[idx])
        elif must_cover_items:
            must_cover_for_section.append(must_cover_items[idx % len(must_cover_items)])
        must_cover_for_section = _dedupe_keep_order(must_cover_for_section, limit=3)
        if announcement_like:
            bridge_defaults = [
                "次に対象者と開始時期を確認する",
                "次に利用者への影響を確認する",
                "次に確認事項を整理する",
                "次に移行時の注意点を確認する",
                "最後に公式情報の確認先を整理する",
            ]
            bridge_hint = bridge_defaults[min(idx, len(bridge_defaults) - 1)]
        elif company_intro_like:
            slot_key = (
                company_intro_slot_order[min(idx, len(company_intro_slot_order) - 1)]
                if company_intro_slot_order
                else "closing"
            )
            bridge_hint = _COMPANY_INTRO_SLOT_SPECS.get(slot_key, _COMPANY_INTRO_SLOT_SPECS["closing"]).get("bridge_hint", "")
        elif article_type == "case_study":
            bridge_defaults = [
                "導入で、最初にどこに課題があったかを短く置く",
                "次に迷いが生まれた場面を切り分け、原因を抽象化しすぎない",
                "次に進め方をどう組み替えたかを順番で示す",
                "次に途中で効いた工夫を置き、結果節へ流す",
                "次に何が変わったかを状態変化で示し、再現条件へ渡す",
                "最後に再現条件、前提、限界を残し、成功談だけで閉じない",
            ]
            bridge_hint = bridge_defaults[min(idx, len(bridge_defaults) - 1)]
        elif article_type == "industry_analysis":
            bridge_defaults = [
                "導入で、まず市場の前提と観測点をそろえる",
                "次に起きている構造変化を背景要因ごとに分ける",
                "次に主要プレイヤーの差分を比較軸で整理する",
                "次に意思決定で見るべき指標を絞り込む",
                "次に直近のリスクを示し、最後の示唆へ渡す",
                "最後に本文の要点を繰り返さず、次の判断に使う視点で結ぶ",
            ]
            bridge_hint = bridge_defaults[min(idx, len(bridge_defaults) - 1)]
        elif article_type == "comparative_review":
            bridge_defaults = [
                "導入で、まず比較対象と前提条件をそろえる",
                "次に評価軸を定義し、途中で軸をずらさない",
                "次に候補ごとの差分を同じ軸で整理する",
                "次に用途別の向き不向きを分ける",
                "次に前提、移行コスト、例外を置いて最後の結論へ渡す",
                "最後に一律の優劣ではなく、用途別に結論を分けて結ぶ",
            ]
            bridge_hint = bridge_defaults[min(idx, len(bridge_defaults) - 1)]
        else:
            bridge_hint = (
                "前段の要点を繰り返さず、この節で初めて必要になる判断材料を置く"
                if idx > 0
                else "導入で最初に置く前提と問題意識を立ち上げる"
            )
            if idx == len(heading_sequence) - 1:
                bridge_hint = "本文の要点をなぞるだけで終えず、次の判断や一歩につなげる"
        reader_question = ""
        if company_intro_like and idx < len(company_intro_reader_question_candidates):
            reader_question = str(company_intro_reader_question_candidates[idx] or "").strip()
        elif idx < len(reader_question_candidates):
            reader_question = str(reader_question_candidates[idx] or "").strip()
        if not reader_question:
            if announcement_like:
                reader_defaults = [
                    "何が変わるか",
                    "いつから・誰が対象か",
                    "利用者への影響は何か",
                    "何を確認すべきか",
                    "移行時の注意点は何か",
                    "公式情報の確認先はどこか",
                ]
                reader_question = reader_defaults[min(idx, len(reader_defaults) - 1)]
            elif company_intro_like:
                slot_key = (
                    company_intro_slot_order[min(idx, len(company_intro_slot_order) - 1)]
                    if company_intro_slot_order
                    else "closing"
                )
                reader_question = _COMPANY_INTRO_SLOT_SPECS.get(slot_key, _COMPANY_INTRO_SLOT_SPECS["closing"]).get("reader_question", "")
            elif article_type == "case_study":
                reader_defaults = [
                    "最初にどこでつまずいていたか",
                    "迷いはどの場面で生まれていたか",
                    "進め方をどう組み替えたか",
                    "途中で何が効いたか",
                    "結果として何が変わったか",
                    "どの条件なら再現できるか",
                ]
                reader_question = reader_defaults[min(idx, len(reader_defaults) - 1)]
            elif article_type == "industry_analysis":
                reader_defaults = [
                    "何を前提として見ればよいか",
                    "いま何が変化しているのか",
                    "主要プレイヤーはどこが違うのか",
                    "何を基準に判断すべきか",
                    "直近でどんなリスクがあるか",
                    "次の判断にどうつなげるか",
                ]
                reader_question = reader_defaults[min(idx, len(reader_defaults) - 1)]
            elif article_type == "comparative_review":
                reader_defaults = [
                    "比較の前提条件は何か",
                    "どの評価軸で比べるべきか",
                    "候補ごとの差分は何か",
                    "どの用途に向いているか",
                    "選ぶ前に何を確認すべきか",
                    "用途別にどう結論づけるか",
                ]
                reader_question = reader_defaults[min(idx, len(reader_defaults) - 1)]
            else:
                reader_defaults = [
                    "何を先に理解するか",
                    "どこで判断を誤りやすいか",
                    "何を基準に線引きするか",
                    "実務でどこから着手するか",
                    "どの前提を確認すべきか",
                    "次に何を決めるか",
                ]
                reader_question = reader_defaults[min(idx, len(reader_defaults) - 1)]
        section_plan = DiscourseSectionPlan(
            heading=heading,
            intent=intent,
            target_chars=int(section_length.get("target_chars", 520) or 520),
            topic_seed=topic_seed,
            fact_slot=_announcement_fact_slot_for_index(idx) if announcement_like else "",
            related_terms=related_terms,
            reader_question=reader_question,
            bridge_hint=bridge_hint,
            must_cover=must_cover_for_section,
            new_information=topic_seed,
        )
        for policy_key, policy_value in _build_reference_realization_policy(
            direction_family=direction_family,
            article_type=article_type,
            base_template=base_template,
            intent=intent,
            section_index=idx,
            section_count=len(heading_sequence),
        ).items():
            setattr(section_plan, policy_key, policy_value)
        discourse.append(section_plan)
        if article_type == "case_study" and intent == "change" and case_study_focus:
            case_change_focus = case_study_focus
        if article_type == "comparative_review" and intent == "criteria" and comparative_focus:
            comparative_criteria_focus = comparative_focus
        if article_type == "comparative_review" and intent == "comparison" and comparative_focus:
            comparative_comparison_focus = comparative_focus
        if article_type == "comparative_review" and intent == "fit" and comparative_focus:
            comparative_fit_focus = comparative_focus
        if article_type == "comparative_review" and intent == "caution" and comparative_focus:
            comparative_caution_focus = comparative_focus
    return discourse


def build_note4000_section_prompt(
    *,
    section: DiscourseSectionPlan,
    speaker_profile: str,
    audience_profile: str,
    relationship_mode: str,
    style_profile: NaturalStyleProfile,
    previous_summary: str,
    recent_summaries: Sequence[str],
    forbidden_topics: Sequence[str],
    allowed_pronouns: Sequence[str],
    user_instruction: str = "",
    instruction_anchor_terms: Sequence[str] | None = None,
    source_grounding_items: Sequence[Mapping[str, str]] | None = None,
) -> str:
    announcement_like = style_profile.profile_name == "note_4000_clear"
    related_terms = "、".join(_dedupe_keep_order(section.related_terms, limit=4)) or "本文の中心語をそのまま使う"
    must_cover = "、".join(_dedupe_keep_order((_normalize_focus_item(item) for item in section.must_cover), limit=3)) or "この節の中心論点を具体化する"
    summaries = " / ".join(_dedupe_keep_order(recent_summaries[-2:], limit=2)) or "まだ前段の要約はない"
    forbidden = "、".join(_dedupe_keep_order(forbidden_topics, limit=6)) or "なし"
    allowed_pronoun_text = "、".join(_dedupe_keep_order(allowed_pronouns, limit=4)) or "文脈上不要なら主語省略"
    anchor_term_items = _build_prompt_anchor_terms(
        must_cover=section.must_cover,
        topic_seed=section.topic_seed,
        related_terms=section.related_terms,
        reader_question=section.reader_question,
        article_profile=style_profile.profile_name,
        extra_terms=list(instruction_anchor_terms or []),
        limit=4,
    )
    anchor_terms = "、".join(anchor_term_items)
    source_grounding_lines: List[str] = []
    for item in list(source_grounding_items or [])[:2]:
        fact_text = str(item.get("fact_text") or "").strip()
        if not fact_text:
            continue
        source_title = str(item.get("source_title") or "").strip()
        locator = str(item.get("locator") or "").strip()
        label = source_title or locator or "source"
        source_grounding_lines.append(f"- {fact_text}（根拠: {label}）")
    fact_slot_line = ""
    if announcement_like and section.fact_slot:
        fact_slot_line = f" / この節の役割補足: {_FACT_SLOT_PROMPT_MAP.get(section.fact_slot, '案内文として事実を整理する')}"
    instruction_brief = _build_instruction_brief(
        user_instruction,
        topic_seed=section.topic_seed,
        must_cover=section.must_cover,
        article_profile=style_profile.profile_name,
    )
    style_rules = " / ".join(style_profile.prompt_rules[:3]) or "読者に語りかける一人の書き手として書く"
    banned_openings = "、".join(style_profile.banned_openings[:4]) or "定型導入句は避ける"
    banned_red_phrases = "、".join(_RED_BRIDGE_PHRASES)
    rhythm_line = {
        "short_medium": "短文と中文を中心に組み、必要な箇所だけ少し長くする",
        "medium_long_with_short_breaks": "中文と長文を軸にしつつ、要所で短文を差し込んでリズムを作る",
        "short_medium_long": "短文・中文・長文を混ぜ、同じテンポを続けない",
    }.get(style_profile.sentence_length_mix, "短文・中文・長文を混ぜる")
    density_line = {
        "fact_dense": "1文1情報を徹底し、事実・対象・影響・確認事項の順で密度高く書く",
        "scene_then_insight": "具体場面を先に置き、そのあとで気づきや判断軸につなげる",
        "market_structure": "市場の事象、構造要因、示唆を混ぜずに順番に置く",
        "criteria_then_fit": "この節に割り当てた比較論点を一つずつ具体化し、他の節の役割へ飛ばない",
        "process_result": "課題、進行、工夫、結果、再現条件を混ぜずに順番に置く",
        "value_evidence": "価値を述べた直後に背景、根拠、現場の具体を置く",
        "example_linked": "抽象語を置いたら次の文で必ず具体例や状況を置く",
        "balanced": "抽象と具体を交互に置き、説明だけで押し切らない",
    }.get(style_profile.information_density, "抽象と具体を交互に置く")
    punctuation_line = {
        "compact_japanese": "読点は必要最小限に抑え、1文を詰め込みすぎない",
        "expressive_japanese": "読点と句点で呼吸を作りつつ、感嘆符は使っても節内で1回までに抑える",
        "reflective_japanese": "読点と句点で間を作り、言い切りすぎずに余韻を残す",
        "balanced_japanese": "読点で情報を詰め込みすぎず、句点でこまめに意味を切り替える",
    }.get(style_profile.punctuation_profile, "句読点で自然な呼吸を作る")
    opening_line = {
        "very_high": "文頭表現は大きく変え、同じ接続詞や同じ主語で連続して始めない",
        "high": "文頭表現に変化をつけ、接続詞頼みの開始を続けない",
        "medium": "文頭表現を適度に変え、同じ開始語を3文以上続けない",
    }.get(style_profile.opening_variation_target, "文頭表現に変化をつける")
    subject_line = {
        "light_corporate_anchor": "企業の立場が切り替わる場面だけ主語を置き、それ以外は自然に省略する",
        "explicit_when_scope_changes": "対象者や比較対象が切り替わる場面だけ主語を明示し、同一話題では省略を許す",
        "explicit_when_comparing_entities": "比較対象を並べる文では主語や対象名を明示し、それ以外では省略を許す",
        "balanced_process_subjects": "工程や担当が切り替わる場面だけ主語を置き、同じ流れの中では省略してよい",
        "allow_implicit_first_person": "一人称は文脈が通る限り省略してよく、感覚が切り替わる場面だけ軽く置く",
        "balanced": "主語は必要なときだけ使い、文脈が続くなら省略してよい",
    }.get(style_profile.subject_omission_policy, "主語は必要なときだけ使う")
    paragraph_break_line = {
        "value_or_scene_shift": "価値説明、具体場面、判断軸のどれかが切り替わるところでだけ段落を変える",
        "structure_or_metric_shift": "市場構造、根拠、指標、示唆の役割が変わるところで段落を変える",
        "criteria_or_usecase_shift": "比較条件、評価軸、用途別結論の役割が変わるところで段落を変える",
        "phase_shift": "課題、進行、工夫、結果、再現条件の役割が変わるところで段落を変える",
        "scene_or_feeling_shift": "出来事、感覚、気づきのどれかが切り替わるところで段落を変える",
        "fact_or_action_shift": "変更点、影響、確認事項、行動のどれかが切り替わるところで段落を変える",
        "example_or_reason_shift": "理由、具体例、補足の役割が切り替わるところで段落を変える",
        "topic_or_role_shift": "話題か役割が切り替わるところで段落を変える",
    }.get(style_profile.paragraph_break_policy, "意味の切れ目で段落を変える")
    ending_line = _ENDING_LINES.get(style_profile.ending_distribution_hint, "文末の単調さを避ける")
    ending_guard_line = _ENDING_GUARD_LINES.get(style_profile.ending_distribution_hint, "主文の語尾を固定しない")
    reference_realization_hint = _reference_realization_prompt_hint(section)
    kotodesu_policy_line = _kotodesu_policy_line(style_profile, section.intent)
    intent_local_rule = _intent_local_rule(style_profile, section.intent, section.fact_slot)
    extra_heading_guard_line = "この節の中で新しい見出し（## / ###）や番号付き補足を追加しない"
    case_study_closure_guard_line = ""
    if style_profile.profile_name == "note_4000_case_study":
        if section.intent == "change":
            case_study_closure_guard_line = "1文目で何がどう変わったかを状態変化で明示し、『変わりました』だけで済ませない"
        elif section.intent == "condition":
            case_study_closure_guard_line = (
                "向く条件、前提、限界の少なくとも2つを本文に含め、"
                "『前段と重なる説明は省略』のようなメタ説明で締めない"
            )
    article_specific_line = _ARTICLE_SPECIFIC_LINES.get(style_profile.profile_name, "")
    example_grounding_line = _example_grounding_line(style_profile)
    legal_citation_guard_line = _legal_citation_guard_line() if _needs_legal_citation_guard(section, user_instruction) else ""
    goal_focus_terms = _extract_terms(_normalize_focus_item(str(section.reader_question or "")), limit=3)
    if not goal_focus_terms:
        goal_focus_terms = _extract_terms(
            _normalize_focus_item(
                "、".join(_dedupe_keep_order((_normalize_focus_item(item) for item in section.must_cover), limit=3))
                or str(section.topic_seed or "")
            ),
            limit=3,
        )
    section_goal_focus = "、".join(goal_focus_terms) or "この節の中心論点"
    role_line = (
        f"あなたは{speaker_profile}として、{audience_profile}向けのお知らせ本文を執筆します。"
        if announcement_like
        else f"あなたは{speaker_profile}として、{audience_profile}に向けて note の本文を執筆します。"
    )
    relation_line = (
        "会話調のエッセイではなく、案内文として簡潔かつ正確に書いてください。"
        if announcement_like
        else f"読者との関係は {relationship_mode} です。報告書ではなく、読者に語りかける一人の書き手として書いてください。"
    )
    section_goal_line = (
        f"この節で明示する焦点: {section_goal_focus}"
        if announcement_like
        else f"この節の焦点: {section_goal_focus}"
    )
    intro_line = f"{role_line} {relation_line}"
    announcement_rule_line = (
        "不安の代弁や励ましを入れず、確認できる変更点だけを書く。"
        "『ご確認ください』『お手続きください』などの依頼文は action 節に寄せる"
        if announcement_like
        else ""
    )
    source_grounding_rule_line = (
        "sourceブロックにない業種・部署・社内状況の例は作らない。会社説明の具体文は、sourceブロックの事実を優先して使う"
        if source_grounding_lines
        else ""
    )
    lines: List[str] = [
        intro_line,
        f"この節の見出しは「## {section.heading}」です。見出し記号は出力に含めないでください。",
        f"この節の役割: {section.intent} / この節の中心語: {section.topic_seed}",
        f"関連語: {related_terms} / 必ず触れる点: {must_cover}",
        section_goal_line,
        f"直前要約: {previous_summary or '導入の第一歩を作る'} / 直近の流れ: {summaries}",
        f"つなぎ方のヒント: {section.bridge_hint or 'この節で初めて必要になる判断材料を置く'}{fact_slot_line}",
        (
            f"想定文字数: {section.target_chars}字前後。"
            f"{style_profile.paragraph_min}〜{style_profile.paragraph_max}段落で書いてください。"
            f" / 主題の要約: {instruction_brief}（ユーザー指示を最優先）"
        ),
        f"アンカー語: {anchor_terms or section.topic_seed}",
    ]
    if source_grounding_lines:
        lines.append("sourceで確認できた事実:")
        lines.extend(source_grounding_lines)
    lines.extend(
        [
            "【不変ルール】",
            f"- 基本: {style_rules}",
            f"- 文のリズム: {rhythm_line} / 情報密度: {density_line}",
            f"- 句読点: {punctuation_line} / 文頭の変化: {opening_line}",
            "- 文の完結性: 各文は単独で意味が通る形で閉じ、助詞『が』『を』『の』『で』でぶら下げて終わらない",
        ]
    )
    if article_specific_line:
        lines.extend(line for line in article_specific_line.splitlines() if line.strip())
    if example_grounding_line:
        lines.append(f"- 事例の具体化: {example_grounding_line}")
    if legal_citation_guard_line:
        lines.append(f"- 法令引用: {legal_citation_guard_line}")
    subject_rule_line = f"- 主語省略: {subject_line}"
    if str(getattr(section, "speaker_reference_policy", "") or "").strip() == "no_first_person":
        subject_rule_line += "。一人称は出さず、必要なら対象や論点で主語を立てる"
    else:
        subject_rule_line += f"。使うなら {allowed_pronoun_text} の範囲に収める"
    if reference_realization_hint:
        subject_rule_line += f" / 参照表現: {reference_realization_hint}"
    lines.extend(
        [
            subject_rule_line,
            f"- 文末運用: {ending_line}。候補は {'、'.join(style_profile.preferred_endings[:4])} / 偏り回避: {ending_guard_line}",
        ]
    )
    if kotodesu_policy_line:
        lines.append(f"- ことです運用: {kotodesu_policy_line}")
    if intent_local_rule:
        lines.append(f"- 節の補足: {intent_local_rule}")
    if case_study_closure_guard_line:
        lines.append(f"- 事例節ルール: {case_study_closure_guard_line}")
    if announcement_rule_line:
        lines.append(f"- 案内文ルール: {announcement_rule_line}")
    lines.extend(
        [
            f"- 改行と構造: {paragraph_break_line}。毎文改行にはしない / {extra_heading_guard_line}",
            f"- 『{banned_red_phrases}』のような橋渡し句や読者感情の代弁は使わない",
            "- 『この記事で』『この記事として言えば』『この記事で伝えたいのは』のような自己言及は使わない",
            f"- {banned_openings} で始めない。見出しや主題文を言い換えただけの一文で始めない",
            f"- 無関係に以下の話題へ逸脱しない: {forbidden}",
        ]
    )
    if source_grounding_rule_line:
        lines.append(f"- sourceルール: {source_grounding_rule_line}")
    lines.append(
        "- 指示フレーズ禁止: この指示文で使われている制御フレーズ"
        "（「読者が知りたいこと」「必ず触れる点」「書き出す」「判断したいことは何か」「まとめと次の手」"
        "「三つ書き出す」などの指示動詞・節名）を本文に含めない"
    )
    lines.append("出力は本文のみ。見出し、注釈、メタ説明、自己評価、指示文の繰り返しは不要です。")
    return "\n".join(line for line in lines if str(line).strip())
