"""Scenario planner node with LLM-based narrative generation."""

from __future__ import annotations

import json
from datetime import datetime
from statistics import mean
from typing import Dict, List, Optional

from config import get_llm
from prompts import SCENARIO_PLANNER_PROMPT
from state import MetricEntry, TrendState

BASE_GROWTH = 12.0
DEFAULT_ASSUMPTIONS = [
    "연구·특허 신호는 약 18개월 선행 지표로 작용한다.",
    "정책 및 규제 변화는 주요 세그먼트에 동일하게 적용된다.",
    "저지연 엣지 인프라 투자가 지속 확대된다는 가정 하에 분석한다.",
]


def scenario_planner_node(state: TrendState) -> TrendState:
    dashboard = state.get("metric_dashboard")
    if not dashboard:
        return {}

    profile = _aggregate_profiles(dashboard)
    numeric = {
        "보수": _build_scenario(profile, 0.6),
        "중립": _build_scenario(profile, 1.0),
        "가속": _build_scenario(profile, 1.4),
    }

    assumptions = state.get("scenario_outlook", {}).get("assumptions", DEFAULT_ASSUMPTIONS)

    narrative = _generate_scenario_narrative(
        horizon="5년",
        numeric_scenarios=numeric,
        assumptions=assumptions,
    )

    outlook_assumptions = narrative.get("assumptions", assumptions) if narrative else assumptions

    result: Dict[str, object] = {
        "scenario_outlook": {
            "horizon": "5년",
            "scenarios": numeric,
            "assumptions": outlook_assumptions,
        }
    }

    if narrative:
        result["scenario_analysis"] = narrative

    return result


def _aggregate_profiles(dashboard: Dict[str, MetricEntry]) -> Dict[str, float]:
    profile: Dict[str, List[float]] = {}
    for metric in dashboard.values():
        for segment, score in metric["segment_scores"].items():
            profile.setdefault(segment, []).append(score)
    return {segment: mean(scores) for segment, scores in profile.items()}


def _build_scenario(profile: Dict[str, float], multiplier: float) -> Dict[str, float]:
    scenario: Dict[str, float] = {}
    for segment, score in profile.items():
        projected = BASE_GROWTH + multiplier * (score / 10.0)
        scenario[segment] = round(projected, 1)
    if scenario:
        scenario["overall_cagr"] = round(mean(scenario.values()), 1)
    else:
        scenario["overall_cagr"] = BASE_GROWTH
    return scenario


def _generate_scenario_narrative(
    horizon: str,
    numeric_scenarios: Dict[str, Dict[str, float]],
    assumptions: List[str],
) -> Optional[Dict[str, object]]:
    payload = {
        "horizon": horizon,
        "numeric_scenarios": numeric_scenarios,
        "assumptions": assumptions,
        "summary_points": [],
    }

    try:
        messages = [
            {"role": "system", "content": SCENARIO_PLANNER_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
        response = get_llm().invoke(messages)
        content = response.content if hasattr(response, "content") else response
        return json.loads(content)
    except Exception:
        current_year = datetime.now().year
        period = f"{current_year + 1}~{current_year + 5}"
        return {
            "summary": f"{period} 5년 동안 세 시나리오는 엣지 인프라 투자 확대라는 공통 축을 공유하지만, 공급망 안정화 속도와 지역 정책 인센티브에 따라 성장 궤적이 달라집니다.",
            "conservative": f"보수 시나리오에서는 {period} 동안 산업 게이트웨이와 온디바이스 분야가 유지보수·생산성 향상 프로젝트에 집중하며 CAGR이 15% 내외로 제한되고, 통신 인프라 투자는 규제 대응에 머뭅니다.",
            "neutral": f"중립 시나리오에서는 {period} 중반부부터 공장 자동화와 차량 엣지가 동시에 확장되며 CAGR이 16%대까지 올라가고, MEC 구축과 파트너 생태계가 균형 있게 성장합니다.",
            "accelerated": f"가속 시나리오에서는 {period} 전 기간 동안 정부 인센티브와 배터리 혁신이 맞물리면서 산업 게이트웨이가 17% 이상, 차량 엣지가 18% 이상 성장해 Edge AI가 핵심 운영 플랫폼으로 자리잡습니다.",
            "assumptions": assumptions,
            "key_drivers": ["엣지 인프라 투자", "정책 인센티브", "에너지 효율성"],
        }
