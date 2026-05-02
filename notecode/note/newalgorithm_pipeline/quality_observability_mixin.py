"""Observability helpers for MinimalPipeline quality metrics and evaluations."""
from __future__ import annotations

from dataclasses import replace
import re
from typing import Any, Dict

from core.app_config import get_quality_pipeline_config
from human_resonance2.quality_pipeline import QualityPipelineRunner, format_monitoring_report
from .output_formatter import normalize_output_body
from .strict_saas import allows_quality_fail_open


class QualityObservabilityMixin:
    CASE_STUDY_RESULT_PROXY_PRIMARY_INTENTS = ("change", "condition")
    CASE_STUDY_RESULT_PROXY_FALLBACK_INTENTS = ("reflection", "closing")
    CASE_STUDY_CONDITION_SENTENCE_RE = re.compile(
        r"(再現条件|条件なら|条件として|条件は|前提として|前提を|前提が|ただし|限界|例外|場合|分岐|退避|必要があります|必要です)"
    )
    BRIDGE_PHRASE_PATTERNS = (
        re.compile(r"前の(?:段落|節)で触れたように"),
        re.compile(r"前述(?:のとおり|したように)"),
    )
    READER_EMOTION_PROXY_PATTERNS = (
        re.compile(r"ここまで(?:読んで|お読みいただいて)"),
        re.compile(r"その感覚は(?:とても)?自然です"),
    )
    COMPARATIVE_AXIS_SECTION_PATTERNS = {
        "comparison": re.compile(r"(強み|弱み|差分|違い)"),
        "fit": re.compile(r"(用途|向いて|向か|合いやす|合います|ケース|選び方)"),
        "closing": re.compile(r"(結論|おすすめの分け方|用途別|分け方)"),
    }
    MUST_COVER_PROXY_PATTERNS = {
        "事業内容": (re.compile(r"(事業|提供|支援|サービス|業務SaaS)"),),
        "具体例": (re.compile(r"(具体的には|たとえば|例えば)"),),
        "変更点": (re.compile(r"(変更点|変更内容|更新します|更新されます|変更されます|必須項目が変更)"),),
        "対象と時期": (
            re.compile(r"(対象は|対象者|対象となる|既存利用者|既存顧客)"),
            re.compile(r"(\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}時(?:\d{2}分)?|開始時期|停止時間)"),
        ),
        "必要な行動": (re.compile(r"(確認してください|行ってください|対応してください|事前準備|確認事項|ログインテスト)"),),
        "価格": (re.compile(r"(価格|月額|費用|コスト|料金)"),),
        "用途": (re.compile(r"(用途|用途別|向きやす|向いて|向かない|選び方|ケース)"),),
        "ガバナンス": (re.compile(r"(ガバナンス|承認|権限|監査|統制|責任)"),),
        "差分": (re.compile(r"(差分|違い|強み|弱み|比較)"),),
        "改善前の状態": (re.compile(r"(改善前|見直し前|離脱が多く|迷っていた|判断しにくかった)"),),
        "見直した点": (re.compile(r"(改善後|見直した|見直し|整理した|組み替えた|分岐し)"),),
        "改善後の変化": (
            re.compile(r"(改善後|見直し後|結果として|変化が出)"),
            re.compile(r"(減っ|増え|短くな|早くな|止まりにく|判断しやす|負担が減|変わ)"),
        ),
        "再現条件": (
            re.compile(r"(再現条件|条件なら再現|条件)"),
            re.compile(r"(必要|前提|ただし|場合|例外|分岐|退避)"),
        ),
        "成功談に寄せず再現条件まで含めて共有する": (
            re.compile(r"(再現条件|条件なら再現できるか)"),
            re.compile(r"(ただし|必要があります|変わった|変化|改善後)"),
        ),
    }
    COMPANY_INTRO_SOURCE_SLOT_KEYS = (
        "current_business",
        "customer_situation_or_entry_point",
        "support_scope_boundary",
        "operating_process_steps",
        "pre_contact_decision",
    )
    COMPANY_INTRO_BUCKET_SLOT_MAP = {
        "現在事業": "current_business",
        "顧客接点": "customer_situation_or_entry_point",
        "支援範囲": "support_scope_boundary",
        "進め方": "operating_process_steps",
        "相談前判断": "pre_contact_decision",
    }
    COMPANY_INTRO_SOURCE_SLOT_PROXY_PATTERNS = {
        "current_business": (
            ("business", (re.compile(r"(データ入力|エントリ|入力作業|データ化|情報整理)"),)),
            ("scope", (re.compile(r"(分析|RPA|スキャニング|市場調査|Webリサーチ|運用サポート|アンケート入力)"),)),
        ),
        "customer_situation_or_entry_point": (
            ("entry", (re.compile(r"(相談|悩み|入口|止まって|やり方|任せたい|出発点)"),)),
            ("situation", (re.compile(r"(目的|集計|収集|分析|入力|スキャニング|活用)"),)),
        ),
        "support_scope_boundary": (
            ("boundary", (re.compile(r"(どこまで|頼める範囲|範囲|前処理|後処理|一貫|工程|切り出|全国対応|セキュリティ|体制)"),)),
            ("service", (re.compile(r"(データ入力|アンケート入力|市場調査|Webリサーチ|分析|RPA|スキャニング|運用サポート)"),)),
        ),
        "operating_process_steps": (
            ("contact", (re.compile(r"(問い合わせ|電話|メールフォーム|連絡)"),)),
            ("meeting", (re.compile(r"(ヒアリング|打ち合わせ|対面|Zoom)"),)),
            ("estimate", (re.compile(r"(NDA|見積)"),)),
        ),
        "pre_contact_decision": (
            ("decision", (re.compile(r"(相談前|先に|まず|確認|用意|見ておき|決め|整理)"),)),
            ("scope", (re.compile(r"(目的|データ|入力|収集|分析|紙資料|どこまで|範囲|任せる|NDA|対面|Zoom)"),)),
        ),
    }

    @staticmethod
    def _coefficient_of_variation(values: list[int]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        if mean <= 0:
            return 0.0
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return round((variance ** 0.5) / mean, 4)

    @staticmethod
    def _content_terms(text: str, limit: int = 24) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,24}", str(text or ""))
        stop_terms = {
            "こと", "もの", "ため", "これ", "それ", "ここ", "そこ", "今回", "記事", "読者",
            "判断", "整理", "具体", "内容", "情報", "説明", "確認", "可能", "必要",
        }
        unique: list[str] = []
        for token in tokens:
            if token in stop_terms or token.isdigit() or token in unique:
                continue
            unique.append(token)
            if len(unique) >= limit:
                break
        return unique

    @staticmethod
    def _strip_heading_text(text: str) -> str:
        value = str(text or "")
        return re.sub(r"(?m)^##\s+.*$", "", value).strip()

    @staticmethod
    def _median(values: list[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0

    @staticmethod
    def _normalize_for_echo(text: str) -> str:
        return re.sub(r"[\s、。！？「」『』（）()\[\]・,./]+", "", str(text or ""))

    @staticmethod
    def _source_grounding_anchor_terms(text: str, limit: int = 8) -> list[str]:
        clauses = [
            str(item or "").strip()
            for item in re.split(r"[。！？\n、,]+", str(text or ""))
            if str(item or "").strip()
        ]
        anchors: list[str] = []
        date_literals = re.findall(r"\d{4}年(?:\d{1,2}月\d{1,2}日)?", str(text or ""))
        for literal in date_literals:
            if literal and literal not in anchors:
                anchors.append(literal)
                if len(anchors) >= limit:
                    return anchors[:limit]
        split_pattern = re.compile(
            r"(?:を通じて|に合わせて|を強みとしています|を整えています|を築いてきました|"
            r"を積み重ね(?:て)?|を重ねてきました|として|によって|により|について|"
            r"に対して|ながら|や|と|の|は|が|を|に)"
        )
        trim_prefix_pattern = re.compile(r"^[のはがをにでもとや]+")
        trim_suffix_pattern = re.compile(
            r"(?:しています|しました|してきました|している|してきた|していた|"
            r"できています|できました|できる|です|ます|でした|ました|する|した)$"
        )
        for clause in clauses:
            for fragment in split_pattern.split(clause):
                normalized = str(fragment or "").strip()
                if not normalized:
                    continue
                normalized = trim_prefix_pattern.sub("", normalized)
                normalized = trim_suffix_pattern.sub("", normalized).strip(" 　")
                compact = QualityObservabilityMixin._normalize_for_echo(normalized)
                if len(compact) < 4 or normalized in anchors:
                    continue
                anchors.append(normalized)
                if len(anchors) >= limit:
                    return anchors[:limit]
        if anchors:
            return anchors[:limit]
        return (QualityObservabilityMixin._content_terms(text, limit=5) or [str(text or "")[:12]])[:limit]

    @staticmethod
    def _matched_normalized_terms(text: str, terms: list[str]) -> list[str]:
        normalized_text = QualityObservabilityMixin._normalize_for_echo(text)
        matched: list[str] = []
        seen_compacts: set[str] = set()
        for term in terms:
            compact = QualityObservabilityMixin._normalize_for_echo(term)
            if not compact or compact in seen_compacts:
                continue
            if compact in normalized_text:
                seen_compacts.add(compact)
                matched.append(str(term))
        return matched

    @staticmethod
    def _source_grounding_anchor_signature(terms: list[str]) -> str:
        normalized_terms = [
            QualityObservabilityMixin._normalize_for_echo(term)
            for term in terms
            if QualityObservabilityMixin._normalize_for_echo(term)
        ]
        return "|".join(normalized_terms)

    @staticmethod
    def _source_grounding_title_like_fact(fact_text: str, fact_terms: list[str]) -> bool:
        compact = str(fact_text or "").strip()
        if not compact:
            return False
        if re.search(r"[。！？\n]", compact):
            return False
        return len(QualityObservabilityMixin._normalize_for_echo(compact)) <= 48 and len(fact_terms) <= 2

    @staticmethod
    def _source_grounding_metadata_like_fact(fact_text: str) -> bool:
        compact = str(fact_text or "").strip().strip("\"'")
        if not compact:
            return False
        if re.match(r"^[A-Za-z]:[\\/]", compact):
            return True
        if re.match(r"^(?:~|/)[^\s]+/[^\s]+$", compact):
            return True
        if re.fullmatch(r"https?://\S+", compact, flags=re.IGNORECASE):
            return True

        basename = re.split(r"[\\/]+", compact)[-1]
        filename_extensions = (
            "txt",
            "md",
            "pdf",
            "doc",
            "docx",
            "rtf",
            "csv",
            "tsv",
            "json",
            "html",
            "htm",
            "png",
            "jpg",
            "jpeg",
            "webp",
        )
        if (
            basename == compact
            and re.fullmatch(r"[^。！？\n\r]+\.(?:" + "|".join(filename_extensions) + r")", compact, re.IGNORECASE)
        ):
            return True

        has_japanese = bool(re.search(r"[ぁ-んァ-ン一-龯]", compact))
        if has_japanese:
            return False
        if re.search(r"(?i)[a-f0-9]{16,}", compact):
            return True
        if (
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{5,}", compact)
            and bool(re.search(r"[_\-.]", compact))
            and bool(re.search(r"\d", compact))
        ):
            return True
        return False

    @classmethod
    def _company_intro_source_contract(cls, contract: Dict[str, Any]) -> Dict[str, Any]:
        source_contract = contract.get("_company_introduction_source_contract")
        if not isinstance(source_contract, dict):
            source_contract = contract.get("company_introduction_source_contract")
        if not isinstance(source_contract, dict):
            return {}
        required_slots = [
            str(slot or "").strip()
            for slot in list(source_contract.get("required_slots") or [])
            if str(slot or "").strip()
        ]
        if not required_slots:
            required_slots = list(cls.COMPANY_INTRO_SOURCE_SLOT_KEYS)
        if not any(slot in cls.COMPANY_INTRO_SOURCE_SLOT_KEYS for slot in required_slots):
            return {}
        semantic_key = str(contract.get("semantic_article_key") or "").strip()
        pattern = str(source_contract.get("pattern") or "").strip()
        if semantic_key != "company_introduction" and "company_introduction" not in pattern:
            return {}
        return dict(source_contract)

    @classmethod
    def _company_intro_source_slot_key(
        cls,
        item: Dict[str, Any],
        fact_text: str,
        contract: Dict[str, Any],
    ) -> str:
        source_contract = cls._company_intro_source_contract(contract)
        if not source_contract:
            return ""
        required_slots = {
            str(slot or "").strip()
            for slot in list(source_contract.get("required_slots") or cls.COMPANY_INTRO_SOURCE_SLOT_KEYS)
            if str(slot or "").strip()
        }
        required_slots &= set(cls.COMPANY_INTRO_SOURCE_SLOT_KEYS)
        if not required_slots:
            return ""

        explicit_slot = str(item.get("slot_key") or item.get("slot") or "").strip()
        if explicit_slot in required_slots:
            return explicit_slot

        bucket_slot = cls.COMPANY_INTRO_BUCKET_SLOT_MAP.get(str(item.get("bucket") or "").strip(), "")
        if bucket_slot in required_slots:
            return bucket_slot

        normalized_fact = cls._normalize_for_echo(fact_text)
        if not normalized_fact:
            return ""
        slots = dict(source_contract.get("slots") or {})
        for slot_key in cls.COMPANY_INTRO_SOURCE_SLOT_KEYS:
            if slot_key not in required_slots:
                continue
            normalized_slot = cls._normalize_for_echo(str(slots.get(slot_key) or ""))
            if len(normalized_slot) < 8:
                continue
            if normalized_slot in normalized_fact or normalized_fact in normalized_slot:
                return slot_key
        return ""

    @classmethod
    def _company_intro_slot_proxy_evidence(cls, body: str, slot_key: str) -> list[str]:
        if slot_key not in cls.COMPANY_INTRO_SOURCE_SLOT_KEYS:
            return []
        evidence: list[str] = []
        for label, patterns in cls.COMPANY_INTRO_SOURCE_SLOT_PROXY_PATTERNS.get(slot_key, ()):
            matched = ""
            for pattern in patterns:
                found = pattern.search(str(body or ""))
                if found:
                    matched = found.group(0)
                    break
            if not matched:
                return []
            evidence.append(f"company_intro:{slot_key}:{label}:{matched[:24]}")
        return evidence

    @staticmethod
    def _topic_phrase_candidates(terms: list[str]) -> list[tuple[str, ...]]:
        phrases: list[tuple[str, ...]] = []
        for size in (3, 2):
            if len(terms) < size:
                continue
            for idx in range(len(terms) - size + 1):
                phrase_terms = tuple(terms[idx: idx + size])
                if len("".join(phrase_terms)) < 8 or phrase_terms in phrases:
                    continue
                phrases.append(phrase_terms)
        return phrases[:8]

    @staticmethod
    def _contains_terms(text: str, terms: list[str], *, threshold: int = 1) -> bool:
        hits = 0
        haystack = str(text or "")
        for term in terms:
            compact = str(term or "").strip()
            if not compact:
                continue
            if compact in haystack:
                hits += 1
            if hits >= threshold:
                return True
        return False

    @staticmethod
    def _must_cover_candidate_terms(text: str, limit: int = 8) -> list[str]:
        value = str(text or "").strip()
        if not value:
            return []
        candidates: list[str] = []
        for term in QualityObservabilityMixin._content_terms(value, limit=limit):
            if term not in candidates:
                candidates.append(term)
        for fragment in re.split(r"(?:と|や|および|及び|、|,|/|・)", value):
            normalized = str(fragment or "").strip()
            if len(normalized) < 2:
                continue
            if normalized not in candidates:
                candidates.append(normalized)
            for suffix in ("内容", "事項", "例"):
                if normalized.endswith(suffix) and len(normalized) > len(suffix):
                    trimmed = normalized[: -len(suffix)].strip()
                    if len(trimmed) >= 2 and trimmed not in candidates:
                        candidates.append(trimmed)
            if len(candidates) >= limit:
                return candidates[:limit]
        return candidates[:limit]

    @classmethod
    def _must_cover_reflected(cls, body: str, item: str) -> bool:
        candidate_terms = cls._must_cover_candidate_terms(item) or [str(item or "")[:12]]
        if cls._contains_terms(body, candidate_terms):
            return True
        patterns = cls.MUST_COVER_PROXY_PATTERNS.get(str(item or "").strip())
        if patterns and all(pattern.search(str(body or "")) for pattern in patterns):
            return True
        return False

    @classmethod
    def _collect_anchor_terms(
        cls,
        topic_statement: str,
        topic: str,
        must_cover_items: list[str],
        *,
        limit: int = 12,
    ) -> list[str]:
        anchors = cls._content_terms(" ".join([topic_statement, topic, *must_cover_items]), limit=limit)
        for item in must_cover_items:
            for candidate in cls._must_cover_candidate_terms(item, limit=4):
                if candidate not in anchors:
                    anchors.append(candidate)
                if len(anchors) >= limit:
                    return anchors[:limit]
        return anchors[:limit]

    @staticmethod
    def _comparative_axis_anchor_terms(section: Any, limit: int = 10) -> list[str]:
        raw_items = [
            str(getattr(section, "heading", "") or "").strip(),
            str(getattr(section, "topic_seed", "") or "").strip(),
            *[
                str(item or "").strip()
                for item in list(getattr(section, "must_cover", []) or [])
                if str(item or "").strip()
            ],
        ]
        anchors: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            compact = QualityObservabilityMixin._normalize_for_echo(item)
            if compact and compact not in seen:
                seen.add(compact)
                anchors.append(item)
            for term in QualityObservabilityMixin._content_terms(item, limit=4):
                compact_term = QualityObservabilityMixin._normalize_for_echo(term)
                if not compact_term or compact_term in seen:
                    continue
                seen.add(compact_term)
                anchors.append(term)
                if len(anchors) >= limit:
                    return anchors[:limit]
        return anchors[:limit]

    @classmethod
    def _comparative_contract_axis_terms(cls, contract: Dict[str, Any] | None, *, limit: int = 10) -> list[str]:
        normalized_contract = dict(contract or {})
        raw_items = [
            *[
                str(item or "").strip()
                for item in list(normalized_contract.get("comparison_axes") or [])
                if str(item or "").strip()
            ],
            *[
                str(item or "").strip()
                for item in list(normalized_contract.get("must_cover") or [])
                if str(item or "").strip()
            ],
        ]
        anchors: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            compact = cls._normalize_for_echo(item)
            if compact and compact not in seen:
                seen.add(compact)
                anchors.append(item)
            for term in cls._must_cover_candidate_terms(item, limit=4):
                compact_term = cls._normalize_for_echo(term)
                if not compact_term or compact_term in seen:
                    continue
                seen.add(compact_term)
                anchors.append(term)
                if len(anchors) >= limit:
                    return anchors[:limit]
        return anchors[:limit]

    @classmethod
    def _comparative_contract_axis_reflected(cls, text: str, contract: Dict[str, Any] | None) -> bool:
        normalized_contract = dict(contract or {})
        for item in [
            *list(normalized_contract.get("comparison_axes") or []),
            *list(normalized_contract.get("must_cover") or []),
        ]:
            label = str(item or "").strip()
            if not label:
                continue
            if cls._must_cover_reflected(text, label):
                return True
        return False

    def _topic_echo_metrics(self, body: str, topic: str, sections: list | None = None) -> Dict[str, Any]:
        normalized_body = self._normalize_for_echo(body)
        body_only = self._strip_heading_text(body)
        normalized_body_only = self._normalize_for_echo(body_only)
        topic_terms = self._content_terms(topic, limit=8)
        topic_phrases = self._topic_phrase_candidates(topic_terms)
        heading_terms = []
        for section in sections or []:
            heading_terms.extend(self._content_terms(str(getattr(section, "heading", "") or ""), limit=4))
        heading_term_set = set(heading_terms)
        normalized_headings = "".join(
            self._normalize_for_echo(str(getattr(section, "heading", "") or ""))
            for section in sections or []
        )
        if not normalized_body or not topic_terms:
            return {
                "topic_echo_ratio": 0.0,
                "topic_echo_body_only_ratio": 0.0,
                "topic_echo_heading_adjusted_ratio": 0.0,
                "topic_echo_long_span_count": 0,
                "topic_echo_anchor_terms": [],
            }
        matched_terms = [term for term in topic_terms if term in normalized_body]
        matched_body_terms = [term for term in topic_terms if term in normalized_body_only]
        adjusted_terms = [term for term in matched_body_terms if term not in heading_term_set]
        matched_phrases = []
        adjusted_phrases = []
        for phrase_terms in topic_phrases:
            pattern = re.compile(".*?".join(re.escape(term) for term in phrase_terms))
            if pattern.search(normalized_body_only):
                matched_phrases.append(phrase_terms)
                if not pattern.search(normalized_headings):
                    adjusted_phrases.append(phrase_terms)
        long_spans = []
        for fragment in re.split(r"[、。！？\s]+", str(topic or "")):
            compact = fragment.strip()
            if len(compact) < 12:
                continue
            normalized_fragment = self._normalize_for_echo(compact)
            if normalized_fragment and normalized_fragment in normalized_body_only:
                long_spans.append(compact)
        phrase_ratio = len(matched_phrases) / max(1, len(topic_phrases))
        adjusted_phrase_ratio = len(adjusted_phrases) / max(1, len(topic_phrases))
        if not matched_phrases:
            phrase_ratio = (len(matched_body_terms) / max(1, len(topic_terms))) * 0.5
            adjusted_phrase_ratio = (len(adjusted_terms) / max(1, len(topic_terms))) * 0.5
        return {
            "topic_echo_ratio": round(len(matched_terms) / max(1, len(topic_terms)), 4),
            "topic_echo_body_only_ratio": round(phrase_ratio, 4),
            "topic_echo_heading_adjusted_ratio": round(adjusted_phrase_ratio, 4),
            "topic_echo_long_span_count": len(list(dict.fromkeys(long_spans))),
            "topic_echo_anchor_terms": matched_terms[:5],
        }

    def _prompt_follow_metrics(self, body: str, contract: Dict[str, Any], sections: list) -> Dict[str, Any]:
        topic = str(contract.get("topic") or "")
        topic_statement = str(contract.get("topic_statement") or "")
        must_cover_items = [
            str(item or "").strip()
            for item in (contract.get("must_cover", []) or [])
            if str(item or "").strip()
        ]
        anchor_terms = self._collect_anchor_terms(topic_statement, topic, must_cover_items, limit=12)
        matched_anchor_terms = []
        for term in anchor_terms:
            if self._must_cover_reflected(body, term):
                matched_anchor_terms.append(term)
        must_cover_hits = 0
        for item in must_cover_items:
            if self._must_cover_reflected(body, item):
                must_cover_hits += 1
        forbidden_topics = [
            str(item or "").strip()
            for item in (contract.get("forbidden_topics", []) or [])
            if str(item or "").strip()
        ]
        forbidden_hits = sum(1 for item in forbidden_topics if item in str(body or ""))
        if "[BLOCKED]" in str(body or "") or "[REMOVED]" in str(body or ""):
            forbidden_hits += 1
        discourse_hits = 0
        for section in sections:
            section_terms = self._content_terms(str(getattr(section, "topic_seed", "") or ""), limit=4)
            for item in list(getattr(section, "must_cover", []) or []):
                section_terms.extend(self._content_terms(str(item or ""), limit=4))
            section_terms = list(dict.fromkeys(section_terms))
            if section_terms and self._contains_terms(body, section_terms):
                discourse_hits += 1
        return {
            "prompt_follow_anchor_coverage": round(len(matched_anchor_terms) / max(1, len(anchor_terms)), 4),
            "prompt_follow_must_cover_hits": must_cover_hits,
            "must_cover_reflection_ratio": round(must_cover_hits / max(1, len(must_cover_items)), 4),
            "prompt_follow_forbidden_drift_count": forbidden_hits,
            "prompt_follow_discourse_hits": discourse_hits,
        }

    def _source_grounding_metrics(self, body: str, contract: Dict[str, Any]) -> Dict[str, Any]:
        items = contract.get("source_grounding_items", []) or []
        if not isinstance(items, list):
            items = []
        reflected_count = 0
        matched_anchor_terms: list[str] = []
        diagnostic_groups: dict[str, Dict[str, Any]] = {}
        group_order: list[str] = []
        raw_item_count = 0
        metadata_excluded_count = 0
        metadata_excluded_examples: list[str] = []
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            fact_text = str(item.get("fact_text") or "").strip()
            if not fact_text:
                continue
            raw_item_count += 1
            if self._source_grounding_metadata_like_fact(fact_text):
                metadata_excluded_count += 1
                if len(metadata_excluded_examples) < 6:
                    metadata_excluded_examples.append(fact_text[:120])
                continue
            fact_terms = self._source_grounding_anchor_terms(fact_text)
            threshold = 2 if len(fact_terms) >= 3 else 1
            matched_terms = self._matched_normalized_terms(body, fact_terms)
            slot_key = self._company_intro_source_slot_key(item, fact_text, contract)
            slot_proxy_evidence: list[str] = []
            if len(matched_terms) < threshold and slot_key:
                slot_proxy_evidence = self._company_intro_slot_proxy_evidence(body, slot_key)
                for term in slot_proxy_evidence:
                    if term not in matched_terms:
                        matched_terms.append(term)
            missing_terms = [term for term in fact_terms if term not in matched_terms]
            match_status = "missing"
            if len(matched_terms) >= threshold:
                match_status = "matched"
            elif matched_terms:
                match_status = "partial"
            if len(matched_terms) >= threshold:
                reflected_count += 1
                for term in matched_terms[:3]:
                    if term not in matched_anchor_terms:
                        matched_anchor_terms.append(term)
            signature = self._source_grounding_anchor_signature(fact_terms) or self._normalize_for_echo(fact_text)
            if signature not in diagnostic_groups:
                diagnostic_groups[signature] = {
                    "item_indices": [],
                    "duplicate_count": 0,
                    "title_like": self._source_grounding_title_like_fact(fact_text, fact_terms),
                    "anchor_terms": fact_terms[:8],
                    "matched_terms": [],
                    "missing_terms": [],
                    "match_status": match_status,
                    "source_excerpt": fact_text[:120],
                    "slot_key": slot_key,
                    "slot_proxy_evidence": [],
                }
                group_order.append(signature)
            group = diagnostic_groups[signature]
            group["item_indices"].append(index)
            group["duplicate_count"] = len(group["item_indices"])
            if slot_key and not group.get("slot_key"):
                group["slot_key"] = slot_key
            if match_status == "matched" or (match_status == "partial" and group.get("match_status") == "missing"):
                group["match_status"] = match_status
            for term in matched_terms[:8]:
                if term not in group["matched_terms"]:
                    group["matched_terms"].append(term)
            for term in missing_terms[:8]:
                if term not in group["missing_terms"]:
                    group["missing_terms"].append(term)
            for term in slot_proxy_evidence[:5]:
                if term not in group["slot_proxy_evidence"]:
                    group["slot_proxy_evidence"].append(term)
        item_count = raw_item_count - metadata_excluded_count
        diagnostics = []
        for group_index, signature in enumerate(group_order[:12], start=1):
            group = diagnostic_groups[signature]
            diagnostics.append(
                {
                    "group_index": group_index,
                    "item_indices": list(group.get("item_indices", []))[:12],
                    "duplicate_count": int(group.get("duplicate_count", 0) or 0),
                    "title_like": bool(group.get("title_like", False)),
                    "anchor_terms": list(group.get("anchor_terms", []))[:8],
                    "matched_terms": list(group.get("matched_terms", []))[:8],
                    "missing_terms": list(group.get("missing_terms", []))[:8],
                    "match_status": str(group.get("match_status") or "missing"),
                    "source_excerpt": str(group.get("source_excerpt") or "")[:120],
                    "slot_key": str(group.get("slot_key") or ""),
                    "slot_proxy_evidence": list(group.get("slot_proxy_evidence", []))[:5],
                }
            )
        matched_group_count = sum(1 for group in diagnostic_groups.values() if group.get("match_status") == "matched")
        partial_group_count = sum(1 for group in diagnostic_groups.values() if group.get("match_status") == "partial")
        missing_group_count = sum(1 for group in diagnostic_groups.values() if group.get("match_status") == "missing")
        duplicate_group_count = sum(1 for group in diagnostic_groups.values() if int(group.get("duplicate_count", 0) or 0) > 1)
        title_like_group_count = sum(1 for group in diagnostic_groups.values() if bool(group.get("title_like", False)))
        source_grounding_reflection_ratio = round(reflected_count / max(1, item_count), 4) if item_count else 0.0
        group_reflection_ratio = round(matched_group_count / max(1, len(diagnostic_groups)), 4) if diagnostic_groups else 0.0
        missing_groups = [
            group
            for group in diagnostic_groups.values()
            if group.get("match_status") == "missing"
        ]
        missing_groups_are_duplicate_title_like = bool(missing_groups) and all(
            bool(group.get("title_like", False))
            and int(group.get("duplicate_count", 0) or 0) > 1
            for group in missing_groups
        )
        group_auxiliary_pass = (
            source_grounding_reflection_ratio < 0.5
            and group_reflection_ratio >= 0.5
            and duplicate_group_count > 0
            and missing_groups_are_duplicate_title_like
        )
        return {
            "source_grounding_item_count": item_count,
            "source_grounding_raw_item_count": raw_item_count,
            "source_grounding_metadata_excluded_count": metadata_excluded_count,
            "source_grounding_metadata_excluded_examples": metadata_excluded_examples,
            "source_grounding_reflected_count": reflected_count,
            "source_grounding_reflection_ratio": source_grounding_reflection_ratio,
            "source_grounding_anchor_terms": matched_anchor_terms[:12],
            "source_grounding_deduped_anchor_group_count": len(diagnostic_groups),
            "source_grounding_matched_anchor_group_count": matched_group_count,
            "source_grounding_partial_anchor_group_count": partial_group_count,
            "source_grounding_missing_anchor_group_count": missing_group_count,
            "source_grounding_duplicate_anchor_group_count": duplicate_group_count,
            "source_grounding_title_like_anchor_group_count": title_like_group_count,
            "source_grounding_anchor_group_diagnostics": diagnostics,
            "source_grounding_group_reflection_ratio": group_reflection_ratio,
            "source_grounding_group_auxiliary_pass": group_auxiliary_pass,
            "source_grounding_group_auxiliary_pass_reason": (
                "duplicate_title_like_denominator_inflation" if group_auxiliary_pass else ""
            ),
        }

    def _prompt_context_metrics(self, body: str, contract: Dict[str, Any]) -> Dict[str, Any]:
        items = contract.get("prompt_context_items", []) or []
        if not isinstance(items, list):
            items = []
        normalized_items = [
            str(item or "").strip()
            for item in items
            if str(item or "").strip()
        ]
        reflected_count = 0
        dx_item_count = 0
        dx_reflected_count = 0
        for item in normalized_items:
            item_terms = self._content_terms(item, limit=6) or [item[:12]]
            threshold = 2 if len(item_terms) >= 3 else 1
            reflected = self._contains_terms(body, item_terms, threshold=threshold)
            if reflected:
                reflected_count += 1
            if any(keyword in item for keyword in ("DX", "デジタル化", "電子化", "アナログ", "紙", "帳票")):
                dx_item_count += 1
                dx_keywords = ("DX", "デジタル化", "電子化", "アナログ", "紙", "帳票")
                dx_keyword_hits = sum(1 for keyword in dx_keywords if keyword in str(body or ""))
                if reflected or dx_keyword_hits >= 2:
                    dx_reflected_count += 1
        return {
            "prompt_context_item_count": len(normalized_items),
            "prompt_context_reflected_count": reflected_count,
            "prompt_context_reflection_ratio": round(reflected_count / max(1, len(normalized_items)), 4)
            if normalized_items
            else 0.0,
            "dx_context_item_count": dx_item_count,
            "dx_context_reflection_ratio": round(dx_reflected_count / max(1, dx_item_count), 4)
            if dx_item_count
            else 0.0,
        }

    def _announcement_fact_metrics(self, body: str, sections: list) -> Dict[str, Any]:
        slot_patterns = {
            "change": re.compile(r"(変更|開始|提供開始|新サービス)"),
            "who_when": re.compile(r"(\d{4}年\d{1,2}月\d{1,2}日|対象|既存顧客|開始時期)"),
            "impact": re.compile(r"(影響|変更される|利用環境|契約条件|画面仕様|停止|継続|アクセスできない)"),
            "check": re.compile(r"(確認|手続き|申込|フォーム|入力内容)"),
            "caution": re.compile(r"(注意|遅延|未申込|誤り|支障|参照専用|編集できません|保持|控え)"),
            "action": re.compile(r"(公式|案内|お問い合わせ|確認してください|お手続き|申し込み)"),
        }
        chunks = [chunk.strip() for chunk in re.split(r"(?=^##\s+)", str(body or ""), flags=re.MULTILINE) if chunk.strip()]
        slot_hits = 0
        assigned_slots = 0
        evidence_terms_by_section: list[list[str]] = []
        for idx, section in enumerate(sections):
            slot = str(getattr(section, "fact_slot", "") or "")
            if not slot:
                continue
            assigned_slots += 1
            pattern = slot_patterns.get(slot)
            candidate_chunks: list[str] = []
            if idx < len(chunks):
                candidate_chunks.append(chunks[idx])
            for chunk in chunks:
                if chunk not in candidate_chunks:
                    candidate_chunks.append(chunk)
            if pattern and any(pattern.search(chunk) for chunk in candidate_chunks):
                slot_hits += 1
            evidence_terms = []
            for item in list(getattr(section, "must_cover", []) or []):
                evidence_terms.extend(self._content_terms(str(item or ""), limit=4))
            if not evidence_terms:
                evidence_terms = self._content_terms(str(getattr(section, "topic_seed", "") or ""), limit=4)
            evidence_terms_by_section.append(list(dict.fromkeys(evidence_terms)))
        reuse_count = 0
        for evidence_terms in evidence_terms_by_section:
            if not evidence_terms:
                continue
            seen_in_chunks = sum(1 for chunk in chunks if self._contains_terms(chunk, evidence_terms))
            if seen_in_chunks > 1:
                reuse_count += 1
        action_sentence_count = 0
        invalid_modal_pattern_count = 0
        sentences = [item.strip() for item in re.split(r"(?<=[。！？])", str(body or "")) if item.strip()]
        for sentence in sentences:
            if re.search(r"(ご確認|お申し込み|お手続き|お問い合わせ|確認してください|お願いいたします)", sentence):
                action_sentence_count += 1
            if re.search(r"可能性が高く[^。]{0,24}(進め|確認|対応|ご利用|お手続き)", sentence):
                invalid_modal_pattern_count += 1
            if re.search(r"多くの場合[^。]{0,32}(専用ページ|公式|お手続き|お申し込み|ご確認)", sentence):
                invalid_modal_pattern_count += 1
        return {
            "fact_slot_coverage": round(slot_hits / max(1, assigned_slots), 4),
            "fact_slot_reuse_count": reuse_count,
            "announcement_action_sentence_count": action_sentence_count,
            "announcement_invalid_modal_pattern_count": invalid_modal_pattern_count,
        }

    def _apply_quality_pass(
        self,
        text: str,
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        quality_config = get_quality_pipeline_config()
        article_type = str(contract.get("article_type") or "").strip().lower()
        runner_config = quality_config
        observe_only_requested = bool(contract.get("quality_observe_only"))
        if observe_only_requested and quality_config.enabled and quality_config.mode not in {"off", "shadow"}:
            runner_config = replace(quality_config, mode="shadow")
        effective_fail_open = allows_quality_fail_open(
            contract.get("strict_saas_mode"),
            config_fail_open=runner_config.fail_open,
        )
        check: Dict[str, Any] = {
            "enabled": bool(runner_config.enabled),
            "mode": str(runner_config.mode),
            "fail_open": bool(effective_fail_open),
            "reports": [],
            "mode_resolution": {},
            "errors": [],
            "applied": [],
            "monitoring_report": {},
        }
        if quality_config.mode != runner_config.mode:
            check["mode_override"] = {
                "requested_mode": str(quality_config.mode),
                "effective_mode": str(runner_config.mode),
                "reason": "contract_observe_only",
            }
        if not text or not runner_config.enabled or runner_config.mode == "off":
            return text, check
        try:
            runner = QualityPipelineRunner(config=runner_config)
            quality_result = runner.process(text, context=self._build_quality_context(contract, style_profile))
            phase_bundle = {
                "platform": "note",
                "mode": runner_config.mode,
                "errors": list(quality_result.errors),
                "phase_reports": list(quality_result.phase_reports),
                "applied": list(quality_result.applied),
                "mode_resolution": dict(getattr(quality_result, "mode_resolution", {}) or {}),
            }
            check.update(
                {
                    "reports": [phase_bundle],
                    "mode_resolution": phase_bundle["mode_resolution"],
                    "errors": phase_bundle["errors"],
                    "applied": phase_bundle["applied"],
                    "monitoring_report": format_monitoring_report(quality_result.phase_reports),
                }
            )
            return quality_result.text, check
        except Exception as exc:
            if effective_fail_open:
                error_text = str(exc)
                check.update(
                    {
                        "reports": [
                            {
                                "platform": "note",
                                "mode": runner_config.mode,
                                "errors": [error_text],
                                "phase_reports": [],
                                "applied": [],
                                "mode_resolution": {},
                            }
                        ],
                        "errors": [error_text],
                    }
                )
                return text, check
            raise

    @staticmethod
    def _flatten_quality_phase_reports(quality_check: Dict[str, Any]) -> list[Dict[str, Any]]:
        phase_reports: list[Dict[str, Any]] = []
        for report in quality_check.get("reports", []) or []:
            if not isinstance(report, dict):
                continue
            for phase_report in report.get("phase_reports", []) or []:
                if isinstance(phase_report, dict):
                    phase_reports.append(phase_report)
        return phase_reports

    @staticmethod
    def _phase_report_by_name(phase_reports: list[Dict[str, Any]], phase_name: str) -> Dict[str, Any]:
        for report in phase_reports:
            if str(report.get("phase") or "") == phase_name:
                return dict(report)
        return {}

    def _build_quality_evaluations(
        self,
        quality_check: Dict[str, Any],
        quality_metrics: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        phase_reports = self._flatten_quality_phase_reports(quality_check)
        fingerprint = self._phase_report_by_name(phase_reports, "fingerprint")
        layout_guard = self._phase_report_by_name(phase_reports, "phase05_layout_guard")
        orchestrator = self._phase_report_by_name(phase_reports, "phase06_orchestrator")
        mode_resolution = dict(quality_check.get("mode_resolution", {}) or {})
        effective_mode = str(
            mode_resolution.get("downstream_mode")
            or mode_resolution.get("effective_mode")
            or quality_check.get("mode")
            or "off"
        )
        flat_zone_flags = list(fingerprint.get("flat_zone_flags", []) or [])
        soft_warnings = [f"fingerprint:{flag}" for flag in flat_zone_flags]
        layout_validation = dict(layout_guard.get("layout_validation_report", {}) or {})
        semantic_issue_count = int(
            layout_validation.get("semantic_issue_count", 0)
            or layout_validation.get("issue_count", 0)
            or 0
        )
        bridge_phrase_count = int(quality_metrics.get("bridge_phrase_count", 0) or 0)
        reader_emotion_proxy_count = int(quality_metrics.get("reader_emotion_proxy_count", 0) or 0)
        source_grounding_item_count = int(quality_metrics.get("source_grounding_item_count", 0) or 0)
        source_grounding_metadata_excluded_count = int(
            quality_metrics.get("source_grounding_metadata_excluded_count", 0) or 0
        )
        source_grounding_reflection_ratio = round(
            float(quality_metrics.get("source_grounding_reflection_ratio", 0.0) or 0.0),
            4,
        )
        source_grounding_group_auxiliary_pass = bool(
            quality_metrics.get("source_grounding_group_auxiliary_pass", False)
        )
        prompt_context_item_count = int(quality_metrics.get("prompt_context_item_count", 0) or 0)
        prompt_context_reflection_ratio = round(
            float(quality_metrics.get("prompt_context_reflection_ratio", 0.0) or 0.0),
            4,
        )
        dx_context_item_count = int(quality_metrics.get("dx_context_item_count", 0) or 0)
        dx_context_reflection_ratio = round(
            float(quality_metrics.get("dx_context_reflection_ratio", 0.0) or 0.0),
            4,
        )
        sentence_integrity_warning_count = int(quality_metrics.get("sentence_integrity_warning_count", 0) or 0)
        hard_fail_reasons: list[str] = []
        if str(orchestrator.get("gate_decision") or "") == "fallback":
            hard_fail_reasons.append("phase06_orchestrator_fallback")
        hard_failed = bool(hard_fail_reasons)
        instructional_fragment_count = 0
        unpredictability = round(float(fingerprint.get("overall_unpredictability", 0.0) or 0.0), 4)
        hard_soft_eval = {
            "mode": effective_mode,
            "hard_failed": hard_failed,
            "hard_fail_reasons": hard_fail_reasons,
            "soft_warnings": soft_warnings,
            "metrics": {
                "unpredictability": unpredictability,
                "flat_zone_count": len(flat_zone_flags),
                "semantic_issue_count": semantic_issue_count,
                "instructional_fragment_count": instructional_fragment_count,
                "paragraph_break_semantic_score": round(
                    float(quality_metrics.get("paragraph_break_semantic_score", 0.0) or 0.0),
                    4,
                ),
            },
        }
        if bridge_phrase_count > 0:
            soft_warnings.append("phrase:bridge_scaffold")
        if reader_emotion_proxy_count > 0:
            soft_warnings.append("phrase:reader_emotion_proxy")
        if (
            source_grounding_item_count >= 2
            and source_grounding_reflection_ratio < 0.5
            and not source_grounding_group_auxiliary_pass
        ) or (
            source_grounding_item_count == 0
            and source_grounding_metadata_excluded_count >= 2
        ):
            soft_warnings.append("source_grounding:weak_reflection")
        if prompt_context_item_count >= 1 and prompt_context_reflection_ratio < 0.5:
            soft_warnings.append("contract:prompt_context_weak_reflection")
        if dx_context_item_count >= 1 and dx_context_reflection_ratio < 0.5:
            soft_warnings.append("contract:dx_context_weak_reflection")
        phrase_issue_count = int(bridge_phrase_count > 0) + int(reader_emotion_proxy_count > 0)
        contextual_naturalness_report = {
            "passed": not hard_failed,
            "issue_count": semantic_issue_count + phrase_issue_count + (1 if hard_failed else 0),
            "soft_issue_count": len(soft_warnings),
            "semantic_issue_count": semantic_issue_count,
            "instructional_fragment_count": instructional_fragment_count,
            "connective_opening_ratio": round(
                float(quality_metrics.get("connective_opening_rate", 0.0) or 0.0),
                4,
            ),
            "bridge_phrase_count": bridge_phrase_count,
            "reader_emotion_proxy_count": reader_emotion_proxy_count,
            "source_grounding_reflection_ratio": source_grounding_reflection_ratio,
            "prompt_context_reflection_ratio": prompt_context_reflection_ratio,
            "dx_context_reflection_ratio": dx_context_reflection_ratio,
            "sentence_integrity_warning_count": sentence_integrity_warning_count,
            "semantic_layout": {
                "semantic_issue_count": semantic_issue_count,
                "paragraph_break_semantic_score": round(
                    float(quality_metrics.get("paragraph_break_semantic_score", 0.0) or 0.0),
                    4,
                ),
            },
        }
        final_quality_eval = {
            "evaluated": bool(quality_check.get("enabled")) and effective_mode != "off",
            "mode": effective_mode,
            "hard_failed": hard_failed,
            "hard_fail_reasons": hard_fail_reasons,
            "soft_warning_count": len(soft_warnings),
            "semantic_issue_count": semantic_issue_count,
            "instructional_fragment_count": instructional_fragment_count,
            "soft_warnings": soft_warnings,
            "metrics": dict(hard_soft_eval["metrics"]),
        }
        final_quality_eval["metrics"].update(
            {
                "bridge_phrase_count": bridge_phrase_count,
                "reader_emotion_proxy_count": reader_emotion_proxy_count,
                "source_grounding_reflection_ratio": source_grounding_reflection_ratio,
                "prompt_context_reflection_ratio": prompt_context_reflection_ratio,
                "dx_context_reflection_ratio": dx_context_reflection_ratio,
                "sentence_integrity_warning_count": sentence_integrity_warning_count,
            }
        )
        return hard_soft_eval, contextual_naturalness_report, final_quality_eval

    def _example_specificity_metrics(self, body: str) -> Dict[str, Any]:
        sentences = [item.strip() for item in re.split(r"(?<=[。！？])", self._strip_heading_text(body)) if item.strip()]
        example_specificity_count = 0
        abstract_example_fallback_count = 0
        category_patterns = [
            re.compile(r"(SaaS|製造|物流|小売|医療|介護|建設|不動産|BtoB|EC|情シス|情報システム)"),
            re.compile(r"(\d{2,4}名規模|小規模|中堅|大手|複数拠点|首都圏|地方拠点|月初|月末)"),
            re.compile(r"(人事|総務|営業|経理|法務|CS|カスタマーサポート|導入担当|店舗運営|管理部)"),
            re.compile(r"(導入前|変更前|切り替え前|二重入力|差し戻し|迷い|手戻り|問い合わせ|承認フロー|初回設定)"),
        ]
        abstract_pattern = re.compile(r"(効率化|最適化|価値|課題|改善|強化|高度化|連携)")
        example_cue_pattern = re.compile(r"(たとえば|例えば|具体例|事例|ケース)")
        for sentence in sentences:
            specificity_hits = sum(1 for pattern in category_patterns if pattern.search(sentence))
            if specificity_hits >= 2:
                example_specificity_count += 1
            if example_cue_pattern.search(sentence) and abstract_pattern.search(sentence) and specificity_hits < 2:
                abstract_example_fallback_count += 1
        return {
            "example_specificity_count": example_specificity_count,
            "abstract_example_fallback_count": abstract_example_fallback_count,
        }

    @staticmethod
    def _split_section_chunks(body: str) -> list[str]:
        return [chunk.strip() for chunk in re.split(r"(?=^##\s+)", str(body or ""), flags=re.MULTILINE) if chunk.strip()]

    def _case_result_proxy_chunks(self, body: str, sections: list) -> list[str]:
        """Collect observe-only result-proxy chunks for case_study."""
        chunks = self._split_section_chunks(body)
        explicit_headings = ("結果として何が変わったか", "どの条件なら再現できるか")
        explicit_chunks = [
            chunk
            for chunk in chunks
            if any(chunk.startswith(f"## {heading}") for heading in explicit_headings)
        ]
        if len(explicit_chunks) >= 2:
            return explicit_chunks

        def _collect(target_intents: tuple[str, ...]) -> list[str]:
            selected: list[str] = []
            for idx, section in enumerate(sections):
                intent = str(getattr(section, "intent", "") or "").strip().lower()
                if intent not in target_intents:
                    continue
                if idx < len(chunks):
                    selected.append(chunks[idx])
            return selected

        result_proxy_chunks = _collect(self.CASE_STUDY_RESULT_PROXY_PRIMARY_INTENTS)
        if result_proxy_chunks:
            return result_proxy_chunks
        if explicit_chunks:
            return explicit_chunks
        return _collect(self.CASE_STUDY_RESULT_PROXY_FALLBACK_INTENTS)

    def _case_result_metrics(self, body: str, sections: list, article_type: str) -> Dict[str, Any]:
        if article_type != "case_study":
            return {
                "case_result_abstract_summary_count": 0,
                "case_result_change_sentence_count": 0,
                "case_result_condition_sentence_count": 0,
            }
        target_chunks = self._case_result_proxy_chunks(body, sections)
        if not target_chunks:
            return {
                "case_result_abstract_summary_count": 0,
                "case_result_change_sentence_count": 0,
                "case_result_condition_sentence_count": 0,
            }
        abstract_summary_count = 0
        change_sentence_count = 0
        condition_sentence_count = 0
        change_pattern = re.compile(
            r"(減っ|増え|短くな|早くな|小さくな|そろっ|改善し|改善につなが|分かっ|でき|見え|安定し|止まりにく|迷いにく|判断しやす|負担が減)"
        )
        condition_pattern = self.CASE_STUDY_CONDITION_SENTENCE_RE
        abstract_summary_pattern = re.compile(r"(結果|変化|改善|効果|学び|ポイント|重要)")
        for chunk in target_chunks:
            sentences = [item.strip() for item in re.split(r"(?<=[。！？])", self._strip_heading_text(chunk)) if item.strip()]
            for sentence in sentences:
                if "ことです" in sentence and abstract_summary_pattern.search(sentence):
                    abstract_summary_count += 1
                if change_pattern.search(sentence):
                    change_sentence_count += 1
                if condition_pattern.search(sentence):
                    condition_sentence_count += 1
        return {
            "case_result_abstract_summary_count": abstract_summary_count,
            "case_result_change_sentence_count": change_sentence_count,
            "case_result_condition_sentence_count": condition_sentence_count,
        }

    def _comparative_review_metrics(
        self,
        body: str,
        sections: list,
        article_type: str,
        contract: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if article_type != "comparative_review":
            return {
                "comparative_fit_sentence_count": 0,
                "comparative_absolute_winner_claim_count": 0,
                "comparative_axis_shift_count": 0,
            }
        chunks = self._split_section_chunks(body)
        criteria_terms: list[str] = []
        fit_sentence_count = 0
        absolute_winner_claim_count = 0
        axis_shift_count = 0
        fit_pattern = re.compile(r"(用途|向いて|向きます|向か|合う|適して|おすすめ|選びやす|ケース)")
        absolute_pattern = re.compile(r"(絶対|必ず|一択|間違いなく|圧倒的(?:に)?|万人に|誰にでも)")
        absolute_recommendation_pattern = re.compile(
            r"(?:(?:最も|一番|完全に)(?:[^\n。]{0,12}))"
            r"(?:向いて|向きやす|おすすめ|適して|選びやす|合う|優位|本命)"
        )
        comparison_sentence_pattern = re.compile(r"(比較|差分|向いて|向か|おすすめ|選ぶ|適して)")
        contract_axis_terms = self._comparative_contract_axis_terms(contract, limit=10)
        for idx, section in enumerate(sections):
            intent = str(getattr(section, "intent", "") or "").strip().lower()
            if idx >= len(chunks):
                continue
            chunk = chunks[idx]
            body_text = self._strip_heading_text(chunk)
            if intent == "criteria":
                criteria_terms = self._comparative_axis_anchor_terms(section, limit=8)
                for term in contract_axis_terms:
                    if term not in criteria_terms:
                        criteria_terms.append(term)
                    if len(criteria_terms) >= 10:
                        break
                continue
            section_terms = self._comparative_axis_anchor_terms(section, limit=8)
            section_pattern = self.COMPARATIVE_AXIS_SECTION_PATTERNS.get(intent)
            sentences = [item.strip() for item in re.split(r"(?<=[。！？])", body_text) if item.strip()]
            for sentence in sentences:
                if fit_pattern.search(sentence):
                    fit_sentence_count += 1
                if absolute_pattern.search(sentence) or absolute_recommendation_pattern.search(sentence):
                    absolute_winner_claim_count += 1
                if intent not in {"comparison", "fit", "closing"}:
                    continue
                if not criteria_terms:
                    criteria_terms = list(contract_axis_terms)
                if not criteria_terms:
                    continue
                criteria_hits = self._matched_normalized_terms(sentence, criteria_terms)
                if not criteria_hits and self._comparative_contract_axis_reflected(sentence, contract):
                    criteria_hits = ["contract_axis_proxy"]
                section_hits = self._matched_normalized_terms(sentence, section_terms)
                section_aligned = bool(section_pattern.search(sentence)) if section_pattern else False
                if comparison_sentence_pattern.search(sentence) and not criteria_hits and not section_hits and not section_aligned:
                    axis_shift_count += 1
        return {
            "comparative_fit_sentence_count": fit_sentence_count,
            "comparative_absolute_winner_claim_count": absolute_winner_claim_count,
            "comparative_axis_shift_count": axis_shift_count,
        }

    def _normalize_announcement_body(self, body: str, contract: Dict[str, Any]) -> str:
        return normalize_output_body(body, contract)

    @staticmethod
    def _jaccard_similarity(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def _build_quality_metrics(
        self,
        body: str,
        sections: list,
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
        legal_result: Dict[str, Any] | None = None,
        editor_report: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        text = str(body or "")
        sentences = [item.strip() for item in text.replace("\n", " ").split("。") if item.strip()]
        endings = [sentence[-4:] for sentence in sentences if sentence]
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
        ending_counts: Dict[str, int] = {}
        triple_repeats = 0
        for idx in range(2, len(endings)):
            if endings[idx] == endings[idx - 1] == endings[idx - 2]:
                triple_repeats += 1
        sentence_lengths = [len(sentence) for sentence in sentences]
        paragraph_lengths = [len(paragraph) for paragraph in paragraphs]
        opening_tokens = []
        connective_openings = 0
        explicit_subject_hits = 0
        abstract_hits = 0
        punctuation_total = text.count("、") + text.count("。") + text.count("！") + text.count("？")
        paragraph_topic_mix_count = 0
        adjacent_paragraph_overlap_high_count = 0
        paragraph_duplication_risk_count = 0
        paragraph_sentence_counts: list[int] = []
        single_sentence_paragraph_count = 0
        bridge_phrase_count = sum(len(pattern.findall(text)) for pattern in self.BRIDGE_PHRASE_PATTERNS)
        reader_emotion_proxy_count = sum(len(pattern.findall(text)) for pattern in self.READER_EMOTION_PROXY_PATTERNS)
        for sentence in sentences:
            connective_probe = re.sub(r"^##\s+.+?\s{2,}", "", sentence.strip())
            normalized = re.sub(r"\s+", "", sentence)
            opening_tokens.append(normalized[:4])
            if re.match(
                r"^(また|そして|しかし|ただ|なお|一方で|たとえば|つまり|そのため|まず|次に)",
                re.sub(r"\s+", "", connective_probe),
            ):
                connective_openings += 1
            if re.search(r"(私は|私たちは|当社は|弊社は|読者は|あなたは)", normalized):
                explicit_subject_hits += 1
            abstract_hits += len(re.findall(r"(重要|必要|効果|価値|課題|ポイント|状況|観点|こと|もの|ため)", normalized))
            ending_key = normalized[-4:] if normalized else ""
            if ending_key:
                ending_counts[ending_key] = ending_counts.get(ending_key, 0) + 1
        for paragraph in paragraphs:
            paragraph_body = self._strip_heading_text(paragraph)
            if not paragraph_body:
                continue
            paragraph_sentences = [item.strip() for item in re.split(r"(?<=[。！？])", paragraph_body) if item.strip()]
            if paragraph_sentences:
                paragraph_sentence_counts.append(len(paragraph_sentences))
                if len(paragraph_sentences) == 1:
                    single_sentence_paragraph_count += 1
            if len(paragraph_sentences) < 3:
                continue
            term_sets = [set(self._content_terms(item, limit=8)) for item in paragraph_sentences]
            overlaps = [
                self._jaccard_similarity(term_sets[idx], term_sets[idx + 1])
                for idx in range(len(term_sets) - 1)
                if term_sets[idx] and term_sets[idx + 1]
            ]
            if overlaps and self._median(overlaps) < 0.035:
                paragraph_topic_mix_count += 1
        paragraph_term_sets = [set(self._content_terms(self._strip_heading_text(paragraph), limit=12)) for paragraph in paragraphs]
        for idx in range(len(paragraph_term_sets) - 1):
            overlap = self._jaccard_similarity(paragraph_term_sets[idx], paragraph_term_sets[idx + 1])
            if overlap > 0.72:
                paragraph_duplication_risk_count += 1
            if overlap > 0.85:
                adjacent_paragraph_overlap_high_count += 1
        section_chunks = [chunk.strip() for chunk in re.split(r"(?=^##\s+)", text, flags=re.MULTILINE) if chunk.strip()]
        section_term_sets = [set(self._content_terms(self._strip_heading_text(chunk), limit=14)) for chunk in section_chunks]
        section_overlap_high_pairs = 0
        section_openings = []
        paragraph_heading_echo_count = 0
        for idx, chunk in enumerate(section_chunks):
            first_sentence_match = re.search(r"(?m)^(?!##\s+)(.+?[。！？])", chunk)
            if first_sentence_match:
                first_sentence = re.sub(r"\s+", "", first_sentence_match.group(1))
                section_openings.append(first_sentence[:16])
                heading_match = re.search(r"(?m)^##\s+(.+)$", chunk)
                if heading_match:
                    heading_terms = set(self._content_terms(heading_match.group(1), limit=6))
                    first_sentence_terms = set(self._content_terms(first_sentence, limit=6))
                    if heading_terms and first_sentence_terms and self._jaccard_similarity(heading_terms, first_sentence_terms) > 0.74:
                        paragraph_heading_echo_count += 1
            if idx == 0:
                continue
            if self._jaccard_similarity(section_term_sets[idx - 1], section_term_sets[idx]) > 0.48:
                section_overlap_high_pairs += 1
        section_opening_repetition_count = 0
        for idx in range(1, len(section_openings)):
            if section_openings[idx] and section_openings[idx] == section_openings[idx - 1]:
                section_opening_repetition_count += 1
        paragraph_break_semantic_score = 1.0
        if paragraphs:
            paragraph_break_semantic_score = max(
                0.0,
                round(
                    1.0
                    - (paragraph_topic_mix_count / max(1, len(paragraphs))) * 0.65
                    - (paragraph_duplication_risk_count / max(1, len(paragraphs) - 1)) * 0.35,
                    4,
                ),
            )
        article_type = str(contract.get("article_type") or "")
        subject_policy_by_type = {
            "announcement": "explicit_when_scope_changes",
            "daily_story": "allow_implicit_first_person",
            "branding": "light_corporate_anchor",
            "case_study": "balanced_process_subjects",
            "industry_analysis": "explicit_when_scope_changes",
            "comparative_review": "explicit_when_comparing_entities",
        }
        ending_policy_hint = str(style_profile.get("ending_distribution_hint") or "balanced")
        topic_echo_metrics = self._topic_echo_metrics(text, str(contract.get("topic") or ""), sections)
        prompt_follow_metrics = self._prompt_follow_metrics(text, contract, sections)
        prompt_context_metrics = self._prompt_context_metrics(text, contract)
        source_grounding_metrics = self._source_grounding_metrics(text, contract)
        announcement_metrics = (
            self._announcement_fact_metrics(text, sections)
            if article_type == "announcement"
            else {
                "fact_slot_coverage": 0.0,
                "fact_slot_reuse_count": 0,
                "announcement_action_sentence_count": 0,
                "announcement_invalid_modal_pattern_count": 0,
            }
        )
        case_result_metrics = self._case_result_metrics(text, sections, article_type)
        comparative_metrics = self._comparative_review_metrics(text, sections, article_type, contract)
        example_metrics = self._example_specificity_metrics(text)
        citation_guard = dict((legal_result or {}).get("citation_guard", {}) or {})
        normalized_editor_report = dict(editor_report or {})
        return {
            "body_chars": len(text),
            "section_count": len(sections),
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "unique_ending_patterns": len(set(endings)),
            "triple_ending_repeat_count": triple_repeats,
            "sentence_length_cv": self._coefficient_of_variation(sentence_lengths),
            "paragraph_length_cv": self._coefficient_of_variation(paragraph_lengths),
            "opening_variety_ratio": round(len(set(token for token in opening_tokens if token)) / max(1, len(sentences)), 4),
            "connective_opening_rate": round(connective_openings / max(1, len(sentences)), 4),
            "explicit_subject_ratio": round(explicit_subject_hits / max(1, len(sentences)), 4),
            "abstract_term_density": round(abstract_hits / max(1, len(sentences)), 4),
            "punctuation_density_per_sentence": round(punctuation_total / max(1, len(sentences)), 4),
            "avg_sentences_per_paragraph": round(len(sentences) / max(1, len(paragraphs)), 4),
            "single_sentence_paragraph_ratio": round(
                single_sentence_paragraph_count / max(1, len(paragraph_sentence_counts)),
                4,
            ),
            "paragraph_sentence_count_cv": self._coefficient_of_variation(paragraph_sentence_counts),
            "paragraph_topic_mix_count": paragraph_topic_mix_count,
            "adjacent_paragraph_overlap_high_count": adjacent_paragraph_overlap_high_count,
            "paragraph_duplication_risk_count": paragraph_duplication_risk_count,
            "paragraph_heading_echo_count": paragraph_heading_echo_count,
            "paragraph_break_semantic_score": paragraph_break_semantic_score,
            "section_overlap_high_pairs": section_overlap_high_pairs,
            "section_opening_repetition_count": section_opening_repetition_count,
            "ending_distribution_top": dict(sorted(ending_counts.items(), key=lambda item: item[1], reverse=True)[:4]),
            "bridge_phrase_count": bridge_phrase_count,
            "reader_emotion_proxy_count": reader_emotion_proxy_count,
            **topic_echo_metrics,
            **prompt_follow_metrics,
            **prompt_context_metrics,
            **source_grounding_metrics,
            **announcement_metrics,
            **case_result_metrics,
            **comparative_metrics,
            **example_metrics,
            "sentence_integrity_warning_count": int(normalized_editor_report.get("sentence_integrity_warning_count", 0) or 0),
            "unverified_legal_citation_count": len(list(citation_guard.get("unverified_citations", []) or [])),
            "target_subject_policy": subject_policy_by_type.get(article_type, "balanced"),
            "target_ending_policy": ending_policy_hint,
        }
