import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agents
from state import Plan, Task, manage_list, merge_task_results
from langchain_core.messages import HumanMessage


def _task(task_id="T1", deps=None):
    return Task(task_id=task_id, task_name="test", tool_required="knowledge_expert_tool", context_needed=deps or [], description="test")


def test_normal_task_id_is_valid():
    assert _task("T1").task_id == "T1"


def _assert_value_error(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_reserved_task_id_is_rejected():
    for task_id in ("__RESET__", "__SYSTEM_DEADLOCK__"):
        _assert_value_error(lambda task_id=task_id: _task(task_id))


def test_reserved_dependency_is_rejected():
    for dependency in ("__RESET__", "__SYSTEM_DEADLOCK__"):
        _assert_value_error(lambda dependency=dependency: _task("T1", [dependency]))


def test_duplicate_task_id_is_rejected():
    _assert_value_error(lambda: Plan(steps=[_task("T1"), _task("T1")]))


def test_internal_reset_protocol_still_works():
    assert manage_list(["T1"], ["__RESET__"]) == []
    assert merge_task_results({"T1": "result"}, {"__RESET__": "__RESET__"}) == {}


def test_executor_deadlock_sentinel_and_critic_recognition():
    plan = Plan(steps=[_task("T1", ["UNKNOWN_TASK"])])
    state = {
        "messages": [HumanMessage(content="test")],
        "plan": plan,
        "completed_tasks": [],
        "task_results": {},
        "execution_step_count": 0,
        "plan_loop_count": 2,
        "evidences": [],
        "evidence_seq": 0,
    }
    command = agents.executor_node(state)
    assert command.goto == "critic_node"
    deadlock_results = command.update["task_results"]
    assert "__SYSTEM_DEADLOCK__" in deadlock_results

    state["task_results"] = deadlock_results
    critic_command = agents.critic_node(state)
    assert critic_command.goto == "finalizer_node"
    assert critic_command.update["critic_verdict"].status == "deadlock"
