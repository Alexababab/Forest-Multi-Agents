import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage

import agents
from state import Plan, Task


class _FakeTool:
    name = "knowledge_expert_tool"

    def __init__(self, artifact):
        self.artifact = artifact

    def invoke(self, tool_call):
        return SimpleNamespace(content="tool result", artifact=self.artifact)


class _FakeExecutor:
    def __init__(self):
        self.tool_calls = [{"id": "call-1", "name": "knowledge_expert_tool", "args": {"query": "q"}}]

    def bind_tools(self, *args, **kwargs):
        return self

    def invoke(self, *_):
        return SimpleNamespace(tool_calls=self.tool_calls)


def _plan(count, chain=False):
    tasks = []
    for i in range(count):
        deps = [f"task_{i}"] if chain and i else []
        tasks.append(Task(
            task_id=f"task_{i + 1}",
            task_name=f"Task {i + 1}",
            tool_required="knowledge_expert_tool",
            context_needed=deps,
            description="test",
        ))
    return Plan(steps=tasks)


def _run(plan, artifact=None):
    state = {
        "messages": [HumanMessage(content="test")],
        "plan": plan,
        "completed_tasks": [],
        "task_results": {},
        "execution_step_count": 0,
        "plan_loop_count": 1,
        "evidences": [],
        "evidence_seq": 0,
    }
    fake_tool = _FakeTool(artifact or {"status": "empty", "documents": []})
    with patch.object(agents, "tool_map", {fake_tool.name: fake_tool}), patch.object(agents, "executor_llm", _FakeExecutor()):
        for _ in range(len(plan.steps) + 1):
            cmd = agents.executor_node(state)
            update = cmd.update or {}
            state["completed_tasks"] = state["completed_tasks"] + update.get("completed_tasks", [])
            state["task_results"] = {**state["task_results"], **update.get("task_results", {})}
            state["execution_step_count"] = update.get("execution_step_count", state["execution_step_count"])
            if cmd.goto == "critic_node":
                return state, cmd
    raise AssertionError("executor did not reach critic")


def test_legal_plans_over_eight_tasks_complete():
    for count in (3, 8, 9, 12):
        state, cmd = _run(_plan(count))
        assert cmd.goto == "critic_node"
        assert state["completed_tasks"] == [f"task_{i}" for i in range(1, count + 1)]


def test_dependency_chain_completes_in_order():
    state, cmd = _run(_plan(10, chain=True))
    assert cmd.goto == "critic_node"
    assert state["completed_tasks"] == [f"task_{i}" for i in range(1, 11)]


def test_cycle_and_missing_dependency_are_deadlocks():
    cycle = Plan(steps=[
        Task(task_id="t1", task_name="T1", tool_required="knowledge_expert_tool", context_needed=["t2"], description="test"),
        Task(task_id="t2", task_name="T2", tool_required="knowledge_expert_tool", context_needed=["t1"], description="test"),
    ])
    state, cmd = _run(cycle)
    assert cmd.goto == "critic_node"
    assert "__SYSTEM_DEADLOCK__" in state["task_results"]

    missing = Plan(steps=[
        Task(task_id="t1", task_name="T1", tool_required="knowledge_expert_tool", context_needed=["UNKNOWN_TASK"], description="test"),
    ])
    state, cmd = _run(missing)
    assert cmd.goto == "critic_node"
    assert "__SYSTEM_DEADLOCK__" in state["task_results"]


def test_empty_error_and_contract_failure_still_complete_task():
    for artifact in (
        {"status": "empty", "documents": []},
        {"status": "error", "error_type": "retrieval_error"},
        {"status": "banana"},
    ):
        state, cmd = _run(_plan(2), artifact)
        assert cmd.goto == "critic_node"
        assert state["completed_tasks"] == ["task_1", "task_2"]
