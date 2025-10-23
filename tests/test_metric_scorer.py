"""Quick check for the MetricScorer node."""

from pathlib import Path
from pprint import pprint
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.info_collector import info_collector_node  # type: ignore  # noqa: E402
from agents.metric_scorer import metric_scorer_node  # type: ignore  # noqa: E402
from prompts import USER_ANALYSIS_PLAN  # type: ignore  # noqa: E402


def run() -> None:
    state = {"analysis_plan": USER_ANALYSIS_PLAN}
    state.update(info_collector_node(state))
    updated = metric_scorer_node(state)
    pprint(updated.get("metric_dashboard"))
    print("Diagnostics:")
    for diag in updated.get("diagnostics", []):
        pprint(diag)


if __name__ == "__main__":
    run()
