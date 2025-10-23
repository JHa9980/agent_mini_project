"""Quick check for the InfoCollector node."""

from pathlib import Path
from pprint import pprint
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.info_collector import info_collector_node  # type: ignore  # noqa: E402
from prompts import USER_ANALYSIS_PLAN  # type: ignore  # noqa: E402


def run() -> None:
    state = {"analysis_plan": USER_ANALYSIS_PLAN}
    updated = info_collector_node(state)
    pool = updated.get("evidence_pool", [])
    print(f"Collected {len(pool)} evidence items")
    for item in pool[:3]:
        pprint(item)


if __name__ == "__main__":
    run()
