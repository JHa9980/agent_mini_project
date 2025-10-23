"""LangGraph node handling feedback loops between MetricScorer and upstream agents."""

from __future__ import annotations

from copy import deepcopy

from state import TrendState

from .info_collector import info_collector_node


MAX_FEEDBACK_ITERATIONS = 4


def feedback_handler_node(state: TrendState) -> TrendState:
    if not state.get("pending_feedback"):
        return {"feedback_iterations": state.get("feedback_iterations", 0)}

    iterations = state.get("feedback_iterations", 0) + 1
    if iterations > MAX_FEEDBACK_ITERATIONS:
        return {
            "pending_feedback": [],
            "feedback_iterations": iterations,
        }

    working_state = deepcopy(state)
    info_updates = info_collector_node(working_state)
    working_state.update(info_updates)

    return {
        "analysis_plan": working_state.get("analysis_plan"),
        "evidence_pool": working_state.get("evidence_pool"),
        "pending_feedback": working_state.get("pending_feedback", []),
        "feedback_iterations": iterations,
    }
