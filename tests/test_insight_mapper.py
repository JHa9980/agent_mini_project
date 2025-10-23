"""Quick check for the InsightMapper node."""

from pathlib import Path
from pprint import pprint
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.info_collector import info_collector_node  # type: ignore  # noqa: E402
from agents.insight_mapper import insight_mapper_node  # type: ignore  # noqa: E402
from prompts import USER_ANALYSIS_PLAN  # type: ignore  # noqa: E402


def run() -> None:
    state = {"analysis_plan": USER_ANALYSIS_PLAN}
    state.update(info_collector_node(state))
    updated = insight_mapper_node(state)
    insights = updated.get("trend_insights", [])
    print(f"Generated {len(insights)} insights")
    for item in insights:
        pprint(item)


if __name__ == "__main__":
    run()
