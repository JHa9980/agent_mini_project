"""Quick check for the FeedbackHandler loop."""

from pathlib import Path
from pprint import pprint
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.feedback_handler import feedback_handler_node  # type: ignore  # noqa: E402
from agents.metric_scorer import metric_scorer_node  # type: ignore  # noqa: E402
from agents.info_collector import info_collector_node  # type: ignore  # noqa: E402
from prompts import USER_ANALYSIS_PLAN  # type: ignore  # noqa: E402


def run() -> None:
    state = {"analysis_plan": USER_ANALYSIS_PLAN, "feedback_iterations": 0}
    state.update(info_collector_node(state))
    state.update(metric_scorer_node(state))
    state = feedback_handler_node(state)
    print(f"Feedback iterations: {state.get('feedback_iterations')}")
    print(f"Pending feedback: {state.get('pending_feedback')}")
    pprint(state.get("evidence_pool"))


if __name__ == "__main__":
    run()
