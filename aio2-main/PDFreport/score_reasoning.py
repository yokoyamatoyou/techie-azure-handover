import asyncio
import json
import re
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    BaseModel = None
    Field = None

try:
    from PDFreport.llm_client import get_llm_client
    from PDFreport.config.pdf_config import settings
except Exception:  # pragma: no cover
    get_llm_client = None
    settings = None


if BaseModel:
    class ScoreReason(BaseModel):
        summary: str = Field(default="", description="スコア理由の要約")
        bullets: List[str] = Field(default_factory=list, description="理由の要点（3-4件）")
else:
    ScoreReason = None


def _can_use_llm() -> bool:
    if get_llm_client is None or ScoreReason is None or settings is None:
        return False
    api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if not api_key or api_key.startswith("sk-test"):
        return False
    if getattr(settings, "OFFLINE_MODE", False):
        return False
    return True


def _run_llm(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return None
    return asyncio.run(coro)


def generate_score_reason(reason_type: str, payload: Dict[str, Any], max_tokens: int = 900) -> Optional[Dict[str, Any]]:
    if not _can_use_llm():
        return None
    try:
        llm_client = get_llm_client()
        system_prompt = (
            "あなたはSEO/AIO専門のコンサルタントです。"
            "与えられたサイトの分析結果から、このサイト固有の状況を踏まえた具体的なスコア理由を説明します。"
            "一般論ではなく、このサイトの実際のデータ（title、description、見出し、URL、業界）を引用して説明してください。"
            "出力はJSONで summary と bullets のみ。"
        )
        user_payload = json.dumps(payload, ensure_ascii=False)
        low_items = payload.get("low_items", [])
        mid_items = payload.get("mid_items", [])
        evidence = payload.get("evidence", {})
        context = payload.get("context", {})
        industry = context.get("industry") or "不明"
        platform = context.get("platform") or "不明"
        url = context.get("url") or ""
        max_chars = getattr(settings, "OPENAI_MAX_INPUT_CHARS", 2000)
        if len(user_payload) > max_chars:
            user_payload = user_payload[: max_chars - 3] + "..."
        evidence_details = _format_evidence_for_prompt(evidence)
        platform_business = context.get("platform_business_steps", [])
        platform_technical = context.get("platform_technical_steps", [])
        platform_steps_text = ""
        if platform_business or platform_technical:
            platform_steps_text = f"\n【{platform}での具体的な改善手順】\n"
            if platform_business:
                platform_steps_text += "管理画面から:\n" + "\n".join([f"  - {s}" for s in platform_business[:2]]) + "\n"
            if platform_technical:
                platform_steps_text += "技術的対応:\n" + "\n".join([f"  - {s}" for s in platform_technical[:2]]) + "\n"
        industry_advice = _get_industry_advice(industry)
        user_content = (
            f"【分析対象】{reason_type}\n"
            f"【URL】{url}\n"
            f"【業界】{industry}\n"
            f"【プラットフォーム】{platform}\n"
            f"{platform_steps_text}\n"
            f"【低評価項目(50点未満)】{', '.join(low_items) if low_items else 'なし'}\n"
            f"【改善余地あり(50-79点)】{', '.join(mid_items) if mid_items else 'なし'}\n\n"
            f"【サイトの実データ】\n{evidence_details}\n\n"
            f"【全スコア】{json.dumps(payload.get('scores', {}), ensure_ascii=False)}\n\n"
            f"【業界別の重要ポイント】\n{industry_advice}\n\n"
            "【出力要件】\n"
            "- summaryは400-550文字程度で具体的に記述\n"
            "- このサイトの実際のtitle/description/見出しなどを「」で引用して言及\n"
            f"- {industry}業界特有の課題（上記参照）を踏まえたアドバイスを含める\n"
            f"- {platform}での具体的な改善手順（上記参照）を参考にアドバイス\n"
            "- 50点未満の各項目について、なぜ低いのか具体的な理由を記述\n"
            "- 改善余地のある項目についても、何が足りないか簡潔に触れる\n"
            "- 改行を入れて読みやすく\n"
            "- bulletsは具体的な改善アクション2-3件（プラットフォーム固有の手順を含める）\n"
        )
        result = _run_llm(
            llm_client.generate_commentary(
                system_prompt,
                user_content,
                ScoreReason,
                max_tokens=max_tokens,
                temperature=0.2,
                model_name=getattr(settings, "PDF_LLM_MODEL", "gpt-4.1-mini"),
            )
        )
        if result is None:
            return None
        return {"summary": result.summary.strip(), "bullets": [b for b in result.bullets if b]}
    except Exception as exc:
        print(f"WARNING[LLM] Score reason generation failed ({reason_type}): {exc}", flush=True)
        return None


def _get_industry_advice(industry: str) -> str:
    """業界別の重要ポイントとAI検索での課題を返す（広告宣伝費比率が高い順）"""
    industry_map = {
        "化粧品・美容": (
            "- 成分・効果を正確に記載し、薬機法に準拠した表現を使用（「治る」「若返る」などNG）\n"
            "- ビフォーアフター写真は医薬品等適正広告基準に注意、体験談は個人差を明記\n"
            "- JSON-LD(Product)で商品情報を構造化、レビュー・評価をSchema.orgで実装"
        ),
        "健康食品・サプリメント": (
            "- 薬機法・景品表示法に準拠（「効く」「治る」「痩せる」などNG、機能性表示食品は届出番号必須）\n"
            "- 体験談には「個人の感想です」「効果を保証するものではありません」を明記\n"
            "- 成分・原材料・摂取目安量を明確にし、JSON-LD(Product)で構造化"
        ),
        "医療・クリニック": (
            "- 医療広告ガイドラインに準拠（「最高」「No.1」「絶対」などNG、ビフォーアフター写真は条件付き）\n"
            "- 医師の経歴・資格・専門分野を明示し、E-E-A-T（専門性・信頼性）を強化\n"
            "- 診療内容・料金・保険適用の有無を明確にし、JSON-LD(MedicalOrganization)を実装"
        ),
        "不動産・住宅": (
            "- 物件情報をJSON-LD(RealEstateListing)で構造化し、価格・間取り・立地を明確に\n"
            "- 周辺環境・交通アクセス・学区情報など、検討に必要な情報を網羅\n"
            "- 仲介手数料・契約条件を明示し、宅建業法に準拠した表記を徹底"
        ),
        "金融・保険": (
            "- 金融商品取引法に準拠（リスク説明・手数料・運用実績の明示必須）\n"
            "- 「元本保証」「必ず儲かる」などの断定的表現はNG、YMYL分野での正確性を確保\n"
            "- 会社の信頼性（金融庁登録・免許番号）を明示し、JSON-LD(FinancialProduct)を実装"
        ),
        "人材・求人": (
            "- 求人情報をJSON-LD(JobPosting)で構造化し、給与・勤務地・雇用形態を明確に\n"
            "- 職業安定法に準拠（虚偽の求人広告禁止、労働条件の明示義務）\n"
            "- 転職成功事例・年収アップ実績は具体的な数値とともに個人差を明記"
        ),
        "教育・スクール": (
            "- 講座内容・カリキュラム・対象者を明確に説明し、FAQ形式で疑問を解消\n"
            "- 講師の資格・経験・実績を明示し、合格率・就職率は根拠とともに提示\n"
            "- 受講料・教材費・追加費用を明確にし、JSON-LD(Course)で構造化"
        ),
        "法律・士業": (
            "- 弁護士法・税理士法等に準拠（誇大広告・比較広告の制限あり）\n"
            "- 専門分野・実績・料金体系を明確にし、E-E-A-T（専門性・信頼性）を強化\n"
            "- 初回相談の流れ・費用を明示し、JSON-LD(LegalService)を実装"
        ),
        "IT・SaaS": (
            "- 機能一覧・料金プラン・導入事例をFAQ形式で整理し、比較検討に役立つ情報を提供\n"
            "- ユースケース別の説明を充実させ、「どんな課題を解決するか」を明確に\n"
            "- 無料トライアル・デモ・API仕様をJSON-LD(SoftwareApplication)で構造化"
        ),
        "飲食・フード": (
            "- 営業時間・住所・電話番号をJSON-LD(Restaurant)で構造化し、予約導線を明確に\n"
            "- メニュー・価格帯・アレルギー情報を網羅し、来店判断に必要な情報を提供\n"
            "- 食品衛生法に準拠（アレルギー表示・原産地表示の義務確認）"
        ),
        "小売・EC": (
            "- 商品情報をJSON-LD(Product)で構造化し、価格・在庫・送料を明確に\n"
            "- 特定商取引法に準拠（返品・交換ポリシー・販売者情報の明示必須）\n"
            "- 比較表・FAQ・レビューを充実させ、購入判断をサポート"
        ),
        "製造業": (
            "- 製品スペック・品質基準をJSON-LD(Product)で構造化し、技術力をアピール\n"
            "- ISO認証・品質管理体制を明示し、B2B取引での信頼性を強化\n"
            "- 導入事例・取引実績を具体的な数値とともに提示"
        ),
        "建設・建築": (
            "- 施工事例・実績をJSON-LD(LocalBusiness)で構造化し、対応エリアを明確に\n"
            "- 建設業許可・資格保有者を明示し、E-E-A-T（専門性・信頼性）を強化\n"
            "- 見積もり・工期・保証内容を明確にし、建築基準法に準拠した説明を徹底"
        ),
    }
    if not industry or industry == "不明":
        return "- 結論を先頭に配置し、AIが引用しやすい構成にする\n- 専門性・信頼性を示す情報を充実させる\n- JSON-LDで情報を構造化する"
    for key, advice in industry_map.items():
        if key in industry or industry in key:
            return advice
    return "- 結論を先頭に配置し、AIが引用しやすい構成にする\n- 業界特有の専門用語・固有名詞を適切に使用\n- 信頼性を示す情報（実績・資格・認証）を明示"


def _format_evidence_for_prompt(evidence: Dict[str, Any]) -> str:
    """evidenceを読みやすいテキスト形式に変換"""
    if not evidence:
        return "（データなし）"
    lines = []
    for key, value in evidence.items():
        if value is None:
            continue
        if isinstance(value, dict):
            sub_items = [f"  - {k}: {v}" for k, v in value.items() if v is not None]
            if sub_items:
                lines.append(f"■ {key}:")
                lines.extend(sub_items)
        elif isinstance(value, list):
            if value:
                lines.append(f"■ {key}: {', '.join(str(v) for v in value[:5])}")
        else:
            lines.append(f"■ {key}: {value}")
    return "\n".join(lines) if lines else "（データなし）"


def format_reason_text(reason: Optional[Any]) -> str:
    def insert_reason_breaks(text: str) -> str:
        if not text:
            return ""
        # Normalize bullets and section markers into separate lines for PDF readability.
        normalized = re.sub(r'(?<!\n)■', '\n■', text)
        normalized = re.sub(r'(?<!\n)【', '\n【', normalized)
        normalized = re.sub(r'(?<!\n)[・･•]', lambda m: '\n' + m.group(0), normalized)
        return "\n".join(line.strip() for line in normalized.splitlines() if line.strip())

    if not reason:
        return ""
    # Ensure reason is a dictionary (it might be a string if LLM returns raw text
    # or if previous steps failed unexpectedly)
    if not isinstance(reason, dict):
        return insert_reason_breaks(str(reason).strip())
    
    summary = insert_reason_breaks(reason.get("summary", "").strip())
    bullets = [insert_reason_breaks(b.strip()) for b in (reason.get("bullets") or []) if b.strip()]
    lines = [summary] if summary else []
    if bullets:
        lines.append("")
        lines.append("【改善アクション】")
        lines.extend([f"・{b}" for b in bullets[:3]])
    return "\n".join(lines)


def build_seo_reason_payload(seo_scores: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    labels = {
        "title_score": "タイトル",
        "meta_description_score": "メタディスクリプション",
        "headings_score": "見出し構造",
        "content_score": "コンテンツ",
        "links_score": "リンク",
        "images_score": "画像",
        "technical_score": "技術要素",
    }
    normalized = {labels[k]: round((seo_scores.get(k, 0) or 0) * 10, 1) for k in labels}
    low_items = [label for label, score in normalized.items() if score < 50]
    mid_items = [label for label, score in normalized.items() if 50 <= score < 80]
    evidence = _build_seo_evidence(context or {}, low_items, mid_items)
    return {
        "low_items": low_items,
        "mid_items": mid_items,
        "scores": normalized,
        "evidence": evidence,
        "context": _build_reason_context(context),
    }


def build_aio_reason_payload(aio_breakdown: Dict[str, Any], penalties: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    core_metrics = aio_breakdown.get("core_metrics", {}) or {}
    enhanced_metrics = aio_breakdown.get("enhanced_metrics", {}) or {}
    labels = {
        "pid": "命題密度",
        "structure": "構造化",
        "entity": "エンティティ",
        "tech": "技術適合",
        "citation": "引用準備度",
        "freshness": "情報鮮度",
        "aeo": "AEOパターン",
        "entity_linking": "知識グラフ連携",
    }
    scores = {}
    for key, label in labels.items():
        value = core_metrics.get(key, enhanced_metrics.get(key, 0))
        try:
            value = float(value)
        except Exception:
            value = 0.0
        if value <= 1:
            value *= 100
        scores[label] = round(value, 1)
    low_items = [label for label, score in scores.items() if score < 50]
    mid_items = [label for label, score in scores.items() if 50 <= score < 80]
    evidence = _build_aio_evidence(context or {}, low_items, mid_items)
    return {
        "low_items": low_items,
        "mid_items": mid_items,
        "scores": scores,
        "penalties": penalties or [],
        "evidence": evidence,
        "context": _build_reason_context(context),
    }


def _build_reason_context(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "industry": context.get("industry"),
        "platform": context.get("platform"),
        "platform_business_steps": context.get("platform_business_steps", []),
        "platform_technical_steps": context.get("platform_technical_steps", []),
        "url": context.get("url"),
    }


def _build_seo_evidence(context: Dict[str, Any], low_items: List[str], mid_items: List[str]) -> Dict[str, Any]:
    seo = context.get("seo", {}) or {}
    headings = seo.get("headings") or {}
    heading_samples = seo.get("heading_samples") or {}
    evidence = {}

    title = seo.get("title") or ""
    title_len = seo.get("title_length") or len(title)
    evidence["タイトル"] = {
        "実際のtitle": f"「{title[:60]}」" if title else "（未設定）",
        "文字数": f"{title_len}文字",
        "推奨": "28-36文字が推奨（20-40文字は許容）",
        "問題": _diagnose_title(title, title_len),
    }

    desc = seo.get("meta_description") or ""
    desc_len = seo.get("meta_description_length") or len(desc)
    evidence["メタディスクリプション"] = {
        "実際のdescription": f"「{desc[:100]}」" if desc else "（未設定）",
        "文字数": f"{desc_len}文字",
        "推奨": "80-120文字が推奨（121-160文字は許容）",
        "問題": _diagnose_description(desc, desc_len),
    }

    h1_list = heading_samples.get("h1", []) or []
    h2_list = heading_samples.get("h2", []) or []
    evidence["見出し構造"] = {
        "H1": h1_list[:2] if h1_list else "（なし）",
        "H2サンプル": h2_list[:3] if h2_list else "（なし）",
        "H1数": headings.get("h1", 0),
        "H2数": headings.get("h2", 0),
        "問題": _diagnose_headings(headings, h1_list),
    }

    word_count = seo.get("word_count") or 0
    text_ratio = seo.get("text_html_ratio") or 0
    evidence["コンテンツ"] = {
        "文字数": f"{word_count}文字",
        "テキスト比率": f"{text_ratio:.1%}" if isinstance(text_ratio, float) else str(text_ratio),
        "問題": _diagnose_content(word_count, text_ratio),
    }

    internal = seo.get("internal_links") or 0
    external = seo.get("external_links") or 0
    evidence["リンク"] = {
        "内部リンク数": internal,
        "外部リンク数": external,
        "問題": _diagnose_links(internal, external),
    }

    images = seo.get("images") or 0
    no_alt = seo.get("images_without_alt") or 0
    evidence["画像"] = {
        "画像数": images,
        "alt未設定数": no_alt,
        "問題": f"{no_alt}枚のalt属性が未設定" if no_alt > 0 else "問題なし",
    }

    evidence["技術要素"] = {
        "構造化データ": seo.get("structured_data_types") or "（なし）",
        "viewport": "あり" if seo.get("has_viewport") else "なし",
        "canonical": seo.get("canonical_url") or "（未設定）",
    }
    return evidence


def _diagnose_title(title: str, length: int) -> str:
    if not title:
        return "titleタグが未設定です"
    if length < 20:
        return f"短すぎます（{length}文字）。20-40文字を推奨"
    if length > 40:
        return f"長すぎます（{length}文字）。検索結果で切れる可能性"
    return "適切な長さです"


def _diagnose_description(desc: str, length: int) -> str:
    if not desc:
        return "meta descriptionが未設定です"
    if length < 80:
        return f"短すぎます（{length}文字）。80-120文字を推奨"
    if length > 160:
        return f"長すぎます（{length}文字）。検索結果で切れる可能性"
    return "適切な長さです"


def _diagnose_headings(headings: Dict, h1_list: List) -> str:
    h1_count = headings.get("h1", 0)
    h2_count = headings.get("h2", 0)
    issues = []
    if h1_count == 0:
        issues.append("H1タグがありません")
    elif h1_count > 1:
        issues.append(f"H1が{h1_count}個（1個推奨）")
    if h2_count == 0:
        issues.append("H2タグがありません")
    return "、".join(issues) if issues else "問題なし"


def _diagnose_content(word_count: int, text_ratio: float) -> str:
    issues = []
    if word_count < 300:
        issues.append(f"文字数が少なすぎます（{word_count}文字）")
    elif word_count < 800:
        issues.append(f"コンテンツ量が少なめ（{word_count}文字）")
    if isinstance(text_ratio, float) and text_ratio < 0.1:
        issues.append("テキスト比率が低い（HTML過多）")
    return "、".join(issues) if issues else "問題なし"


def _diagnose_links(internal: int, external: int) -> str:
    issues = []
    if internal == 0:
        issues.append("内部リンクがありません")
    elif internal < 3:
        issues.append("内部リンクが少なめ")
    if external == 0:
        issues.append("外部リンクがありません（権威性低下の可能性）")
    return "、".join(issues) if issues else "問題なし"


def _build_aio_evidence(context: Dict[str, Any], low_items: List[str], mid_items: List[str]) -> Dict[str, Any]:
    aio = context.get("aio", {}) or {}
    evidence = {}

    citation = aio.get("citation_readiness") or {}
    if isinstance(citation, dict):
        evidence["引用準備度"] = {
            "スコア": citation.get("score"),
            "結論優先度": citation.get("conclusion_first"),
            "データ密度": citation.get("data_density"),
            "問題": "結論が先頭にない、または数値/事実が少ない" if (citation.get("score") or 0) < 0.5 else "良好",
        }
    else:
        evidence["引用準備度"] = {"スコア": citation, "問題": "詳細データなし"}

    freshness = aio.get("contextual_freshness") or {}
    if isinstance(freshness, dict):
        last_modified = freshness.get("last_modified") or freshness.get("date")
        evidence["情報鮮度"] = {
            "最終更新": last_modified or "（検出できず）",
            "スコア": freshness.get("score"),
            "問題": _diagnose_freshness(freshness),
        }
    else:
        evidence["情報鮮度"] = {"スコア": freshness, "問題": "更新日が検出できません"}

    aeo = aio.get("aeo_patterns") or {}
    if isinstance(aeo, dict):
        patterns = aeo.get("patterns", []) or []
        is_body_only = any((p or {}).get("location") == "body" for p in patterns if isinstance(p, dict))
        evidence["AEOパターン"] = {
            "検出パターン数": len(patterns),
            "サンプル": patterns[:2] if patterns else "（なし）",
            "問題": "定義文（〜とは、〜である）がH2/H3直下にない" if len(patterns) == 0 else ("定義文が本文内のみで検出（見出し直下に配置推奨）" if is_body_only else "良好"),
        }
    else:
        evidence["AEOパターン"] = {"スコア": aeo, "問題": "定義パターンが少ない可能性"}

    entity = aio.get("entity_linking") or {}
    if isinstance(entity, dict):
        linked = entity.get("linked_entities", []) or []
        evidence["知識グラフ連携"] = {
            "認識エンティティ": linked[:5] if linked else "（なし）",
            "スコア": entity.get("score"),
            "問題": "AIが認識しやすい固有名詞・専門用語が少ない" if len(linked) < 3 else "良好",
        }
    else:
        evidence["知識グラフ連携"] = {"スコア": entity, "問題": "エンティティ検出データなし"}

    structure = aio.get("structure") or {}
    if isinstance(structure, dict):
        evidence["構造化"] = {
            "JSON-LD": "あり" if structure.get("has_jsonld") else "なし",
            "FAQ構造化": "あり" if structure.get("has_faq") else "なし",
            "問題": "JSON-LDやFAQ構造化データがない" if not structure.get("has_jsonld") else "良好",
        }
    else:
        evidence["構造化"] = {"スコア": structure}

    tech = aio.get("tech") or {}
    if isinstance(tech, dict):
        evidence["技術適合"] = {
            "SSR/静的HTML": "対応" if tech.get("is_ssr") else "未対応（JSレンダリング）",
            "robots.txt": "AIクローラー許可" if tech.get("allows_ai") else "AIクローラーブロック",
            "llms.txt": "あり" if tech.get("has_llms_txt") else "なし",
            "問題": _diagnose_tech(tech),
        }
    else:
        evidence["技術適合"] = {"スコア": tech}

    return evidence


def _diagnose_freshness(freshness: Dict) -> str:
    score = freshness.get("score") or 0
    source = str(freshness.get("source") or "")
    if "Text" in source:
        return "本文の日付のみ（機械判読が弱い）。JSON-LD/metaで更新日を明示推奨"
    if score >= 0.8:
        return "良好（6ヶ月以内の更新）"
    if score >= 0.5:
        return "やや古い（6ヶ月-1年）"
    return "古い情報（1年以上前、または日付なし）"


def _diagnose_tech(tech: Dict) -> str:
    issues = []
    if not tech.get("is_ssr"):
        issues.append("JavaScriptレンダリング依存（AIクローラーが読めない可能性）")
    if not tech.get("allows_ai"):
        issues.append("robots.txtでAIクローラーをブロック")
    if not tech.get("has_llms_txt"):
        issues.append("llms.txtがない（AI向けコンテンツガイドなし）")
    return "、".join(issues) if issues else "良好"


def fallback_reason(payload: Dict[str, Any], label: str) -> Dict[str, Any]:
    scores = payload.get("scores", {}) or {}
    items = sorted(scores.items(), key=lambda x: x[1])
    lows = [(name, val) for name, val in items if val < 50]
    mids = [(name, val) for name, val in items if 50 <= val < 80]
    highs = [(name, val) for name, val in items if val >= 80]
    penalties = payload.get("penalties", [])
    evidence = payload.get("evidence", {}) or {}
    context = payload.get("context", {}) or {}
    industry = context.get("industry") or ""
    platform = context.get("platform") or ""
    platform_business = context.get("platform_business_steps", [])
    platform_technical = context.get("platform_technical_steps", [])

    summary_lines = [f"【{label}の評価理由】"]

    if lows:
        summary_lines.append("")
        summary_lines.append("■ 低評価項目（50点未満）:")
        for name, val in lows[:3]:
            detail = _get_evidence_detail(evidence, name)
            summary_lines.append(f"  ・{name}: {val:.0f}点 {detail}")

    if mids:
        summary_lines.append("")
        summary_lines.append("■ 改善余地あり（50-79点）:")
        for name, val in mids[:2]:
            summary_lines.append(f"  ・{name}: {val:.0f}点")

    if highs:
        summary_lines.append("")
        high_names = [f"{n}({v:.0f}点)" for n, v in highs[:2]]
        summary_lines.append(f"■ 強み: {', '.join(high_names)}")

    if penalties:
        summary_lines.append("")
        summary_lines.append(f"■ ペナルティ: {penalties[0]}")

    if industry:
        summary_lines.append("")
        summary_lines.append(f"■ {industry}業界での重要ポイント:")
        industry_tips = _get_industry_advice(industry).split("\n")[:2]
        for tip in industry_tips:
            if tip.strip():
                summary_lines.append(f"  {tip.strip()}")

    if platform and (platform_business or platform_technical):
        summary_lines.append("")
        summary_lines.append(f"■ {platform}での改善手順:")
        if platform_business:
            summary_lines.append(f"  ・{platform_business[0][:60]}...")
        if platform_technical:
            summary_lines.append(f"  ・{platform_technical[0][:60]}...")

    summary = "\n".join(summary_lines)

    bullets = []
    if platform_business:
        bullets.append(f"【{platform}】{platform_business[0][:80]}")
    for name, val in lows[:2]:
        action = _suggest_action(name, evidence)
        if action and len(bullets) < 3:
            bullets.append(action)
    if mids and len(bullets) < 3:
        bullets.append(f"{mids[0][0]}を改善すると総合スコアが向上します")

    return {"summary": summary, "bullets": bullets[:3]}


def _get_evidence_detail(evidence: Dict[str, Any], item_name: str) -> str:
    item_evidence = evidence.get(item_name, {})
    if not item_evidence or not isinstance(item_evidence, dict):
        return ""
    problem = item_evidence.get("問題", "")
    if problem and problem != "問題なし" and problem != "良好":
        return f"- {problem}"
    return ""


def _suggest_action(item_name: str, evidence: Dict[str, Any]) -> str:
    actions = {
        "タイトル": "titleタグを28-36文字で、キーワードを含めて最適化",
        "メタディスクリプション": "meta descriptionを80-120文字で魅力的に記述",
        "見出し構造": "H1を1つ設定し、H2で論理的にセクション分け",
        "コンテンツ": "本文を800文字以上に拡充し、価値ある情報を追加",
        "リンク": "関連ページへの内部リンクと権威あるサイトへの外部リンクを追加",
        "画像": "すべての画像にalt属性を設定",
        "技術要素": "JSON-LD構造化データを追加（JSON-LDはAI/検索向けの説明書）",
        "引用準備度": "結論を先頭に配置し、数値や事実を明記",
        "情報鮮度": "コンテンツを更新し、更新日をJSON-LDまたはmetaタグで明示（本文表示だけでは伝わりにくい）",
        "AEOパターン": "H2直下に「〜とは、〜である」形式の定義文を追加",
        "知識グラフ連携": "業界で認知された固有名詞や専門用語を適切に使用してください",
        "構造化": "FAQ、HowTo、ArticleなどのJSON-LDを追加（AIが内容を誤読しにくくなる）",
        "技術適合": "SSR対応とrobots.txtでAIクローラーを許可（llms.txtはルート配下 /llms.txt に配置）",
        "命題密度": "簡潔で情報密度の高い文章に書き換え",
        "エンティティ": "重要な固有名詞を明確に記述",
    }
    return actions.get(item_name, "")
