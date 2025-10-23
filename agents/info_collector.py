"""LangGraph node for the InfoCollector agent using Tavily search."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Tuple

from config import get_tavily_tool
from state import EvidenceItem, FeedbackAction, TrendState


def info_collector_node(state: TrendState) -> TrendState:
    plan = state.get("analysis_plan")
    if plan is None:
        return {}

    tavily = get_tavily_tool()
    evidence_pool = deepcopy(state.get("evidence_pool", []))
    pending_feedback = state.get("pending_feedback", [])
    remaining_feedback: List[FeedbackAction] = []

    for action in pending_feedback:
        if action.get("route") != "InfoCollector":
            remaining_feedback.append(action)
            continue
        payload = action.get("payload", {})
        segment_name = payload.get("segment")
        if not segment_name:
            continue
        evidence_pool.extend(
            _fetch_segment_evidence(
                segment_name,
                plan["segments"],
                tavily,
                hints=payload.get("hints", []),
                confidence_boost=payload.get("confidence_boost", 0.2),
                minimum_items=payload.get("minimum_items", 3),
            )
        )

    counts: Dict[str, int] = {}
    for item in evidence_pool:
        name = item.get("segment")
        if name:
            counts[name] = counts.get(name, 0) + 1

    for segment in plan["segments"]:
        name = segment["name"]
        current = counts.get(name, 0)
        if current < 2:
            evidence_pool.extend(
                _fetch_segment_evidence(
                    name,
                    plan["segments"],
                    tavily,
                    minimum_items=2 - current,
                )
            )

    return {
        "evidence_pool": evidence_pool,
        "pending_feedback": remaining_feedback,
    }


def _fetch_segment_evidence(
    segment_name: str,
    segments: List[Dict[str, object]],
    tavily,
    hints: List[str] | None = None,
    confidence_boost: float = 0.0,
    minimum_items: int = 2,
) -> List[EvidenceItem]:
    segment_plan = next((seg for seg in segments if seg["name"] == segment_name), None)
    if not segment_plan:
        return []

    # --- Start of Enhanced Query Generation ---
    base_keywords = list(segment_plan.get("keywords", []))
    if hints:
        base_keywords.extend(hints)

    # Create a set of enhanced, forward-looking queries
    future_terms = ["forecast", "outlook", "trends", "roadmap", "future", "prospects", "2030"]
    queries = {f'"{key}" {term}' for key in base_keywords for term in future_terms}
    # Add queries for credible roadmaps
    queries.update({f'"credible source" "{key}" roadmap' for key in base_keywords})
    # Add base keywords as queries as well
    queries.update({f'"{key}"' for key in base_keywords})

    if not queries:
        queries = {segment_name}
    # --- End of Enhanced Query Generation ---

    evidence: List[EvidenceItem] = []
    processed_urls = set()

    for query in sorted(list(queries)):
        if len(evidence) >= minimum_items + 5: # Stop if we have enough evidence (target ~7)
            break
        try:
            results = tavily.invoke({"query": query})
        except Exception as exc:
            print(f"Tavily search failed for query '{query}': {exc}")
            continue # Try next query

        raw_results = results.get("results", [])
        for idx, item in enumerate(raw_results):
            url = item.get("url")
            if url and url in processed_urls:
                continue # Skip duplicate content
            if url:
                processed_urls.add(url)

            summary = item.get("snippet") or item.get("content") or ""
            signals, conf_adj = _estimate_signals(summary)
            evidence.append(
                {
                    "segment": segment_name,
                    "source": item.get("source") or item.get("url") or "Unknown",
                    "published_date": item.get("published_date") or "",
                    "confidence": min(
                        0.95, (item.get("score") or 0.6) + confidence_boost + conf_adj
                    ),
                    "summary": summary or f"{segment_name} 관련 Tavily 검색 결과 요약",
                    "signals": signals,
                    "metadata": {
                        "title": item.get("title"),
                        "url": url,
                        "query": query,
                        "tavily_score": item.get("score"),
                        "rank": idx + 1,
                    },
                }
            )

    if not evidence:
        evidence.append(
            {
                "segment": segment_name,
                "source": "TavilyNoResult",
                "published_date": "",
                "confidence": min(0.5 + confidence_boost, 0.85),
                "summary": f"{segment_name} 관련 Tavily 검색 결과가 부족해 기본 신호를 사용합니다.",
                "signals": _default_signals(segment_name),
                "metadata": {"query": ", ".join(queries), "results": 0},
            }
        )
    return evidence


def _estimate_signals(summary: str) -> Tuple[Dict[str, float], float]:
    summary_lower = summary.lower()
    signals = {
        "papers": 10.0,
        "patents": 4.0,
        "investments": 60.0,
        "search_index": 55.0,
        "deployments": 25.0,
        "latency": 26.0,
    }
    confidence_adj = 0.0

    if "research" in summary_lower or "논문" in summary_lower:
        signals["papers"] += 12
        confidence_adj += 0.05
    if "patent" in summary_lower or "특허" in summary_lower:
        signals["patents"] += 9
        confidence_adj += 0.05
    if "investment" in summary_lower or "funding" in summary_lower or "투자" in summary_lower or "$" in summary_lower:
        signals["investments"] += 70
        confidence_adj += 0.1
    if "deployment" in summary_lower or "rollout" in summary_lower or "도입" in summary_lower or "출시" in summary_lower:
        signals["deployments"] += 35
        confidence_adj += 0.05
    if "latency" in summary_lower or "지연" in summary_lower or "response time" in summary_lower:
        signals["latency"] = max(10.0, signals["latency"] - 10)
    if "market" in summary_lower or "trend" in summary_lower or "시장" in summary_lower:
        signals["search_index"] += 25
        confidence_adj += 0.05

    return signals, confidence_adj


def _default_signals(segment: str) -> Dict[str, float]:
    base = {
        "papers": 12.0,
        "patents": 5.0,
        "investments": 80.0,
        "search_index": 60.0,
        "deployments": 30.0,
        "latency": 25.0,
    }
    if "온디바이스" in segment:
        base.update({"deployments": 50.0, "latency": 20.0})
    if "차량" in segment:
        base.update({"investments": 150.0, "deployments": 35.0})
    if "통신" in segment:
        base.update({"search_index": 70.0})
    return base
