"""LangGraph node for the InsightMapper agent powered by OpenAI."""

from __future__ import annotations

import json
from statistics import mean
from typing import Dict, List

from config import get_llm
from prompts import INSIGHT_MAPPER_PROMPT
from state import EvidenceItem, TrendInsight, TrendState


def insight_mapper_node(state: TrendState) -> TrendState:
    plan = state.get("analysis_plan")
    if plan is None:
        return {}

    llm = get_llm()
    evidence_pool = state.get("evidence_pool", [])
    insights: List[TrendInsight] = []
    evidence_by_segment: Dict[str, List[EvidenceItem]] = {}

    for item in evidence_pool:
        segment = item.get("segment")
        if not segment:
            continue
        evidence_by_segment.setdefault(segment, []).append(item)

    for segment in plan["segments"]:
        segment_name = segment["name"]
        items = evidence_by_segment.get(segment_name, [])
        if not items:
            continue

        insight = _generate_insight_with_llm(llm, segment_name, items)
        if not insight:
            insight = _fallback_insight(segment_name, items)
        insights.append(insight)

    return {"trend_insights": insights}


def _generate_insight_with_llm(llm, segment: str, items: List[EvidenceItem]) -> TrendInsight | None:
    payload = {
        "segment": segment,
        "evidence": [
            {
                "summary": item.get("summary", ""),
                "signals": item.get("signals", {}),
                "confidence": item.get("confidence", 0.0),
                "source": item.get("source", "Unknown"),
            }
            for item in items
        ],
    }

    messages = [
        {"role": "system", "content": INSIGHT_MAPPER_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else response
        data = json.loads(content)
        return TrendInsight(
            segment=data["segment"],
            summary=data["summary"],
            leading_indicators=data["leading_indicators"],
            supporting_sources=data["supporting_sources"],
            confidence=float(data["confidence"]),
        )
    except Exception:
        return None


def _fallback_insight(segment: str, items: List[EvidenceItem]) -> TrendInsight:
    avg_papers = mean(item.get("signals", {}).get("papers", 0.0) for item in items)
    avg_investments = mean(item.get("signals", {}).get("investments", 0.0) for item in items)
    summary = (
        f"{segment} 세그먼트는 월평균 논문 {avg_papers:.1f}편, 투자 {avg_investments:.1f}M 수준으로 "
        "기술 확산이 이어지고 있습니다."
    )

    leading_indicators = []
    if any(item.get("signals", {}).get("search_index", 0.0) > 70 for item in items):
        leading_indicators.append("검색 관심 증가")
    if any(item.get("signals", {}).get("investments", 0.0) > 150 for item in items):
        leading_indicators.append("대규모 투자 유입")
    if any(item.get("signals", {}).get("patents", 0.0) > 8 for item in items):
        leading_indicators.append("특허 활동 강화")
    if any(item.get("signals", {}).get("deployments", 0.0) > 40 for item in items):
        leading_indicators.append("배포 사례 확대")
    if not leading_indicators:
        leading_indicators = ["추가 데이터 필요"]

    top_sources = [
        item.get("source", "Unknown")
        for item in sorted(items, key=lambda x: x.get("confidence", 0.0), reverse=True)[:3]
    ]
    avg_confidence = mean(item.get("confidence", 0.0) for item in items)

    return TrendInsight(
        segment=segment,
        summary=summary,
        leading_indicators=leading_indicators,
        supporting_sources=top_sources,
        confidence=round(avg_confidence, 2),
    )
