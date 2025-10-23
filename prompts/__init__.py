"""Prompt constants for the Edge AI Trend Lab project."""

from .info_collector import INFO_COLLECTOR_PROMPT
from .insight_mapper import INSIGHT_MAPPER_PROMPT
from .metric_scorer import METRIC_SCORER_PROMPT
from .scenario_planner import SCENARIO_PLANNER_PROMPT
from .report_assembler import SINGLE_SECTION_PROMPT
from .user_plan import USER_ANALYSIS_PLAN

__all__ = [
    "INFO_COLLECTOR_PROMPT",
    "INSIGHT_MAPPER_PROMPT",
    "METRIC_SCORER_PROMPT",
    "SCENARIO_PLANNER_PROMPT",
    "SINGLE_SECTION_PROMPT",
    "USER_ANALYSIS_PLAN",
]
