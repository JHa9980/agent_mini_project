"""LangGraph implementation for the Edge AI Trend Lab pipeline (Sequential Generation)."""

from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from agents import (
    feedback_handler_node,
    info_collector_node,
    insight_mapper_node,
    metric_scorer_node,
    scenario_planner_node,
)
from agents.report_assembler import report_assembler_node, save_report_to_file
from prompts import USER_ANALYSIS_PLAN
from state import TrendState

MAX_FEEDBACK_ITERATIONS = 4

# The list of sections to be generated for the report.
REPORT_SECTIONS = [
    "summary",
    "introduction",
    "global_overview",
    "trend_insights",
    "five_year_scenarios",
    "risk_opportunity",
    "strategy_recommendations",
    "references_text",
    "appendix_text",
]


def build_graph() -> StateGraph:
    """Builds the LangGraph for sequential report generation."""
    graph = StateGraph(TrendState)

    # Add nodes for the main analysis pipeline
    graph.add_node("info_collector", info_collector_node)
    graph.add_node("insight_mapper", insight_mapper_node)
    graph.add_node("metric_scorer", metric_scorer_node)
    graph.add_node("feedback_handler", feedback_handler_node)
    graph.add_node("scenario_planner", scenario_planner_node)

    # Add nodes for the new sequential report generation process
    graph.add_node("report_planner", report_planner_node)
    graph.add_node("generate_section", report_assembler_node)
    graph.add_node("set_next_section", set_next_section_node)  # New node
    graph.add_node("finalize_report", save_report_to_file)

    # Define the graph edges
    graph.add_edge(START, "info_collector")
    graph.add_edge("info_collector", "insight_mapper")
    graph.add_edge("insight_mapper", "metric_scorer")

    graph.add_conditional_edges(
        "metric_scorer",
        _route_after_metrics,
        {"feedback": "feedback_handler", "scenario": "scenario_planner"},
    )

    graph.add_edge("feedback_handler", "insight_mapper")
    graph.add_edge("scenario_planner", "report_planner")
    graph.add_edge("report_planner", "generate_section")

    # Add the main loop for generating sections
    graph.add_conditional_edges(
        "generate_section",
        _decide_to_continue_generation,
        {"continue": "set_next_section", "finalize": "finalize_report"},
    )
    graph.add_edge("set_next_section", "generate_section") # Loop back

    graph.add_edge("finalize_report", END)

    return graph


def report_planner_node(state: TrendState) -> Dict[str, Any]:
    """Initializes the list of sections and the first section to generate."""
    return {
        "report_sections": REPORT_SECTIONS,
        "generated_report": {},
        "current_section": REPORT_SECTIONS[0],
    }


def set_next_section_node(state: TrendState) -> Dict[str, str]:
    """Sets the next section to be generated in the state."""
    generated_sections = state.get("generated_report", {}).keys()
    all_sections = state.get("report_sections", [])
    next_section_index = len(generated_sections)
    next_section = all_sections[next_section_index]
    return {"current_section": next_section}


def _route_after_metrics(state: TrendState) -> str:
    """Routes to feedback or scenario planning based on metrics."""
    has_feedback = bool(state.get("pending_feedback"))
    iteration_cap = state.get("feedback_iterations", 0) >= MAX_FEEDBACK_ITERATIONS
    if has_feedback and not iteration_cap:
        return "feedback"
    return "scenario"


def _decide_to_continue_generation(state: TrendState) -> str:
    """Decides whether to continue the report generation loop."""
    generated_sections = state.get("generated_report", {}).keys()
    all_sections = state.get("report_sections", [])

    if len(generated_sections) < len(all_sections):
        return "continue"
    else:
        return "finalize"


def run_demo() -> Dict:
    """Runs the full report generation pipeline."""
    graph = build_graph().compile()
    initial_state: TrendState = {
        "analysis_plan": USER_ANALYSIS_PLAN,
        "feedback_iterations": 0,
    }
    # The recursion_limit is increased to handle the loop.
    config = {"recursion_limit": 50}
    
    # Use stream to observe the state changes, and get the final state
    final_state = {}
    for step in graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = step

    return final_state


if __name__ == "__main__":
    final_state = run_demo()
    report_path = final_state.get("report_path")
    print(f"\n--- Report Generation Complete ---")
    print(f"Report saved to: {report_path or '생성되지 않음'}")
    report_error = final_state.get("report_error")
    if report_error:
        print(f"Report fallback note: {report_error}")

    print("\n=== Final Report (excerpt) ===")
    report = final_state.get("final_report", "")
    lines = report.splitlines()
    print("\n".join(lines[:15]))
    if len(lines) > 15:
        print("... (truncated)")
