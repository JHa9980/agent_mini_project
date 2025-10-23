"""LangGraph node for the MetricScorer agent."""

from __future__ import annotations

from statistics import mean
from typing import Dict, List

from state import (
    AnalysisPlan,
    DiagnosticTag,
    FeedbackAction,
    MetricDashboard,
    MetricEntry,
    TrendState,
)

MIN_CONFIDENCE = 0.6
MIN_ITEMS_PER_SEGMENT = 2
LOW_CONFIDENCE_THRESHOLD = 0.5

RESEARCH_DIVISOR = 0.8  # 0~100 → 0~20
RESEARCH_MAX = 20.0
MARKET_DIVISOR = 10.0  # 0~100 → 0~10
MARKET_MAX = 10.0
DEPLOYMENT_DIVISOR = 10.0  # 0~100 → 0~10
DEPLOYMENT_MAX = 10.0


def metric_scorer_node(state: TrendState) -> TrendState:
    plan = state.get("analysis_plan")
    if plan is None:
        return {}

    dashboard = MetricDashboard()
    dashboard["research_activity"] = _score_research_activity(plan, state)
    dashboard["market_reaction"] = _score_market_reaction(plan, state)
    dashboard["deployment_readiness"] = _score_deployment(plan, state)

    diagnostics = []
    diagnostics.extend(_diagnose_segment_coverage(plan, state))
    diagnostics.extend(_diagnose_confidence(plan, state))

    feedback_actions = _route_feedback(diagnostics)

    return {
        "metric_dashboard": dashboard,
        "diagnostics": diagnostics,
        "pending_feedback": feedback_actions,
    }


def _score_research_activity(plan: AnalysisPlan, state: TrendState) -> MetricEntry:
    scores: Dict[str, float] = {}
    for segment in plan["segments"]:
        name = segment["name"]
        papers = [
            item.get("signals", {}).get("papers", 0.0)
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        patents = [
            item.get("signals", {}).get("patents", 0.0)
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        if not papers and not patents:
            continue
        score = 0.0
        if papers:
            score += 0.6 * mean(papers)
        if patents:
            score += 0.4 * mean(patents)
        score = min(RESEARCH_MAX, score / RESEARCH_DIVISOR)
        scores[name] = round(score, 2)
    return {
        "segment_scores": scores,
        "description": "논문·특허 활동량을 반영한 연구 활동 지수",
        "unit": "지수 (0~20)",
    }


def _score_market_reaction(plan: AnalysisPlan, state: TrendState) -> MetricEntry:
    scores: Dict[str, float] = {}
    for segment in plan["segments"]:
        name = segment["name"]
        investments = [
            item.get("signals", {}).get("investments", 0.0)
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        searches = [
            item.get("signals", {}).get("search_index", 0.0)
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        if not investments and not searches:
            continue
        score = 0.0
        if investments:
            score += 0.7 * mean(investments)
        if searches:
            score += 0.3 * mean(searches)
        score = min(MARKET_MAX, score / MARKET_DIVISOR)
        scores[name] = round(score, 2)
    return {
        "segment_scores": scores,
        "description": "투자·검색 반응을 통합한 시장 모멘텀 지수",
        "unit": "지수 (0~10)",
    }


def _score_deployment(plan: AnalysisPlan, state: TrendState) -> MetricEntry:
    scores: Dict[str, float] = {}
    for segment in plan["segments"]:
        name = segment["name"]
        deployments = [
            item.get("signals", {}).get("deployments", 0.0)
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        latency = [
            item.get("signals", {}).get("latency", 0.0)
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        if not deployments and not latency:
            continue
        score = 0.0
        if deployments:
            score += 0.5 * mean(deployments)
        if latency:
            score += 0.5 * (100 - mean(latency))
        score = min(DEPLOYMENT_MAX, score / DEPLOYMENT_DIVISOR)
        scores[name] = round(score, 2)
    return {
        "segment_scores": scores,
        "description": "사업화 사례와 지연시간을 기반으로 한 배포 준비도 지수",
        "unit": "지수 (0~10)",
    }


def _diagnose_segment_coverage(plan: AnalysisPlan, state: TrendState) -> List[DiagnosticTag]:
    observed_segments = {
        item.get("segment")
        for item in state.get("evidence_pool", [])
        if item.get("confidence", 0.0) >= MIN_CONFIDENCE
    }
    expected_segments = {segment["name"] for segment in plan["segments"]}
    missing = expected_segments - observed_segments

    diagnostics: List[DiagnosticTag] = []
    for name in sorted(missing):
        diagnostics.append(
            {
                "metric": "segment_coverage",
                "issue": f"세그먼트 '{name}'에서 근거 신뢰 지수 높은 증거가 확보되지 않음",
                "severity": "high",
                "cause": "coverage-gap",
                "target": "InfoCollector",
                "detail": {"segment": name},
            }
        )
    return diagnostics


def _diagnose_confidence(plan: AnalysisPlan, state: TrendState) -> List[DiagnosticTag]:
    diagnostics: List[DiagnosticTag] = []
    for segment in plan["segments"]:
        name = segment["name"]
        items = [
            item
            for item in state.get("evidence_pool", [])
            if item.get("segment") == name
        ]
        if not items:
            continue

        avg_confidence = mean(item.get("confidence", 0.0) for item in items)
        if avg_confidence < LOW_CONFIDENCE_THRESHOLD:
            diagnostics.append(
                {
                    "metric": "evidence_confidence",
                    "issue": f"'{name}' 평균 근거 신뢰 지수 {avg_confidence:.2f}",
                    "severity": "medium",
                    "cause": "low-confidence",
                    "target": "InfoCollector",
                    "detail": {
                        "segment": name,
                        "average_confidence": round(avg_confidence, 2),
                    },
                }
            )

        if len(items) < MIN_ITEMS_PER_SEGMENT:
            diagnostics.append(
                {
                    "metric": "evidence_depth",
                    "issue": f"'{name}' 증거 개수 {len(items)}개",
                    "severity": "medium",
                    "cause": "low-volume",
                    "target": "InfoCollector",
                    "detail": {
                        "segment": name,
                        "observed_items": len(items),
                        "required_items": MIN_ITEMS_PER_SEGMENT,
                    },
                }
            )
    return diagnostics


def _route_feedback(diagnostics: List[DiagnosticTag]) -> List[FeedbackAction]:
    actions: List[FeedbackAction] = []
    for tag in diagnostics:
        segment = tag.get("detail", {}).get("segment")
        if segment is None:
            continue
        actions.append(
            {
                "route": "InfoCollector",
                "message": f"[InfoCollector] '{segment}' 세그먼트 증거를 보강하세요.",
                "payload": {
                    "segment": segment,
                    "minimum_items": MIN_ITEMS_PER_SEGMENT,
                    "hints": [
                        "산업별 전문 매체나 협회 보고서를 우선 탐색하세요.",
                        "최근 12개월 이내 발표 자료를 추가 확보하세요.",
                        "투자·거래 관련 키워드를 확장해 보세요.",
                    ],
                    "confidence_boost": 0.2,
                },
            }
        )
    return actions
