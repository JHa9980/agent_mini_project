"""State definitions for the Edge AI Trend Lab LangGraph pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


class SegmentPlan(TypedDict):
    name: str
    keywords: List[str]
    sources: List[str]
    priority: int


class AnalysisPlan(TypedDict):
    segments: List[SegmentPlan]
    time_window: str
    scenario_targets: Dict[str, Any]


class EvidenceSignals(TypedDict, total=False):
    papers: float
    patents: float
    investments: float
    search_index: float
    deployments: float
    latency: float


class EvidenceItem(TypedDict, total=False):
    segment: str
    source: str
    published_date: str
    confidence: float
    summary: str
    signals: EvidenceSignals
    metadata: Dict[str, Any]


class TrendInsight(TypedDict):
    segment: str
    summary: str
    leading_indicators: List[str]
    supporting_sources: List[str]
    confidence: float


class MetricEntry(TypedDict):
    segment_scores: Dict[str, float]
    description: str
    unit: str


class MetricDashboard(TypedDict, total=False):
    research_activity: MetricEntry
    market_reaction: MetricEntry
    deployment_readiness: MetricEntry


class ScenarioData(TypedDict):
    overall_cagr: float


class ScenarioOutlook(TypedDict):
    horizon: str
    scenarios: Dict[str, Dict[str, float]]
    assumptions: List[str]


class DiagnosticTag(TypedDict):
    metric: str
    issue: str
    severity: Literal["low", "medium", "high"]
    cause: str
    target: Literal["InfoCollector"]
    detail: Dict[str, Any]


class FeedbackAction(TypedDict, total=False):
    route: Literal["InfoCollector"]
    message: str
    payload: Dict[str, Any]


class TrendState(TypedDict, total=False):
    analysis_plan: AnalysisPlan
    evidence_pool: List[EvidenceItem]
    trend_insights: List[TrendInsight]
    metric_dashboard: MetricDashboard
    scenario_outlook: ScenarioOutlook
    final_report: str
    diagnostics: List[DiagnosticTag]
    pending_feedback: List[FeedbackAction]
    feedback_iterations: int
    report_path: str
    report_error: str
    scenario_analysis: Dict[str, Any]

    # Fields for sequential report generation
    report_sections: List[str]
    current_section: str
    generated_report: Dict[str, str]
