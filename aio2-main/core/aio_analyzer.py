import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from collections import Counter
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import time
import json
import logging
from datetime import datetime, timedelta
from sudachipy import tokenizer, dictionary
# Phase 1: Sudachi品詞判定に移行のため不要化 (2026-01-29)
# from core.knowledge_graph import calculate_entity_recognition_score
# Phase 2: カテゴリ別重み付け (2026-01-29)
# Phase 3: 補完辞書 (2026-01-29)
# Phase 4: 正規化 (2026-01-29)
from core.knowledge_graph import (
    get_category_weight,
    is_supplementary_entity,
    normalize_entity,
    group_entities_by_normalized
)
from core.wikidata_client import WikidataClient
from core.config import config
from core.aio.commerce_readiness import assess_openai_commerce_readiness, build_perplexity_operational_note
from core.aio.schema_validator import extract_json_ld, infer_schema_site_type, validate_schema
from core.aio.gap_analyzer import analyze_content_schema_gap
from core.safe_fetch import safe_fetch_url

logger = logging.getLogger(__name__)

# Provider readiness is an evidence contract, not a score.  Do not collapse a
# missing observation into pass: callers need to distinguish a confirmed gate
# from a gate that could not be read.
PROVIDER_STATUS_ORDER = {"not_applicable": 0, "pass": 1, "unverified": 2, "fail": 3}
PROVIDER_STATUS_LABELS = {
    "pass": "通過",
    "fail": "要対応",
    "unverified": "未確認",
    "not_applicable": "対象外",
}
PROVIDER_LABELS = {
    "google": "Google",
    "openai_search": "OpenAI Search",
    "perplexity": "Perplexity",
    "claude_search": "Claude Search",
}
OFFICIAL_SEARCH_BOTS = {
    "google": "googlebot",
    "openai_search": "oai-searchbot",
    "perplexity": "perplexitybot",
    "claude_search": "claude-searchbot",
}
INFORMATIONAL_BOTS = {
    "gptbot": "GPTBot",
    "chatgpt-user": "ChatGPT-User",
    "claude-user": "Claude-User",
    "claudebot": "ClaudeBot",
    "ccbot": "CCBot",
}

# ===== P02: 文中E-E-A-T検出パターン（日本語対応 2026-02-27） =====
# JSON-LDに頼らず、本文テキストから日本語固有のE-E-A-Tシグナルを検出する。
EEAT_PATTERNS_JA = {
    # 資格・免許
    "license": [
        r"(?:一級|二級|三級)?(?:建築|施工管理|電気工事|危険物取扱|宅地建物取引)+(?:士|技士|主任者|検定)",
        r"(?:医師|歯科医師|薬剤師|看護師|管理栄養士|社会福祉士|精神保健福祉士)",
        r"(?:弁護士|司法書士|行政書士|税理士|公認会計士|社会保険労務士|中小企業診断士)",
        r"(?:ファイナンシャルプランナー|FP[1-3]級|AFP|CFP)",
        r"(?:博士|修士|学士)\s*(?:号|課程)",
        r"Ph\.?D",
    ],
    # 著者明示
    "author_explicit": [
        r"(?:著者|筆者|執筆者|監修者?|編集者?)\s*[:：]\s*[\u4e00-\u9fff\u3040-\u30ff]{2,10}",
        r"(?:執筆|監修)\s*[：:]\s*[\u4e00-\u9fff\u3040-\u30ff]{2,10}",
        r"[\u4e00-\u9fff\u3040-\u30ff]{2,6}\s*(?:医師|弁護士|税理士|薬剤師|栄養士)",
    ],
    # 組織・経験
    "organization": [
        r"(?:株式会社|有限会社|合同会社|一般社団法人|公益財団法人|医療法人)",
        r"[0-9０-９]{1,2}年以上の(?:経験|実績|キャリア)",
        r"元\s*[\u4e00-\u9fff]{2,10}(?:勤務|所属|在籍)?",
    ],
    # 一次情報シグナル（体験・実測）
    "first_hand": [
        r"(?:実際に|自分で|筆者が|私が)\s*(?:試|使|調|体験|確認)",
        r"(?:実測|計測|独自(?:調査|検証|データ))",
        r"[0-9０-９]+\s*(?:件|例|症例|事例|サンプル)\s*(?:を)?(?:分析|調査|確認|検証)",
    ],
}


# ===== P03: GEO基本指標パターン（統計・数値密度 2026-02-27） =====
# GEO論文（ACM SIGKDD 2024）実証: 統計密度が高いほどAI可視性+30〜40%
STATISTICS_PATTERNS = [
    r"[0-9０-９]+\s*(?:%|％|倍|件|人|社|年|か月|ヶ月|万|億|兆)",  # 数値+単位
    r"[0-9０-９]+\s*[〜~]\s*[0-9０-９]+",                          # 範囲表現
    r"(?:約|およそ|最大|最小|平均|中央値)\s*[0-9０-９]",            # 修飾付き数値
    r"(?:前年比|前月比|対前年|YoY|比較|増加|減少|上昇|下落)\s*[0-9０-９]",  # 比較
    r"調査(?:によると|では|の結果)|アンケート|統計|データ(?:によると|では)",  # 調査出典
    r"(?:出典|参考|引用)\s*[:：]",                                  # 外部引用
]


