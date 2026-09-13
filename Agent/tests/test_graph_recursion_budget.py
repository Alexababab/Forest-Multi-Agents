import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import GRAPH_RECURSION_LIMIT


def _steps(tasks, rounds, planner_retries_per_round=0):
    # Each round: planner + N executor task turns + final executor scan + critic.
    # The final round additionally runs finalizer.
    return rounds * (tasks + 3 + planner_retries_per_round) + 1


def test_budget_covers_expected_plans():
    assert GRAPH_RECURSION_LIMIT == 64
    assert _steps(3, 1) == 7
    assert _steps(12, 1) == 16
    assert _steps(12, 2) == 31
    assert _steps(20, 2) == 47
    assert _steps(20, 2, planner_retries_per_round=3) == 53
    assert _steps(20, 2, planner_retries_per_round=3) < GRAPH_RECURSION_LIMIT


def test_budget_remains_finite_safety_cap():
    assert GRAPH_RECURSION_LIMIT > 0
    assert GRAPH_RECURSION_LIMIT < 100