class AIOContentAnalyzer:
    def __init__(self, enable_wikidata: bool = True, wikidata_top_k: int = 3):
        self.dict_obj = None
        self.tokenizer_obj = None
        self.sudachi_dict_variant = None

        sudachi_errors = []
        # sudachidict-full を導入済み環境を優先し、未導入辞書への依存で0点化しないようにする
        for dict_name, kwargs in (
            ("full", {"dict": "full"}),
            ("core", {"dict": "core"}),
            ("small", {"dict": "small"}),
            ("default", {}),
        ):
            try:
                dict_obj = dictionary.Dictionary(**kwargs) if kwargs else dictionary.Dictionary()
                self.dict_obj = dict_obj
                self.tokenizer_obj = dict_obj.create()
                self.sudachi_dict_variant = dict_name
                if dict_name != "full":
                    print(f"[WARNING] Sudachi fallback dictionary in use: {dict_name}")
                break
            except Exception as e:
                sudachi_errors.append(f"{dict_name}: {e}")

        if not self.tokenizer_obj:
            joined_errors = " | ".join(sudachi_errors) if sudachi_errors else "unknown error"
            print(f"[WARNING] Sudachi dictionary not found: {joined_errors}. PID calculation will be skipped.")

        self.enable_wikidata = enable_wikidata
        self.wikidata_top_k = max(0, int(wikidata_top_k or 0))
        self._wikidata_client = None

    def _get_wikidata_client(self) -> Optional[WikidataClient]:
        if not self.enable_wikidata or self.wikidata_top_k <= 0:
            return None
        if self._wikidata_client is None:
            self._wikidata_client = WikidataClient()
        return self._wikidata_client

    def _merge_status(self, current: str, candidate: str) -> str:
        return candidate if PROVIDER_STATUS_ORDER.get(candidate, 0) > PROVIDER_STATUS_ORDER.get(current, 0) else current

    def _parse_robots_agent_access(
        self, robots_text: str, agents: List[str], target_url: str
    ) -> Dict[str, Optional[bool]]:
        """Evaluate robots directives for the analysed URL path.

        The most-specific matching user-agent group wins over ``*``; within a
        group the longest matching Allow/Disallow rule wins, with Allow winning
        a tie.  ``None`` means the robots document did not establish access.
        """
        access_map: Dict[str, Optional[bool]] = {agent: None for agent in agents}
        if not robots_text:
            return access_map

        target = urlsplit(target_url)
        target_path = target.path or "/"
        if target.query:
            target_path = f"{target_path}?{target.query}"
        rules: Dict[str, List[tuple[str, str]]] = {}
        current_agents: List[str] = []
        previous_was_user_agent = False

        for raw_line in robots_text.splitlines():
            line = raw_line.split("#", 1)[0].strip().lower()
            if not line:
                previous_was_user_agent = False
                continue

            if line.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                if previous_was_user_agent and agent:
                    current_agents.append(agent)
                else:
                    current_agents = [agent] if agent else []
                if agent and agent not in rules:
                    rules[agent] = []
                previous_was_user_agent = True
                continue

            if not current_agents or not (line.startswith("allow:") or line.startswith("disallow:")):
                previous_was_user_agent = False
                continue

            directive, value = line.split(":", 1)
            for agent in current_agents:
                if agent not in rules:
                    rules[agent] = []
                rules[agent].append((directive, value.strip()))
            previous_was_user_agent = False

        for agent in agents:
            agent_key = agent.lower()
            matching_groups = [
                group for group in rules
                if group == "*" or agent_key.startswith(group)
            ]
            if not matching_groups:
                access_map[agent] = True
                continue
            longest_agent_match = max(len(group) for group in matching_groups)
            applicable_groups = [group for group in matching_groups if len(group) == longest_agent_match]
            matched_rules: List[tuple[int, str]] = []
            for group in applicable_groups:
                for directive, raw_pattern in rules[group]:
                    # Empty Disallow explicitly permits all paths.
                    if directive == "disallow" and raw_pattern == "":
                        continue
                    anchored = raw_pattern.endswith("$")
                    literal_pattern = raw_pattern[:-1] if anchored else raw_pattern
                    pattern = re.escape(literal_pattern).replace(r"\*", ".*")
                    if anchored:
                        pattern += "$"
                    else:
                        pattern += ".*"
                    if re.match(pattern, target_path):
                        matched_rules.append((len(raw_pattern.rstrip("$")), directive))
            if not matched_rules:
                access_map[agent] = True
                continue
            longest_rule = max(length for length, _ in matched_rules)
            strongest = [directive for length, directive in matched_rules if length == longest_rule]
            access_map[agent] = "allow" in strongest
        return access_map

    def _extract_provider_controls(self, soup: BeautifulSoup, response_headers: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Collect meta and X-Robots-Tag controls into one provider evidence shape."""
        controls: Dict[str, Dict[str, Any]] = {
            provider: {"meta_tokens": set(), "header_tokens": set(), "max_snippet": None}
            for provider in PROVIDER_LABELS
        }
        bot_to_provider = {agent: provider for provider, agent in OFFICIAL_SEARCH_BOTS.items()}

        def _parse_meta_content(content: str) -> tuple[set[str], Optional[int]]:
            tokens: set[str] = set()
            max_snippet: Optional[int] = None
            for raw_part in str(content or "").split(","):
                part = raw_part.strip().lower()
                if not part:
                    continue
                if ":" in part:
                    key, value = [p.strip() for p in part.split(":", 1)]
                    tokens.add(key)
                    if key == "max-snippet":
                        try:
                            max_snippet = int(value)
                        except Exception:
                            max_snippet = None
                else:
                    tokens.add(part)
            return tokens, max_snippet

        def _apply(raw_name: str, content: Any, source: str) -> None:
            name = raw_name.strip().lower()
            tokens, max_snippet = _parse_meta_content(str(content or ""))
            targets = list(PROVIDER_LABELS) if name == "robots" else [bot_to_provider[name]] if name in bot_to_provider else []
            for provider in targets:
                controls[provider][f"{source}_tokens"].update(tokens)
                if max_snippet is not None:
                    controls[provider]["max_snippet"] = max_snippet

        for meta in soup.find_all("meta"):
            name = str(meta.get("name") or meta.get("property") or "").strip().lower()
            _apply(name, meta.get("content", ""), "meta")
        for header_name, header_value in (response_headers or {}).items():
            if str(header_name).lower() != "x-robots-tag":
                continue
            values = header_value if isinstance(header_value, (list, tuple)) else [header_value]
            for value in values:
                for directive in str(value or "").split(";"):
                    target_name, separator, content = directive.partition(":")
                    if separator and target_name.strip().lower() in bot_to_provider:
                        _apply(target_name, content, "header")
                    else:
                        _apply("robots", directive, "header")
        for provider, evidence in controls.items():
            effective_tokens = evidence["meta_tokens"] | evidence["header_tokens"]
            evidence["meta_tokens"] = sorted(evidence["meta_tokens"])
            evidence["header_tokens"] = sorted(evidence["header_tokens"])
            evidence["effective_tokens"] = sorted(effective_tokens)
            evidence["noindex"] = "noindex" in effective_tokens or "none" in effective_tokens
            evidence["nosnippet"] = "nosnippet" in effective_tokens or "none" in effective_tokens
            evidence["data_nosnippet_count"] = len(soup.select("[data-nosnippet]")) if provider == "google" else 0
        return controls

    def assess_provider_readiness(
        self,
        soup: BeautifulSoup,
        tech_results: Dict[str, Any],
        structure_results: Dict[str, Any],
        inline_eeat: Dict[str, Any],
        response_headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        provider_readiness: Dict[str, Any] = {"informational_notes": []}
        bot_access = tech_results.get("bot_access", {}) or {}
        provider_controls = self._extract_provider_controls(soup, response_headers)
        weak_eeat = float(inline_eeat.get("combined_score", 0.0) or 0.0) < 4.0

        def _make_provider_entry(key: str, checks: List[Dict[str, str]], heuristic_notes: List[str]) -> Dict[str, Any]:
            status = "pass"
            for check in checks:
                status = self._merge_status(status, str(check.get("status") or "pass"))
            summary_map = {
                "pass": "確認できた公開条件に阻害はありません。",
                "fail": "公式公開条件で到達性または抜粋可否を阻害する要素があります。",
                "unverified": "robots.txt の取得または評価が完了していないため、公開条件を確認できません。",
                "not_applicable": "この公開条件は対象外です。",
            }
            return {
                "label": PROVIDER_LABELS[key],
                "status": status,
                "status_label": PROVIDER_STATUS_LABELS[status],
                "summary": summary_map[status],
                "official_checks": checks,
                "heuristic_notes": heuristic_notes,
            }

        def _robots_status(agent: str) -> str:
            if tech_results.get("robots_status") != "pass":
                return "unverified"
            return "fail" if bot_access.get(agent) is False else "pass"

        def _control_checks(provider: str) -> List[Dict[str, str]]:
            controls = provider_controls[provider]
            checks = [
                {"label": "noindex が無効", "status": "fail" if controls["noindex"] else "pass"},
                {"label": "nosnippet が無効", "status": "fail" if controls["nosnippet"] else "pass"},
            ]
            if controls["max_snippet"] == 0:
                checks.append({"label": "max-snippet 制御", "status": "fail"})
            else:
                checks.append({"label": "max-snippet 制御", "status": "pass"})
            if controls["data_nosnippet_count"] > 0:
                checks.append({"label": "data-nosnippet 利用", "status": "fail"})
            return checks

        google_checks = [
            {
                "label": "Googlebot のクロール許可",
                "status": _robots_status("googlebot"),
            },
        ] + _control_checks("google")

        google_heuristics: List[str] = []
        if not structure_results.get("has_json_ld"):
            google_heuristics.append("JSON-LD は公式必須ではありませんが、内容理解の補助にはなります。")
        if weak_eeat:
            google_heuristics.append("著者・運営者・一次情報の明示が弱く、信頼性評価で不利になりえます。")
        provider_readiness["google"] = _make_provider_entry("google", google_checks, google_heuristics)

        for provider_key, agent in (
            ("openai_search", "oai-searchbot"),
            ("perplexity", "perplexitybot"),
            ("claude_search", "claude-searchbot"),
        ):
            checks = [{
                "label": f"{PROVIDER_LABELS[provider_key]} 用クローラーの許可",
                "status": _robots_status(agent),
            }] + _control_checks(provider_key)
            heuristics: List[str] = []
            if weak_eeat:
                heuristics.append("著者・運営者・一次情報の明示が弱く、引用判断で不利になりえます。")
            provider_readiness[provider_key] = _make_provider_entry(provider_key, checks, heuristics)

        openai_commerce = assess_openai_commerce_readiness(soup)
        if openai_commerce.get("applicable"):
            provider_readiness["openai_search"]["heuristic_notes"].append(
                f"Commerce note: {openai_commerce.get('summary')}"
            )

        provider_readiness["special_notes"] = {
            "openai_commerce": openai_commerce,
            "perplexity_operational": build_perplexity_operational_note(),
        }

        informational_notes: List[Dict[str, str]] = []
        informational_notes.append({
            "label": "llms.txt",
            "status": "present" if tech_results.get("llms_txt") else "missing",
            "message": "公式要件ではありません。AI向け案内ファイルとして運用ポリシー次第で設置します。" if not tech_results.get("llms_txt") else "公式要件ではありませんが、AI向け案内ファイルとして配置されています。",
        })

        if tech_results.get("google_extended_disallowed"):
            informational_notes.append({
                "label": "Google-Extended",
                "status": "blocked",
                "message": "Google Search の掲載条件ではなく、Gemini Apps / Vertex AI の学習・grounding 方針に関する設定です。",
            })

        for agent, label in INFORMATIONAL_BOTS.items():
            if bot_access.get(agent) is False:
                informational_notes.append({
                    "label": label,
                    "status": "blocked",
                    "message": f"{label} は検索の必須条件ではなく、学習やユーザー経由取得などの補助経路に関する設定です。",
                })

        provider_readiness["informational_notes"] = informational_notes
        provider_readiness["provider_controls"] = provider_controls
        return provider_readiness

    def analyze(
        self, url: str, html: str, response_time_ms: float = None,
        response_headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for AIO analysis with stricter calibration.
        Target: Average site = 50-70, Note.com/Wikipedia level = 80-90
        """
        if not html:
            return {"error": "Empty HTML content"}

        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script/style for text analysis
        analysis_soup = BeautifulSoup(html, 'html.parser')
        for script in analysis_soup(["script", "style"]):
            script.decompose()
        text = analysis_soup.get_text(separator=' ', strip=True)

        # 1. PID Score (Already reasonably calibrated)
        pid_score = self.calculate_pid(text)
        
        # 2. Structure Score (STRICTER)
        structure_results = self.analyze_structure(html)
        structure_score = structure_results.get("score", 0.0)

        schemas: List[Dict[str, Any]] = []
        schema_validation = {}
        schema_site_type = "company"
        try:
            schemas = extract_json_ld(html)
            schema_site_type = infer_schema_site_type(html, url, schemas=schemas)
            schema_validation = validate_schema(schemas, site_type=schema_site_type)
        except Exception as e:
            schema_validation = {"error": str(e)}

        # 3. Entity Salience Score (STRICTER)
        entity_results = self.calculate_entity_salience(text)
        entity_score = self._calculate_entity_score(entity_results)

        # 4. Tech Score (With penalties)
        tech_results = self.check_technical_aio(url, response_time_ms)
        tech_score = tech_results.get("score", 0.0)

        # ===== PHASE 2/3 NEW FEATURES =====
        # Phase 2: Citation Readiness Index
        citation_readiness = self.calculate_citation_readiness(text)

        # Phase 2: Contextual Freshness Signal
        contextual_freshness = self.calculate_contextual_freshness(soup)

        # Phase 2: AEO Patterns (Definitional Check)
        aeo_patterns = self.analyze_aeo_patterns(soup)

        # Phase 3: Knowledge Graph Entity Linking
        entity_linking = self.calculate_entity_linking(text)

        # P02: 文中E-E-A-T検出（日本語対応）
        inline_eeat = self.detect_inline_eeat(text, soup, structure_results.get("eeat", {}))

        # P03: GEO基本指標（TL;DR + 統計密度）
        tldr_result = self.detect_tldr_summary(text, soup)
        stats_density = self.calculate_statistics_density(text)

        # Provider readiness: official gates + internal heuristics + informational notes
        provider_readiness = self.assess_provider_readiness(
            soup=soup,
            tech_results=tech_results,
            structure_results=structure_results,
            inline_eeat=inline_eeat,
            response_headers=response_headers,
        )

        content_schema_gap = {}
        if schemas:
            content_schema_gap = analyze_content_schema_gap(text, schemas, site_type=schema_site_type)
        else:
            content_schema_gap = {
                "gaps": [],
                "recommendations": ["Schema.orgが検出されませんでした"],
                "aio_improvement_potential": 0,
            }

        # ===== NORMALIZE PHASE 2/3 SCORES =====
        # Citation Readiness の正規化（既に0-1範囲）
        citation_score = citation_readiness.get('score', 0.0)

        # Contextual Freshness の正規化（既に0-1範囲）
        freshness_score = contextual_freshness.get('score', 0.0)

        # AEO Patterns の正規化（パターン検出数を0-1にマッピング）
        aeo_detected = len(aeo_patterns.get('patterns', []))
        if aeo_patterns.get("confidence") == "low":
            aeo_score = aeo_patterns.get("score", 0.0)
        else:
            aeo_score = min(aeo_detected / 5.0, 1.0)  # 5パターン以上で満点

        # Entity Linking の正規化（既に0-1範囲）
        entity_linking_score = entity_linking.get('score', 0.0)

        penalties: List[str] = []
        penalty_multiplier = 1.0

        # ===== ENHANCED WEIGHTED SCORE (P06: E-E-A-T組み込み版 2026-02-27) =====
        # 重み合計 = 1.00
        # PID 0.20 + Structure 0.15 + Entity 0.12 + Tech 0.10 + EEaT 0.08
        # + Citation 0.10 + Freshness 0.06 + AEO 0.05 + EntityLink 0.04
        # + TL;DR 0.05 + StatsDensity 0.05 = 1.00
        eeat_normalized = inline_eeat.get("combined_score", 0.0) / 10.0  # 0〜10 → 0〜1
        raw_score = (
            # Core Metrics (57%)
            (pid_score       * 0.20) +
            (structure_score * 0.15) +
            (entity_score    * 0.12) +  # 0.15 → 0.12（E-E-A-T追加分を一部吸収）
            (tech_score      * 0.10) +

            # E-E-A-T（P06新規: 全業種で著者信頼性を直接反映）
            (eeat_normalized * 0.08) +

            # Phase 2/3 Enhanced Metrics (25%)
            (citation_score        * 0.10) +
            (freshness_score       * 0.06) +  # 0.08 → 0.06
            (aeo_score             * 0.05) +  # 0.07 → 0.05
            (entity_linking_score  * 0.04) +  # 0.05 → 0.04

            # P03: GEO指標（TL;DR 5% + 統計密度 5% = 10%）
            (tldr_result["score"] / 5.0  * 0.05) +
            (stats_density["score"] / 10.0 * 0.05)
        ) * 100

        logger.debug(
            "Score breakdown: PID=%.2f Structure=%.2f Entity=%.2f Tech=%.2f "
            "EEAT=%.2f Citation=%.2f Freshness=%.2f AEO=%.2f EntityLink=%.2f "
            "TL;DR=%.2f StatsDensity=%.2f",
            pid_score, structure_score, entity_score, tech_score,
            eeat_normalized,
            citation_score, freshness_score, aeo_score, entity_linking_score,
            tldr_result["score"] / 5.0,
            stats_density["score"] / 10.0,
        )

        # Apply penalties
        final_score = raw_score * penalty_multiplier

        return {
            "total_score": round(final_score, 1),
            "raw_score": round(raw_score, 1),
            "penalty_multiplier": round(penalty_multiplier, 2),
            "penalties": penalties,
            "scores": {
                "pid_score": round(pid_score * 100, 1),
                "structure_score": round(structure_score * 100, 1),
                "entity_score": round(entity_score * 100, 1),
                "tech_score": round(tech_score * 100, 1),
                "eeat": {
                    "score": inline_eeat.get("combined_score", 0.0),
                    "inline_score": inline_eeat.get("score", 0.0),
                    "detail": inline_eeat,
                },
                "geo_tldr": {
                    "score": tldr_result["score"],
                    "detail": tldr_result,
                },
                "geo_stats": {
                    "score": stats_density["score"],
                    "detail": stats_density,
                },
            },
            "score_breakdown": {
                "core_metrics": {
                    "pid": round(pid_score, 2),
                    "structure": round(structure_score, 2),
                    "entity": round(entity_score, 2),
                    "tech": round(tech_score, 2)
                },
                "enhanced_metrics": {
                    "citation": round(citation_score, 2),
                    "freshness": round(freshness_score, 2),
                    "aeo": round(aeo_score, 2),
                    "entity_linking": round(entity_linking_score, 2)
                }
            },
            "details": {
                "pid": pid_score,
                "structure": structure_results,
                "tech": tech_results,
                "entity_salience_top": dict(sorted(entity_results.items(), key=lambda item: item[1], reverse=True)[:5]) if entity_results else {},
                # Phase 2/3 Enhanced Features
                "citation_readiness": citation_readiness,
                "contextual_freshness": contextual_freshness,
                "aeo_patterns": aeo_patterns,
                "entity_linking": entity_linking,
                # P02: 文中E-E-A-T（日本語対応）
                "inline_eeat": inline_eeat,
                # P03: GEO基本指標
                "geo_tldr": tldr_result,
                "geo_stats": stats_density,
                # Provider readiness: official gates + heuristics + informational notes
                "provider_readiness": provider_readiness,
            },
            "structured_data": {
                "has_json_ld": structure_results.get("has_json_ld", False),
                "list_count": structure_results.get("list_count", 0),
                "table_count": structure_results.get("table_count", 0)
            },
            "schema_validation": schema_validation,
            "content_schema_gap": content_schema_gap,
            "llms_txt": {
                "exists": tech_results.get("llms_txt", False)
            },
            "immediate_actions": self._generate_actions(
                pid_score,
                structure_results,
                tech_results,
                provider_readiness=provider_readiness,
                freshness=contextual_freshness,
                aeo=aeo_patterns,
                citation=citation_readiness,
                entity_linking=entity_linking,
                inline_eeat=inline_eeat,  # P02: 文中E-E-A-T
                tldr=tldr_result,         # P03: TL;DR
                stats=stats_density,      # P03: 統計密度
            )
        }

    def _get_sudachi_tokenizer(self, mode: str = 'A'):
        """
        Helper method to get Sudachi split mode.

        Args:
            mode: 'A' (short unit), 'B' (middle unit), or 'C' (named entity/long unit)

        Returns:
            Sudachi SplitMode constant
        """
        mode_map = {
            'A': tokenizer.Tokenizer.SplitMode.A,
            'B': tokenizer.Tokenizer.SplitMode.B,
            'C': tokenizer.Tokenizer.SplitMode.C
        }

        return mode_map.get(mode.upper(), tokenizer.Tokenizer.SplitMode.A)

    def calculate_pid(self, text: str) -> float:
        """
        Calculates Propositional Idea Density (PID).
        Target: 0.5 - 0.7 for high-quality content.
        Uses Sudachi A-mode for shortest tokenization.
        """
        if not self.tokenizer_obj:
            return 0.0

        try:
            # Tokenize with Sudachi Mode-A
            mode_a = self._get_sudachi_tokenizer('A')
            tokens = self.tokenizer_obj.tokenize(text[:5000], mode_a)
            content_words = 0
            total_tokens = len(tokens)

            if total_tokens == 0:
                return 0.0

            for token in tokens:
                pos = token.part_of_speech()  # Returns tuple like ('名詞', '普通名詞', '一般', ...)
                # Check for content words: NOUN, VERB, ADJ, NUM (excluding pronouns)
                if pos[0] in ['名詞', '動詞', '形容詞', '形状詞'] and pos[1] != '代名詞':
                    content_words += 1

            raw_pid = content_words / total_tokens
            # Stricter normalization: 0.65 = 1.0 (max), 0.4 = 0.6
            normalized = min(raw_pid / 0.65, 1.0)
            return normalized
        except Exception as e:
            print(f"[ERROR] PID calculation error: {e}")
            return 0.0

    def analyze_structure(self, html: str) -> dict:
        """
        Evaluates HTML structure with STRICTER criteria.
        Checks: Semantic tags, heading hierarchy, FAQs, lists, tables, JSON-LD, E-E-A-T, Multimodal.
        """
        soup = BeautifulSoup(html, 'html.parser')
        text_length = len(soup.get_text())
        if text_length == 0: return {"score": 0.0}

        score = 0.0
        
        # 1. Semantic HTML tags (max 0.2)
        has_article = bool(soup.find('article'))
        has_section = bool(soup.find('section'))
        has_header = bool(soup.find('header'))
        has_main = bool(soup.find('main'))
        semantic_count = sum([has_article, has_section, has_header, has_main])
        score += min(semantic_count * 0.05, 0.2)
        
        # 2. Heading hierarchy (max 0.25)
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        # Ideal: 1 H1, 3+ H2, H3s under H2s
        if h1_count == 1:
            score += 0.1
        if h2_count >= 3:
            score += 0.1
        elif h2_count >= 1:
            score += 0.05
        if h3_count >= 2:
            score += 0.05
        
        # 3. Lists and Tables (max 0.2)
        lists = len(soup.find_all(['ul', 'ol']))
        tables = len(soup.find_all('table'))
        # Stricter: need at least 2 lists AND 1 table for max
        list_score = min(lists * 0.03, 0.12)
        table_score = min(tables * 0.04, 0.08)
        score += list_score + table_score
        
        # 4. JSON-LD presence (scoreには直接加算しない。補助シグナルとして保持)
        json_ld = bool(soup.find('script', {'type': 'application/ld+json'}))

        # 5. FAQ-like Q&A sections (0.15)
        # Check for common Q&A patterns
        faq_patterns = soup.find_all(string=re.compile(r'(よくある質問|FAQ|Q\s*[:：]|Q\.)', re.IGNORECASE))
        if len(faq_patterns) >= 3:
            score += 0.15
        elif len(faq_patterns) >= 1:
            score += 0.05

        # ===== NEW: E-E-A-T Signal Detection (Author/Organization in JSON-LD) =====
        eeat_signals = {
            "has_author": False,
            "has_organization": False,
            "author_name": None,
            "organization_name": None,
        }
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_ld_scripts:
            try:
                if not script.string:
                    continue
                import json
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("@type", "")
                    # Check for Person/Author
                    if item_type == "Person" or "author" in item:
                        eeat_signals["has_author"] = True
                        author_data = item if item_type == "Person" else item.get("author", {})
                        if isinstance(author_data, dict):
                            eeat_signals["author_name"] = author_data.get("name")
                        elif isinstance(author_data, str):
                            eeat_signals["author_name"] = author_data
                    # Check for Organization/Publisher
                    if item_type == "Organization" or "publisher" in item:
                        eeat_signals["has_organization"] = True
                        org_data = item if item_type == "Organization" else item.get("publisher", {})
                        if isinstance(org_data, dict):
                            eeat_signals["organization_name"] = org_data.get("name")
                        elif isinstance(org_data, str):
                            eeat_signals["organization_name"] = org_data
            except Exception:
                continue

        # ===== NEW: Multimodal Signal Detection (Image Alt Quality) =====
        multimodal_signals = {
            "total_images": 0,
            "images_with_alt": 0,
            "alt_quality_score": 0.0,
        }
        images = soup.find_all('img')
        multimodal_signals["total_images"] = len(images)
        good_alt_count = 0
        for img in images:
            alt = img.get('alt', '')
            if alt and len(alt.strip()) > 0:
                multimodal_signals["images_with_alt"] += 1
                # Quality check: alt should be descriptive (>10 chars, not just filename)
                if len(alt.strip()) > 10 and not re.match(r'^[\w_-]+\.(jpg|png|gif|webp|svg)$', alt.strip(), re.IGNORECASE):
                    good_alt_count += 1
        if multimodal_signals["total_images"] > 0:
            multimodal_signals["alt_quality_score"] = round(good_alt_count / multimodal_signals["total_images"], 2)

        return {
            "score": min(score, 1.0),
            "has_json_ld": json_ld,
            "has_semantic_tags": semantic_count >= 2,
            "list_count": lists,
            "table_count": tables,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "faq_detected": len(faq_patterns) >= 1,
            # NEW: E-E-A-T and Multimodal signals
            "eeat": eeat_signals,
            "multimodal": multimodal_signals,
        }

    def detect_inline_eeat(
        self,
        text: str,
        soup: BeautifulSoup,
        existing_eeat_signals: Optional[dict] = None,
    ) -> dict:
        """
        日本語本文テキストからE-E-A-Tシグナルを検出し、スコアと詳細を返す。
        JSON-LDに頼らず、本文中の資格・著者明示・組織・一次情報表現を正規表現で検出する。
        fail-open: 検出失敗時は score=0.0 を返し分析全体を止めない。

        Returns:
            {
                "score": float(0〜10),           # インライン検出スコア
                "signals": dict,                 # カテゴリ別検出結果
                "signal_count": int,             # 総検出シグナル数
                "has_json_ld_eeat": bool,        # JSON-LD経由のE-E-A-T検出済みか
                "combined_score": float,         # JSON-LD + inline の合算（0〜10）
                "advice": list[str],             # 不足シグナルに対するアドバイス
            }
        """
        _empty = {
            "score": 0.0, "signals": {}, "signal_count": 0,
            "has_json_ld_eeat": False, "combined_score": 0.0, "advice": [],
        }
        try:
            signals: dict = {}
            total_hits = 0

            for category, patterns in EEAT_PATTERNS_JA.items():
                hits: list = []
                for pat in patterns:
                    matches = re.findall(pat, text)
                    for m in matches[:3]:  # 同一パターンは最大3件
                        if isinstance(m, tuple):
                            hits.append("".join(part for part in m if part))
                        else:
                            hits.append(m)
                signals[category] = list(dict.fromkeys(hits))  # 順序保持で重複除去
                total_hits += len(signals[category])

            # スコア計算（上限10点）
            score = min(10.0, (
                min(4.0, len(signals.get("license", [])) * 2.0) +
                min(3.0, len(signals.get("author_explicit", [])) * 1.5) +
                min(2.0, len(signals.get("organization", [])) * 1.0) +
                min(1.0, len(signals.get("first_hand", [])) * 0.5)
            ))

            # 既存JSON-LD E-E-A-Tスコアを算出（has_author/has_organization フラグから）
            eeat = existing_eeat_signals or {}
            existing_score = 0.0
            if eeat.get("has_author"):
                existing_score += 3.0
            if eeat.get("has_organization"):
                existing_score += 2.0
            existing_score = min(5.0, existing_score)

            combined_score = min(10.0, score + existing_score * 0.5)

            # 不足シグナルに対するアドバイス
            advice: list = []
            if score < 3.0:
                advice.append(
                    "著者の氏名・資格・所属をページ内テキストに明記してください"
                    "（例: 監修：山田太郎 税理士）"
                )
            if not eeat.get("has_author") and not eeat.get("has_organization"):
                advice.append(
                    "schema.org/Person の JSON-LD を実装し、"
                    "著者の資格・所属をマークアップしてください"
                )
            if not signals.get("first_hand"):
                advice.append(
                    "実測データ・独自調査・体験談など一次情報を含めると"
                    "AIに引用されやすくなります"
                )

            return {
                "score": round(score, 2),
                "signals": signals,
                "signal_count": total_hits,
                "has_json_ld_eeat": existing_score > 0,
                "combined_score": round(combined_score, 2),
                "advice": advice,
            }
        except Exception as e:
            logger.warning("detect_inline_eeat failed: %s", e)
            return _empty

    def detect_tldr_summary(self, text: str, soup: BeautifulSoup) -> dict:
        """
        冒頭要約（TL;DR）の有無と品質を検出する。
        先頭2000字のみ評価（パフォーマンス優先）。
        fail-open: 検出失敗時は score=0.0 を返す。

        Returns:
            {
                "score": float(0〜5),
                "has_explicit_tldr": bool,      # 「要約」「TL;DR」等の明示ラベルあり
                "has_early_bullets": bool,       # 先頭HTML3000字以内に箇条書きあり
                "lead_paragraph_length": int,    # 冒頭段落の文字数
                "is_optimal_length": bool,       # 50〜150字なら最適
                "advice": str,
            }
        """
        _empty = {
            "score": 0.0, "has_explicit_tldr": False, "has_early_bullets": False,
            "lead_paragraph_length": 0, "is_optimal_length": False,
            "advice": "冒頭に「この記事でわかること」などの要約ブロック（50〜150字）を追加するとAIに引用されやすくなります",
        }
        try:
            body_text = text[:2000]

            # 明示TL;DRラベル検出（先頭500字）
            has_explicit = bool(re.search(
                r"(?:TL;?DR|要約|まとめ(?:ると)?|この記事(?:の|で)?ポイント|わかること)",
                body_text[:500],
                re.IGNORECASE,
            ))

            # 先頭HTML3000字以内に箇条書き（li/ul/ol）があるか
            early_html = str(soup)[:3000]
            has_early_bullets = bool(re.search(r"<(?:ul|ol|li)\b", early_html))

            # 冒頭段落の文字数
            paragraphs = [p for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
            lead_len = len(paragraphs[0].get_text(strip=True)) if paragraphs else 0
            is_optimal = 50 <= lead_len <= 150

            # スコア計算（最大5点）
            score = 0.0
            if has_explicit:
                score += 3.0
            elif has_early_bullets:
                score += 2.0
            if is_optimal:
                score += 2.0
            elif lead_len > 0:
                score += 0.5
            score = min(5.0, score)

            if score < 2.0:
                advice = "冒頭に「この記事でわかること」などの要約ブロック（50〜150字）を追加するとAIに引用されやすくなります"
            elif score < 4.0:
                advice = "冒頭要約はありますが、明示ラベル（例:「この記事のポイント」）を加えるとさらに効果的です"
            else:
                advice = "冒頭要約は最適化されています"

            return {
                "score": round(score, 2),
                "has_explicit_tldr": has_explicit,
                "has_early_bullets": has_early_bullets,
                "lead_paragraph_length": lead_len,
                "is_optimal_length": is_optimal,
                "advice": advice,
            }
        except Exception as e:
            logger.warning("detect_tldr_summary failed: %s", e)
            return _empty

    def calculate_statistics_density(self, text: str) -> dict:
        """
        本文中の統計・数値・引用密度を評価する。
        GEO論文実証: 高密度コンテンツはAI可視性が+30〜40%向上。
        fail-open: 検出失敗時は score=0.0 を返す。

        Returns:
            {
                "score": float(0〜10),
                "stats_count": int,       # 数値/統計表現の総検出数
                "chars_per_stat": float,  # 1統計あたりの文字数（密度指標）
                "has_citations": bool,    # 「出典：」「参考：」等の引用表記あり
                "density_level": str,     # "high" / "medium" / "low"
                "density_per_1k": float,  # 1000字あたりの統計表現数
            }
        """
        _empty = {
            "score": 0.0, "stats_count": 0, "chars_per_stat": 0.0,
            "has_citations": False, "density_level": "low", "density_per_1k": 0.0,
        }
        try:
            total_chars = len(text)
            if total_chars == 0:
                return _empty

            hits: list = []
            for pat in STATISTICS_PATTERNS:
                matches = re.findall(pat, text)
                for m in matches:
                    if isinstance(m, tuple):
                        hits.append("".join(part for part in m if part))
                    else:
                        hits.append(m)

            stats_count = len(hits)
            has_citations = bool(re.search(r"(?:出典|参考文献|引用)\s*[:：]", text))

            density_per_1k = stats_count / (total_chars / 1000)

            if density_per_1k >= 3.0:
                score = 8.0 + min(2.0, (density_per_1k - 3.0) * 0.5)
                level = "high"
            elif density_per_1k >= 1.5:
                score = 5.0 + (density_per_1k - 1.5) * 2.0
                level = "medium"
            elif density_per_1k >= 0.5:
                score = 2.0 + (density_per_1k - 0.5) * 3.0
                level = "low"
            else:
                score = density_per_1k * 4.0
                level = "low"

            if has_citations:
                score = min(10.0, score + 1.0)

            chars_per_stat = round(total_chars / stats_count, 1) if stats_count > 0 else 0.0

            return {
                "score": round(min(10.0, score), 2),
                "stats_count": stats_count,
                "chars_per_stat": chars_per_stat,
                "has_citations": has_citations,
                "density_level": level,
                "density_per_1k": round(density_per_1k, 2),
            }
        except Exception as e:
            logger.warning("calculate_statistics_density failed: %s", e)
            return _empty

    def calculate_entity_salience(self, text: str) -> dict:
        """
        Estimates Entity Salience with Sudachi C-mode.
        Extracts compound nouns as entities and scores them based on frequency and position.
        """
        if not self.tokenizer_obj:
            return {}

        try:
            # Tokenize with Sudachi Mode-C (extracts compound nouns)
            mode_c = self._get_sudachi_tokenizer('C')
            tokens = self.tokenizer_obj.tokenize(text[:10000], mode_c)
            entity_scores = {}
            total_tokens = len(tokens)

            if total_tokens == 0:
                return {}

            for idx, token in enumerate(tokens):
                pos = token.part_of_speech()
                # Extract nouns (compound nouns are automatically combined in Mode-C)
                if pos[0] == '名詞' and pos[1] not in ['代名詞', '非自立可能']:
                    surface = token.surface()

                    # Skip single-character nouns and common particles
                    if len(surface) < 2:
                        continue

                    if surface not in entity_scores:
                        entity_scores[surface] = 0.0

                    # Frequency score
                    entity_scores[surface] += 1.0

                    # Position bonus: entities appearing in the first 10% get higher scores
                    if idx / total_tokens < 0.1:
                        entity_scores[surface] += 2.0

            if not entity_scores:
                return {}

            max_score = max(entity_scores.values())
            return {k: v / max_score for k, v in entity_scores.items()}
        except Exception as e:
            print(f"[ERROR] Entity salience error: {e}")
            return {}

    def _calculate_entity_score(self, entity_results: dict) -> float:
        """
        STRICTER entity score calculation.
        Considers: diversity, distribution, and quality.
        """
        if not entity_results:
            return 0.0
        
        # 1. Diversity: More unique entities = better (max 0.4)
        unique_count = len(entity_results)
        diversity_score = min(unique_count / 15, 0.4)  # 15 unique entities = max
        
        # 2. Top entity prominence (max 0.3)
        top_scores = sorted(entity_results.values(), reverse=True)[:3]
        prominence_score = min(sum(top_scores) / 5, 0.3)  # Needs 5 well-positioned entities
        
        # 3. Distribution: Not too concentrated (max 0.3)
        if len(top_scores) >= 3:
            concentration = top_scores[0] / (sum(top_scores) + 0.01)
            # Lower concentration = better distribution
            distribution_score = (1 - concentration) * 0.3
        else:
            distribution_score = 0.1
        
        return min(diversity_score + prominence_score + distribution_score, 1.0)

    def check_technical_aio(self, base_url: str, response_time_ms: float = None) -> dict:
        """
        Soft technical signals only.
        Provider-specific crawl gates and informational crawler notes are collected separately.
        """
        results = {
            "score": 0.0,
            "llms_txt": False,
            "ai_bots_blocked": False,
            # Google-Extended は Google Search の掲載/ランキングには影響しないため別扱い（情報目的）
            "google_extended_disallowed": False,
            "errors": [],
            "https": False,
            "bot_access": {},
            "robots_status": "unverified",
        }
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            root_url = f"{parsed.scheme}://{parsed.netloc}"
            results["https"] = parsed.scheme.lower() == "https"

            llms_resp = None
            robots_resp = None
            # 2本のHTTP取得は独立しているため並列化して待機時間を短縮
            with ThreadPoolExecutor(max_workers=2) as executor:
                llms_future = executor.submit(
                    safe_fetch_url,
                    f"{root_url}/llms.txt",
                    timeout=config.TIMEOUT_SHORT,
                )
                robots_future = executor.submit(
                    safe_fetch_url,
                    f"{root_url}/robots.txt",
                    timeout=config.TIMEOUT_SHORT,
                )
                try:
                    llms_resp = llms_future.result()
                except Exception as e:
                    results["errors"].append(f"llms.txt fetch failed: {e}")
                    llms_resp = None
                try:
                    robots_resp = robots_future.result()
                except Exception as e:
                    results["errors"].append(f"robots.txt fetch failed: {e}")
                    robots_resp = None

            # 1. llms.txt (informational only)
            if llms_resp is not None and llms_resp.status_code == 200 and len(llms_resp.text.strip()) > 10:
                results["llms_txt"] = True
            elif llms_resp is not None and llms_resp.status_code >= 400:
                results["errors"].append(f"llms.txt HTTP {llms_resp.status_code}")

            # 2. robots.txt for provider gates / informational crawlers
            if robots_resp is not None and robots_resp.status_code == 200:
                content = robots_resp.text
                tracked_agents = list(OFFICIAL_SEARCH_BOTS.values()) + ["google-extended"] + list(INFORMATIONAL_BOTS.keys())
                bot_access = self._parse_robots_agent_access(content, tracked_agents, base_url)
                results["bot_access"] = bot_access
                results["robots_status"] = "pass"
                blocked = [agent for agent in OFFICIAL_SEARCH_BOTS.values() if bot_access.get(agent) is False]
                if blocked:
                    results["ai_bots_blocked"] = True
                    results["blocked_bots"] = blocked
                results["google_extended_disallowed"] = bot_access.get("google-extended") is False
            elif robots_resp is not None:
                # Redirects and every other non-200 response are not evidence
                # that the analysed path is crawlable.
                results["errors"].append(f"robots.txt HTTP {robots_resp.status_code}")

            # 3. HTTPS (0.25)
            if results["https"]:
                results["score"] += 0.25

            # 4. Response Time (0.50)
            if response_time_ms:
                if response_time_ms < 500:
                    results["score"] += 0.50
                elif response_time_ms < 1000:
                    results["score"] += 0.40
                elif response_time_ms < 2000:
                    results["score"] += 0.30
                else:
                    results["score"] += 0.15

            # 5. Baseline (0.25)
            results["score"] += 0.25

        except Exception as e:
            results["errors"].append(f"technical_aio_error: {e}")
            logger.exception("check_technical_aio failed: %s", e)
        
        results["score"] = min(results["score"], 1.0)
        return results

    def _generate_actions(
        self,
        pid: float,
        structure: dict,
        tech: dict,
        provider_readiness: Optional[dict] = None,
        freshness: Optional[dict] = None,
        aeo: Optional[dict] = None,
        citation: Optional[dict] = None,
        entity_linking: Optional[dict] = None,  # Phase 2: カテゴリ情報
        inline_eeat: Optional[dict] = None,     # P02: 文中E-E-A-T
        tldr: Optional[dict] = None,            # P03: TL;DR検出結果
        stats: Optional[dict] = None,           # P03: 統計密度
    ) -> List[dict]:
        actions = []
        freshness = freshness or {}
        aeo = aeo or {}
        citation = citation or {}
        entity_linking = entity_linking or {}
        provider_readiness = provider_readiness or {}
        inline_eeat = inline_eeat or {}
        tldr = tldr or {}
        stats = stats or {}
        actions_by_priority = []

        provider_action_specs = (
            ("google", "■ Google向け公開条件の修正（高優先）", "Googlebot / noindex / snippet 制御を確認し、AI features を阻害する noindex・nosnippet・強い snippet 制限を解除してください。"),
            ("openai_search", "■ OpenAI Search 向けクローラー許可（高優先）", "robots.txt で `OAI-SearchBot` を Disallow しないように設定してください。`GPTBot` は学習用であり、検索用 gate ではありません。"),
            ("perplexity", "■ Perplexity 向けクローラー許可（高優先）", "robots.txt で `PerplexityBot` を Disallow しないように設定してください。"),
            ("claude_search", "■ Claude Search 向けクローラー許可（高優先）", "robots.txt で `Claude-SearchBot` を Disallow しないように設定してください。"),
        )
        for provider_key, action_title, action_method in provider_action_specs:
            provider = provider_readiness.get(provider_key, {}) or {}
            if provider.get("status") == "fail":
                actions_by_priority.append({
                    "action": action_title,
                    "method": action_method,
                    "expected_impact": "High（公式公開条件の解消）",
                })

        # Freshness (prioritize machine-readable dates)
        freshness_score = float(freshness.get("score") or 0)
        freshness_source = str(freshness.get("source") or "")
        if freshness_score < 0.5:
            actions_by_priority.append({
                "action": "■ 更新日の明示（高優先）",
                "method": "更新日をJSON-LDの `dateModified` またはmetaタグで明示してください。本文表示だけだとAIが更新扱いにしにくいです。",
                "expected_impact": "High"
            })
        elif "Text" in freshness_source:
            actions_by_priority.append({
                "action": "▲ 更新日を機械判読に切り替え",
                "method": "本文の日付に加えてJSON-LD/metaにも更新日を記載してください（機械が読み取りやすくなります）。",
                "expected_impact": "Medium"
            })

        # AEO patterns (definitional structure)
        aeo_score = float(aeo.get("score") or 0)
        patterns = aeo.get("patterns", []) or []
        if aeo_score < 0.5 or not patterns:
            actions_by_priority.append({
                "action": "■ 定義文を見出し直下に追加（高優先）",
                "method": "H2/H3直下に「〜とは、〜である」形式の1-2文を置くとAEO/引用適合が上がります。",
                "expected_impact": "High"
            })

        # Citation readiness
        citation_score = float(citation.get("score") or 0)
        if citation_score < 0.5:
            actions_by_priority.append({
                "action": "▲ 結論先出し＋出典の明記",
                "method": "段落冒頭に結論を書き、数値や出典（〜によると/出典）を追記してください。",
                "expected_impact": "Medium"
            })

        # Content-based actions
        if pid < 0.6:
            actions_by_priority.append({
                "action": "▲ 情報の密度を高める",
                "method": "不要な助詞・代名詞を削り、体言止めや箇条書きを活用してPIDスコアを上げてください。",
                "expected_impact": "Medium"
            })

        if structure.get("list_count", 0) < 2:
            actions_by_priority.append({
                "action": "● リスト構造の追加",
                "method": "箇条書き(ul/ol)を増やし、機械可読性を向上させてください。",
                "expected_impact": "Low"
            })

        if not structure.get("has_json_ld"):
            actions_by_priority.append({
                "action": "● 構造化データ(JSON-LD)の補強",
                "method": "JSON-LD は一般公開の公式必須条件ではありませんが、内容理解の補助として有用です。Article / Organization などの追加を検討してください。",
                "expected_impact": "Low（補助シグナル）",
            })

        # llms.txt はコミュニティ仕様であり、SEOランキング要因としては不明確。
        # ただしAIシステムに「案内」を渡す用途としては有用なため、任意の推奨として提示する。
        if not tech.get("llms_txt"):
            actions_by_priority.append({
                "action": "● /llms.txt の設置（任意）",
                "method": "AI向けに重要ページの一覧・要約を示すファイルです。運用ポリシーとして設置する場合は、サイトルート直下に `llms.txt` を配置してください。",
                "expected_impact": "Low（AI向け案内の明確化）"
            })

        # Google-Extended は Google Search の掲載/ランキングに影響しない（公式）。
        # 許可/拒否は「Gemini Apps / Vertex AIの学習・grounding」用途の方針として扱う。
        if tech.get("google_extended_disallowed"):
            actions_by_priority.append({
                "action": "● Google-Extended の扱いを方針として決定（任意）",
                "method": "robots.txt の `User-agent: Google-Extended` は Gemini Apps/Vertex AI の学習・grounding用途を制御します。Google検索順位には影響しません。公開方針に合わせて Allow/Disallow を設定してください。",
                "expected_impact": "Low（方針の明確化）"
            })

        # ===== NEW: E-E-A-T (Author/Organization) Actions =====
        eeat_signals = structure.get("eeat", {})
        if not eeat_signals.get("has_author") and not eeat_signals.get("has_organization"):
            actions_by_priority.append({
                "action": "■ E-E-A-T強化: 著者・組織情報をJSON-LDに追加（高優先）",
                "method": "JSON-LDに `author` (Person) や `publisher` (Organization) を追加してください。例: {\"@type\": \"Article\", \"author\": {\"@type\": \"Person\", \"name\": \"山田太郎\"}} のように記述します。AIはコンテンツの権威性・信頼性を評価するため、著者情報は引用可能性に大きく影響します。",
                "expected_impact": "High（E-E-A-T / AI引用性向上）"
            })
        elif not eeat_signals.get("has_author"):
            actions_by_priority.append({
                "action": "▲ E-E-A-T強化: 著者情報(author)をJSON-LDに追加",
                "method": "記事に著者情報（氏名、プロフィール、SNSリンク等）を追加し、JSON-LDにも `author` を記述してください。",
                "expected_impact": "Medium（E-E-A-T向上）"
            })
        elif not eeat_signals.get("has_organization"):
            actions_by_priority.append({
                "action": "● E-E-A-T強化: 運営組織情報(publisher)をJSON-LDに追加",
                "method": "サイトの運営元組織（会社名、ロゴなど）を `Organization` スキーマで記述してください。",
                "expected_impact": "Low（組織の明示化）"
            })

        # ===== P02: 文中E-E-A-T（日本語対応）アドバイス =====
        # JSON-LDになくてもインライン検出でカバーできている場合は重複アドバイスを抑制する
        inline_eeat_score = inline_eeat.get("combined_score", 0.0)
        for advice_text in inline_eeat.get("advice", []):
            # JSON-LDベースのアクションと重複する場合はスキップ
            if "JSON-LD" in advice_text and structure.get("eeat", {}).get("has_author"):
                continue
            if inline_eeat_score >= 6.0:
                # スコアが十分高ければアドバイス不要
                break
            actions_by_priority.append({
                "action": f"▲ E-E-A-T（文中）: {advice_text}",
                "method": advice_text,
                "expected_impact": "Medium（日本語サイトのAI引用性向上）",
            })

        # ===== P03: GEO基本指標アドバイス =====
        tldr_score = tldr.get("score", 0.0)
        if tldr_score < 4.0:
            actions_by_priority.append({
                "action": f"● GEO: {tldr.get('advice', '冒頭要約を追加してください')}",
                "method": (
                    "GEO研究（ACM SIGKDD 2024）では冒頭50〜150字の要約ブロックが"
                    "AI引用スニペットの直接候補になると実証されています。"
                    "「この記事でわかること」などの明示ラベルを付けると効果的です。"
                ),
                "expected_impact": "Medium（AI引用率向上）",
            })
        stats_score = stats.get("score", 0.0)
        if stats_score < 4.0:
            density_level = stats.get("density_level", "low")
            stats_count = stats.get("stats_count", 0)
            actions_by_priority.append({
                "action": f"● GEO: 数値・統計の密度を高めてください（現在{stats_count}件 / {density_level}）",
                "method": (
                    "統計・数値・引用を含むコンテンツはAI可視性が+30〜40%向上します"
                    "（GEO論文実証値）。"
                    "「〇〇%の利用者が…」「調査によると…」「出典：〇〇」のような"
                    "表現を本文に組み込んでください。"
                ),
                "expected_impact": "Medium（AI可視性+30〜40%）",
            })

        # ===== NEW: Multimodal (Image Alt Quality) Actions =====
        multimodal_signals = structure.get("multimodal", {})
        total_images = multimodal_signals.get("total_images", 0)
        alt_quality_score = multimodal_signals.get("alt_quality_score", 0.0)
        if total_images > 0 and alt_quality_score < 0.5:
            actions_by_priority.append({
                "action": "▲ マルチモーダル対応: 画像のalt属性を改善",
                "method": "画像の `alt` 属性は「ファイル名」ではなく、画像の内容を具体的に説明する文（10文字以上推奨）を設定してください。例: alt=\"2024年の売上推移グラフ\"。AI検索は画像検索との統合が進んでおり、altの品質が引用確率に影響します。",
                "expected_impact": "Medium（AI画像検索対応）"
            })

        # ===== Phase 2: Entity Linking カテゴリ分析に基づくアクション =====
        category_breakdown = entity_linking.get("category_breakdown", {})
        proper_noun_count = entity_linking.get("proper_noun_count", 0)

        # 人名が少ない場合（E-E-A-Tの専門性・権威性に影響）
        person_count = category_breakdown.get("人名", 0) + category_breakdown.get("姓", 0)
        if proper_noun_count > 0 and person_count == 0:
            actions_by_priority.append({
                "action": "▲ 著者・専門家情報の追加",
                "method": "記事に著者名や引用元の専門家名を明記してください。「〜氏によると」「〜教授は述べている」などの形式が効果的です。",
                "expected_impact": "Medium（E-E-A-T向上）"
            })

        # 組織名が少ない場合（権威性に影響）
        org_count = category_breakdown.get("一般", 0)
        if proper_noun_count > 0 and org_count < 2:
            actions_by_priority.append({
                "action": "● 組織・機関名の明記",
                "method": "情報の出典となる組織名（企業、研究機関、政府機関等）を具体的に記載してください。",
                "expected_impact": "Low（権威性向上）"
            })

        # 固有名詞が全体的に少ない場合
        if proper_noun_count < 3:
            actions_by_priority.append({
                "action": "● 具体的な固有名詞の追加",
                "method": "企業名、人名、地名、製品名など具体的な固有名詞を追加し、コンテンツの具体性を高めてください。",
                "expected_impact": "Low（具体性向上）"
            })

        # Phase 4: 表記ゆれに関するアドバイス
        variants_detected = entity_linking.get("variants_detected", [])
        if variants_detected:
            variant_examples = ", ".join([
                f"「{'・'.join(v['variants'][:2])}」→「{v['normalized']}」"
                for v in variants_detected[:2]
            ])
            actions_by_priority.append({
                "action": "● エンティティ表記の統一",
                "method": f"同じ対象に複数の表記が使われています。統一を推奨: {variant_examples}",
                "expected_impact": "Low（一貫性向上）"
            })

        # Wikidata Linking (optional)
        wikidata_info = entity_linking.get("wikidata", {}) or {}
        if wikidata_info.get("enabled") and wikidata_info.get("top_entities"):
            linked_ratio = float(wikidata_info.get("linked_ratio") or 0.0)
            if linked_ratio < 0.5:
                top_terms = ", ".join(wikidata_info.get("top_entities", [])[:3])
                actions_by_priority.append({
                    "action": "● エンティティの明確化（Wikidata/sameAs）",
                    "method": f"主要語句（{top_terms}）の識別が曖昧です。Organization/Personに sameAs としてWikidata URLを追加するか、一般的な名称への言い換えを検討してください。",
                    "expected_impact": "Low（曖昧性の低減）"
                })

        # Deduplicate while preserving order
        seen = set()
        for item in actions_by_priority:
            key = item.get("action")
            if key and key not in seen:
                actions.append(item)
                seen.add(key)

        return actions

    def calculate_citation_readiness(self, text: str) -> dict:
        """
        Enhanced Citation Readiness Index with 6 evaluation axes.
        Evaluates if the text structure is easy for AI to cite.

        Returns:
            dict with score (0.0-1.0) and breakdown of 6 axes:
            - conclusion_first: Paragraphs starting with conclusions
            - data_density: Frequency of numbers with units
            - conciseness: Average sentence length appropriateness
            - source_attribution: Citation and source references
            - fact_opinion_ratio: Ratio of facts vs opinions
            - temporal_clarity: Temporal indicators presence
        """
        if not self.tokenizer_obj:
            return {
                "score": 0.0,
                "conclusion_first": 0.0,
                "data_density": 0.0,
                "conciseness": 0.0,
                "source_attribution": 0.0,
                "fact_opinion_ratio": 0.0,
                "temporal_clarity": 0.0,
                "error": "tokenizer_not_initialized",
            }

        try:
            mode_a = self._get_sudachi_tokenizer('A')
            # Limit text analysis to first 5000 chars for performance
            tokens = self.tokenizer_obj.tokenize(text[:5000], mode_a)

            # Split text into sentences (simple approach using Japanese sentence endings)
            sentences = re.split(r'[。．！!？?]', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return {
                    "score": 0.0,
                    "conclusion_first": 0.0,
                    "data_density": 0.0,
                    "conciseness": 0.0,
                    "source_attribution": 0.0,
                    "fact_opinion_ratio": 0.0,
                    "temporal_clarity": 0.0
                }

            # 1. Conclusion First: Check if sentences start with conclusions or use summary conjunctions
            # Expanded patterns to be more inclusive of polite forms and summary indicators
            conclusion_patterns = re.compile(r'(だ|である|です|ます|でした|ました)$|^(つまり|要するに|結論|まとめると|要約すると)')
            conclusion_count = 0
            check_range = min(len(sentences), 15) # Check first 15 sentences (expanded from 10)
            for sentence in sentences[:check_range]:
                if conclusion_patterns.search(sentence):
                    conclusion_count += 1
            # Relaxed threshold: 3+ conclusions = max (was 5)
            conclusion_first_score = min(conclusion_count / 3, 1.0)

            # 2. Data Density: Numbers + Units (円, %, 人, 年, etc.)
            data_pattern = re.compile(r'\d+\s*[円%人年個件台kg名万億千百十前後以上以下〜~]')
            data_matches = data_pattern.findall(text[:5000])
            # Relaxed threshold: 5+ data points = max (was 10)
            data_density_score = min(len(data_matches) / 5, 1.0)

            # 3. Conciseness: Average sentence length (optimal: 30-100 chars)
            # Widened range to accommodate various writing styles
            total_chars = sum(len(s) for s in sentences)
            avg_sentence_length = total_chars / len(sentences) if sentences else 0

            if 30 <= avg_sentence_length <= 100:
                conciseness_score = 1.0
            elif 20 <= avg_sentence_length < 30 or 100 < avg_sentence_length <= 140:
                conciseness_score = 0.7
            elif 10 <= avg_sentence_length < 20 or 140 < avg_sentence_length <= 200:
                conciseness_score = 0.4
            else:
                conciseness_score = 0.2

            # 4. Source Attribution (引用元・出典の明記度)
            source_patterns = re.compile(r'(によると|によれば|によって|調査|研究|報告|発表|出典|引用|参考|Source|Citation|監修|提供|作成)')
            source_matches = source_patterns.findall(text[:3000])
            # Relaxed threshold: 3+ sources = max (was 5)
            source_attribution_score = min(len(source_matches) / 3, 1.0)

            # 5. Fact vs Opinion Ratio (事実と意見の割合)
            # 事実パターン: 数値、日付、固有名詞、「〜である」
            fact_patterns = re.compile(r'(\d+[年月日％円人個件]|\b(である|でした|とされる|判明|確認|実施|開催|発売)\b)')
            fact_matches = fact_patterns.findall(text[:3000])

            # 意見パターン: 「思う」「考える」「感じる」「べき」「だろう」「かもしれ」
            opinion_patterns = re.compile(r'(思う|思います|考える|考えます|感じ|べき|だろう|かもしれ|たい|ほしい)')
            opinion_matches = opinion_patterns.findall(text[:3000])

            total_statements = len(fact_matches) + len(opinion_matches)
            if total_statements > 0:
                fact_ratio = len(fact_matches) / total_statements
                # Relaxed Ideal ratio: 60-95% facts (was 70-90%)
                if 0.6 <= fact_ratio <= 0.95:
                    fact_opinion_ratio_score = 1.0
                elif 0.4 <= fact_ratio < 0.6 or 0.95 < fact_ratio <= 1.0:
                    fact_opinion_ratio_score = 0.7
                else:
                    fact_opinion_ratio_score = 0.4
            else:
                fact_opinion_ratio_score = 0.6 # Default higher if no clear signals

            # 6. Temporal Clarity (時間的指標の明記)
            temporal_patterns = re.compile(r'(20\d{2}年|\d{4}[./-]\d{1,2}[./-]\d{1,2}|現在|最新|最近|従来|過去|未来|今後|これまで|時点)')
            temporal_matches = temporal_patterns.findall(text[:3000])
            # Relaxed threshold: 2+ markers = max (was 3)
            temporal_clarity_score = min(len(temporal_matches) / 2, 1.0)

            # Enhanced weighted calculation (6 axes)
            # Adjusted weights slightly
            overall_score = (
                conclusion_first_score * 0.20 +
                data_density_score * 0.20 +
                conciseness_score * 0.15 +
                source_attribution_score * 0.15 +
                fact_opinion_ratio_score * 0.15 +
                temporal_clarity_score * 0.15
            )

            # Boost score for short texts or healthy looking texts to avoid erroneously low scores
            if overall_score < 0.3 and avg_sentence_length > 20:
                 overall_score += 0.2

            return {
                "score": min(round(overall_score, 2), 1.0),
                "conclusion_first": round(conclusion_first_score, 2),
                "data_density": round(data_density_score, 2),
                "conciseness": round(conciseness_score, 2),
                "source_attribution": round(source_attribution_score, 2),
                "fact_opinion_ratio": round(fact_opinion_ratio_score, 2),
                "temporal_clarity": round(temporal_clarity_score, 2),
                # Debug info
                "avg_sentence_length": round(avg_sentence_length, 1) if avg_sentence_length else 0,
                "data_point_count": len(data_matches),
                "source_count": len(source_matches),
                "fact_count": len(fact_matches),
                "opinion_count": len(opinion_matches),
                "temporal_marker_count": len(temporal_matches),
                "error": None,
            }
        except Exception as e:
            print(f"[ERROR] Citation readiness calculation error: {e}")
            return {
                "score": 0.0,
                "conclusion_first": 0.0,
                "data_density": 0.0,
                "conciseness": 0.0,
                "source_attribution": 0.0,
                "fact_opinion_ratio": 0.0,
                "temporal_clarity": 0.0,
                "error": str(e),
            }

    def calculate_contextual_freshness(self, soup) -> dict:
        """
        Calculates Contextual Freshness Signal (情報鮮度シグナル).
        Evaluates content freshness from JSON-LD and meta tags.

        Returns:
            dict with:
            - score: 0.0-1.0 (bonus for updates within 6 months)
            - date_modified: Last modification date
            - date_published: Publication date
            - months_since_update: Months since last update
        """
        result = {
            "score": 0.0,
            "date_modified": None,
            "date_published": None,
            "months_since_update": None,
            "source": None,
            "error": None,
            "parse_warnings": [],
        }

        date_modified = None
        date_published = None
        text_date = None

        try:
            # 1. Check JSON-LD for dateModified/datePublished
            json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]

                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        # Extract dateModified
                        if 'dateModified' in item:
                            date_modified = item['dateModified']
                            result["source"] = "JSON-LD (dateModified)"
                            break
                        # Fallback to datePublished
                        if 'datePublished' in item and not date_published:
                            date_published = item['datePublished']

                    if date_modified:
                        break
                except Exception:
                    if len(result["parse_warnings"]) < 3:
                        result["parse_warnings"].append("json_ld_parse_error")
                    continue

            # 2. Check meta tags if JSON-LD not found
            if not date_modified:
                meta_tags = [
                    ('property', 'article:modified_time'),
                    ('property', 'og:updated_time'),
                    ('name', 'last-modified'),
                    ('property', 'article:published_time'),
                    ('name', 'date')
                ]

                for attr_name, attr_value in meta_tags:
                    meta = soup.find('meta', {attr_name: attr_value})
                    if meta and meta.get('content'):
                        if 'modified' in attr_value or 'updated' in attr_value:
                            date_modified = meta.get('content')
                            result["source"] = f"Meta tag ({attr_value})"
                            break
                        elif not date_published:
                            date_published = meta.get('content')

            # 3. Fallback: Parse visible text dates (lower confidence)
            if not date_modified and not date_published:
                text = soup.get_text(separator=' ', strip=True)
                # Common Japanese date formats (YYYY.MM.DD / YYYY/MM/DD / YYYY年MM月DD日)
                text_patterns = [
                    r'\b(20\d{2})[./-](\d{1,2})[./-](\d{1,2})\b',
                    r'(20\d{2})年(\d{1,2})月(\d{1,2})日',
                ]
                candidates = []
                for pattern in text_patterns:
                    for match in re.finditer(pattern, text):
                        try:
                            year = int(match.group(1))
                            month = int(match.group(2))
                            day = int(match.group(3))
                            candidates.append(datetime(year, month, day))
                        except Exception:
                            if len(result["parse_warnings"]) < 3:
                                result["parse_warnings"].append("text_date_parse_error")
                            continue
                if candidates:
                    parsed_date = max(candidates)
                    text_date = parsed_date.strftime('%Y-%m-%d')
                    result["source"] = "Text content (low confidence)"
                    date_published = text_date

            # 3. Parse and calculate freshness score
            target_date = date_modified or date_published
            if target_date:
                # Try to parse ISO 8601 format (YYYY-MM-DD or full datetime)
                try:
                    # Handle various date formats
                    parsed_date = None
                    for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y/%m/%d']:
                        try:
                            # Remove timezone info for simplicity (just keep the date part)
                            date_str = target_date.split('+')[0].split('Z')[0].strip()
                            parsed_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue

                    if parsed_date:
                        now = datetime.now()
                        delta = now - parsed_date
                        months_since = delta.days / 30.44  # Average days per month

                        result["date_modified"] = date_modified
                        result["date_published"] = date_published
                        result["months_since_update"] = round(months_since, 1)

                        # Scoring: Bonus for recent updates
                        if months_since <= 6:
                            result["score"] = 1.0
                        elif months_since <= 12:
                            result["score"] = 0.7
                        elif months_since <= 24:
                            result["score"] = 0.4
                        else:
                            result["score"] = 0.2
                        # Lower confidence if date only found in visible text
                        if text_date and not date_modified:
                            result["score"] = round(result["score"] * 0.6, 2)

                except Exception as e:
                    print(f"[ERROR] Date parsing error: {e}")
                    result["error"] = f"date_parsing_error: {e}"

        except Exception as e:
            print(f"[ERROR] Contextual freshness calculation error: {e}")
            result["error"] = str(e)

        return result

    def analyze_aeo_patterns(self, soup) -> dict:
        """
        Analyzes Answer Engine Optimization patterns (定義文・FAQ構造の検出).
        Enhanced with more patterns and structured data integration.

        Returns:
            dict with:
            - score: 0.0-1.0
            - patterns: List of detected pattern dictionaries
            - faq_count: Number of FAQ items detected
            - definition_quality: Quality score of definitions
        """
        result = {
            "patterns": [],
            "score": 0.0,
            "faq_count": 0,
            "definition_quality": 0.0,
            "confidence": "high",
            "candidates": [],
            "page_hint": None,
            "error": None,
        }

        try:
            # Enhanced definitional patterns (4 → 10 patterns)
            enhanced_patterns = [
                # 既存パターン
                r'(.+)とは[、，]?(.+)(である|です|を指す|のこと)',
                r'(.+)は[、，]?(.+)(のことを指す|を意味する)',
                r'(.+)\s*[=＝]\s*(.+)',
                r'(.+)とは何か[？?]?\s*(.+)',

                # 新規パターン
                r'(.+)の定義は(.+)',
                r'(.+)という(?:の)?は(.+)',
                r'(.+)によって(.+)とされる',
                r'(.+)とも(?:呼ばれ|言われ)(.+)',
                r'(.+)という概念は(.+)',
                r'(.+)の意味は(.+)',
            ]

            # Check paragraphs under h2/h3 headings
            headings = soup.find_all(['h2', 'h3'])
            candidate_pool = []

            # Page-type hint (list-like vs article-like)
            text = soup.get_text(separator=' ', strip=True)
            date_like = re.findall(r'(20\d{2}[./-]\d{1,2}[./-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日)', text)
            list_like = (len(date_like) >= 3) and (len(soup.find_all('li')) >= 5 or len(soup.find_all('tr')) >= 5)
            result["page_hint"] = "list_like" if list_like else "article_like"

            for heading in headings:
                heading_text = heading.get_text(strip=True)

                # Find the next paragraph after this heading
                next_elem = heading.find_next_sibling()
                paragraphs_checked = 0

                while next_elem and paragraphs_checked < 3:
                    if next_elem.name == 'p':
                        para_text = next_elem.get_text(strip=True)
                        if 40 <= len(para_text) <= 220:
                            candidate_pool.append({
                                "heading": heading_text,
                                "definition": para_text[:200],
                            })

                        # Check each pattern
                        for pattern in enhanced_patterns:
                            matches = re.findall(pattern, para_text)
                            if matches:
                                result["patterns"].append({
                                    "heading": heading_text,
                                    "definition": para_text[:200],
                                    "pattern_matched": pattern[:30] + "..."
                                })
                                result["candidates"].append({
                                    "heading": heading_text,
                                    "definition": para_text[:200],
                                    "reason": "定義文が見出し直下にあります"
                                })
                                break

                        paragraphs_checked += 1
                    elif next_elem.name in ['h2', 'h3', 'h4']:
                        # Stop if we hit another heading
                        break

                    next_elem = next_elem.find_next_sibling()

            # Check for FAQPage structured data
            faq_schemas = []
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string or "")
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and item.get("@type") == "FAQPage":
                            faq_schemas.append(item)
                            main_entity = item.get("mainEntity", [])
                            result["faq_count"] += len(main_entity)
                except Exception:
                    continue

            # Bonus score for FAQPage schema
            if faq_schemas:
                result["has_faq_schema"] = True
                result["score"] += min(result["faq_count"] * 0.1, 0.3)  # Max +0.3 bonus

            # Candidate suggestions even without explicit patterns
            if not result["candidates"] and candidate_pool:
                keywords = ["概要", "とは", "FAQ", "Q&A", "よくある質問", "特徴", "目的", "メリット", "使い方", "手順"]
                if result["page_hint"] == "list_like":
                    keywords = keywords + ["お知らせ", "イベント", "更新", "一覧", "ニュース"]
                prioritized = [
                    item for item in candidate_pool
                    if any(k in (item.get("heading") or "") for k in keywords)
                ]
                picks = prioritized[:2] if prioritized else candidate_pool[:2]
                for item in picks:
                    result["candidates"].append({
                        "heading": item.get("heading") or "本文",
                        "definition": item.get("definition") or "",
                        "reason": "この見出し直下に定義文を置くとAIが理解しやすくなります"
                    })

            # Quality scoring for definitions
            if result["patterns"]:
                quality_scores = []
                for pattern_info in result["patterns"]:
                    definition = pattern_info.get("definition", "")
                    quality = 0.0

                    # Length check (20-200 chars is ideal)
                    if 20 <= len(definition) <= 200:
                        quality += 0.4
                    elif 10 <= len(definition) < 20 or 200 < len(definition) <= 300:
                        quality += 0.2

                    # Contains examples or data
                    if re.search(r'例えば|たとえば|具体的には|\d+', definition):
                        quality += 0.3

                    # Contains sources
                    if re.search(r'によると|によれば|出典|引用', definition):
                        quality += 0.3

                    quality_scores.append(quality)

                result["definition_quality"] = round(sum(quality_scores) / len(quality_scores), 2)
                result["score"] = result["definition_quality"]
            else:
                # Lower-confidence fallback: find definition patterns anywhere in text
                body_text = soup.get_text(separator=' ', strip=True)
                for pattern in enhanced_patterns:
                    matches = re.findall(pattern, body_text)
                    if matches:
                        result["patterns"].append({
                            "heading": "本文",
                            "definition": body_text[:200],
                            "pattern_matched": pattern[:30] + "...",
                            "location": "body"
                        })
                        break

                if result["patterns"]:
                    result["confidence"] = "low"
                    quality_scores = []
                    for pattern_info in result["patterns"]:
                        definition = pattern_info.get("definition", "")
                        quality = 0.0
                        if 20 <= len(definition) <= 200:
                            quality += 0.4
                        elif 10 <= len(definition) < 20 or 200 < len(definition) <= 300:
                            quality += 0.2
                        if re.search(r'例えば|たとえば|具体的には|\d+', definition):
                            quality += 0.3
                        if re.search(r'によると|によれば|出典|引用', definition):
                            quality += 0.3
                        quality_scores.append(quality)

                    result["definition_quality"] = round(sum(quality_scores) / len(quality_scores), 2)
                    result["score"] = min(round(result["definition_quality"] * 0.6, 2), 1.0)

        except Exception as e:
            print(f"[ERROR] AEO pattern analysis error: {e}")
            result["error"] = str(e)

        return result

    def calculate_entity_linking(self, text: str) -> dict:
        """
        Performs Knowledge Graph Entity Linking using Sudachi proper noun detection.
        Uses pos[1] == '固有名詞' to identify entities instead of static dictionary.

        Returns:
            dict with:
            - score: 0.0-1.0 (ratio of proper nouns)
            - known_entities: List of proper nouns detected by Sudachi
            - unknown_entities: List of common nouns
            - total_entities: Total count
            - proper_noun_count: Number of proper nouns
            - common_noun_count: Number of common nouns
            - proper_noun_details: Detailed breakdown with category info
            - diagnosis: Quality assessment message
        """
        if not self.tokenizer_obj:
            return {
                "score": 0.0,
                "known_entities": [],
                "unknown_entities": [],
                "total_entities": 0,
                "proper_noun_count": 0,
                "common_noun_count": 0,
                "diagnosis": "トークナイザーが初期化されていません",
                "error": "tokenizer_not_initialized",
            }

        try:
            mode_c = self._get_sudachi_tokenizer('C')
            tokens = self.tokenizer_obj.tokenize(text[:10000], mode_c)

            proper_nouns = []  # 固有名詞
            common_nouns = []  # 普通名詞
            supplementary_matches = []  # Phase 3: 補完辞書マッチ

            for token in tokens:
                pos = token.part_of_speech()
                surface = token.surface()

                if len(surface) < 2:
                    continue

                # Phase 3: 補完辞書チェック（Sudachiより先に）
                if is_supplementary_entity(surface):
                    supplementary_matches.append({
                        "surface": surface,
                        "category": "補完辞書",
                        "normalized": surface
                    })
                    continue

                if pos[0] == '名詞':
                    if pos[1] == '固有名詞':
                        # 固有名詞: Sudachi辞書で判定（人名/地名/組織等）
                        proper_nouns.append({
                            "surface": surface,
                            "category": pos[2] if len(pos) > 2 else "一般",
                            "normalized": token.normalized_form()
                        })
                    elif pos[1] not in ['代名詞', '非自立可能']:
                        common_nouns.append(surface)

            # 重複除去（固有名詞）
            seen = set()
            unique_proper = []
            for item in proper_nouns:
                if item["surface"] not in seen:
                    unique_proper.append(item)
                    seen.add(item["surface"])

            # Phase 3: 重複除去（補完辞書マッチ）
            unique_supplementary = []
            for item in supplementary_matches:
                if item["surface"] not in seen:
                    unique_supplementary.append(item)
                    seen.add(item["surface"])

            # 固有名詞 + 補完辞書マッチを統合
            all_known = unique_proper + unique_supplementary

            # 重複除去（普通名詞）
            unique_common = list(dict.fromkeys(common_nouns))

            # Phase 4: 正規化してグループ化
            entity_groups = group_entities_by_normalized(all_known)
            unique_entity_count = len(entity_groups)

            # Phase 2/3/4: 重み付きスコア計算
            total = unique_entity_count + len(unique_common)
            wikidata_payload = {
                "enabled": False,
                "top_entities": [],
                "linked_entities": [],
                "linked_ratio": 0.0,
                "error": None,
            }
            if total == 0:
                raw_score = 0.0
                weighted_score = 0.0
                diagnosis = "本文から名詞が検出できません"
                category_counts = {}
                variants_detected = []
                final_score = weighted_score
            else:
                # 基本スコア（重み付けなし）
                raw_score = unique_entity_count / total

                # 重み付きスコア計算（グループ単位）
                total_weight = 0.0
                weighted_proper_score = 0.0

                for normalized, info in entity_groups.items():
                    weight = get_category_weight(info["category"])
                    # 出現回数も考慮（最大3回まで）
                    count_factor = min(info["count"], 3) / 3
                    weighted_proper_score += weight * (0.7 + 0.3 * count_factor)
                    total_weight += weight

                # 普通名詞は低重み（0.5）
                common_weight = 0.5
                for _ in unique_common:
                    total_weight += common_weight

                # 重み付きスコア
                if total_weight == 0:
                    weighted_score = 0.0
                else:
                    weighted_score = weighted_proper_score / total_weight

                # カテゴリ別集計（グループ単位）
                category_counts = {}
                for normalized, info in entity_groups.items():
                    cat = info["category"]
                    category_counts[cat] = category_counts.get(cat, 0) + 1

                # Phase 4: 表記ゆれの検出
                variants_detected = []
                for normalized, info in entity_groups.items():
                    if len(info["variants"]) > 1:
                        variants_detected.append({
                            "normalized": normalized,
                            "variants": info["variants"],
                            "suggestion": f"「{info['variants'][0]}」に統一を推奨"
                        })

                # ===== Phase 1: Wikidata QID Linking (Top-K only) =====
                client = self._get_wikidata_client()
                if client and entity_groups:
                    wikidata_payload["enabled"] = True
                    ranked = sorted(
                        [
                            {
                                "normalized": normalized,
                                "count": info.get("count", 0),
                                "category": info.get("category", "一般"),
                            }
                            for normalized, info in entity_groups.items()
                        ],
                        key=lambda item: (item.get("count", 0) * get_category_weight(item.get("category", "一般"))),
                        reverse=True,
                    )
                    top_entities = ranked[: self.wikidata_top_k]
                    wikidata_payload["top_entities"] = [e["normalized"] for e in top_entities if e.get("normalized")]
                    linked = []
                    lookup_errors = []
                    try:
                        for entity in top_entities:
                            term = entity.get("normalized") or ""
                            match = client.search(term)
                            if match:
                                linked.append({
                                    "term": term,
                                    "qid": match.qid,
                                    "label": match.label,
                                    "description": match.description,
                                    "source": match.source,
                                })
                            elif getattr(client, "last_error", None):
                                lookup_errors.append(f"{term}: {client.last_error}")
                    except Exception as e:
                        wikidata_payload["error"] = str(e)
                    if not wikidata_payload.get("error") and lookup_errors:
                        wikidata_payload["error"] = " / ".join(lookup_errors[:2])
                    wikidata_payload["linked_entities"] = linked
                    if top_entities:
                        wikidata_payload["linked_ratio"] = round(len(linked) / len(top_entities), 2)

                # Small bonus from QID linkage to avoid large score shifts
                qid_bonus = 0.0
                if wikidata_payload.get("linked_ratio"):
                    qid_bonus = min(0.05, 0.05 * float(wikidata_payload["linked_ratio"]))
                final_score = min(1.0, weighted_score + qid_bonus)

                # 診断メッセージ
                if weighted_score >= 0.4:
                    diagnosis = "優良（固有名詞が豊富で、表記も統一されています）"
                elif weighted_score >= 0.25:
                    diagnosis = "良好（固有名詞が適切に含まれています）"
                elif weighted_score >= 0.1:
                    diagnosis = "普通（組織名・人名をもう少し増やすと良い）"
                else:
                    diagnosis = "改善推奨（具体的な組織名・人名・地名を追加してください）"

                # 表記ゆれがある場合は診断に追記
                if variants_detected:
                    diagnosis += f"（表記ゆれ{len(variants_detected)}件検出）"

            return {
                "score": round(final_score, 2),
                "raw_score": round(raw_score, 2),  # 重み付けなしスコア
                "known_entities": list(entity_groups.keys())[:20],  # Phase 4: 正規化後のエンティティ
                "unknown_entities": unique_common[:10],
                "total_entities": total,
                "unique_entity_count": unique_entity_count,  # Phase 4: 正規化後のユニーク数
                "total_mentions": sum(g["count"] for g in entity_groups.values()),  # Phase 4: 総出現回数
                "proper_noun_count": len(unique_proper),
                "common_noun_count": len(unique_common),
                "supplementary_count": len(unique_supplementary),
                "supplementary_matches": [s["surface"] for s in unique_supplementary],
                "entity_groups": {k: v for k, v in list(entity_groups.items())[:10]},  # Phase 4: グループ情報
                "variants_detected": variants_detected[:5],  # Phase 4: 表記ゆれ警告
                "category_breakdown": category_counts,
                "diagnosis": diagnosis,
                "wikidata": wikidata_payload,
                "error": None,
            }

        except Exception as e:
            print(f"[ERROR] Entity linking error: {e}")
            return {
                "score": 0.0,
                "known_entities": [],
                "unknown_entities": [],
                "total_entities": 0,
                "proper_noun_count": 0,
                "common_noun_count": 0,
                "diagnosis": f"エラー: {str(e)}",
                "error": str(e),
            }
