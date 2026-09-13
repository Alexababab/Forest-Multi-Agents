"""
Critic Verdict V1.1 针对性测试
验证 critic_node 在五种核心场景下写入 state 的 critic_verdict 结构与路由正确。

运行方式（在 Agent 目录下）：
    .venv/Scripts/python.exe tests/test_critic_verdict.py

本测试通过 monkeypatch 替换 critic_llm，不触发真实 LLM / 工具 / 向量库调用。
"""

import os
import sys

# Windows 控制台默认 GBK，Agent 的 emoji print 会触发 UnicodeEncodeError，重配为 UTF-8（与 api.py 一致）
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

# 从 tests/ 子目录向上找到 Agent 根目录，确保 `import agents` / `import state` 可用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage

import agents
from state import EvidenceRecord, ReviewResult


class _FakeCriticLLM:
    """替身：按预设的 ReviewResult 返回，绕过真实 LLM 调用。"""
    def __init__(self, review: ReviewResult):
        self._review = review

    def invoke(self, *args, **kwargs):
        return self._review


class _FailingCriticLLM:
    def __init__(self, message: str):
        self._message = message

    def invoke(self, *args, **kwargs):
        raise RuntimeError(self._message)


def _make_state(plan_loop_count: int, task_results: dict) -> dict:
    return {
        "messages": [HumanMessage(content="测试线索")],
        "plan_loop_count": plan_loop_count,
        "execution_step_count": 0,
        "completed_tasks": [],
        "task_results": task_results,
        "reflections": [],
        "evidences": [],
        "evidence_seq": 0,
    }


def _patch_critic(review: ReviewResult):
    agents.critic_llm = _FakeCriticLLM(review)


_PASSED = 0
_FAILED = 0


def check(name, cond, detail=""):
    global _PASSED, _FAILED
    if cond:
        _PASSED += 1
        print(f"  ✅ PASS  {name}  {detail}")
    else:
        _FAILED += 1
        print(f"  ❌ FAIL  {name}  {detail}")


def main():
    # CASE 1：loop=1，不通过 → replan
    print("\n[Case 1] loop=1, is_compliant=False -> replan")
    _patch_critic(ReviewResult(is_compliant=False, critique="缺少权威政策依据"))
    cmd = agents.critic_node(_make_state(1, {"task_1": "草稿"}))
    v = cmd.update.get("critic_verdict")
    check("status == replan", v.status == "replan", f"got {v.status}")
    check("is_compliant == False", v.is_compliant is False, f"got {v.is_compliant}")
    check("plan_loop == 1", v.plan_loop == 1, f"got {v.plan_loop}")
    check("critique 保留", v.critique == "缺少权威政策依据", f"got {v.critique}")
    check("goto == planner_node", cmd.goto == "planner_node", f"got {cmd.goto}")

    # CASE 6：Critic 异常且仍有额度 → replan
    print("\n[Case 6] critic exception, loop=1 -> bounded replan")
    agents.critic_llm = _FailingCriticLLM("Connection error")
    cmd = agents.critic_node(_make_state(1, {"task_1": "草稿"}))
    v = cmd.update.get("critic_verdict")
    check("exception status == replan", v.status == "replan", f"got {v.status}")
    check("exception is_compliant is None", v.is_compliant is None, f"got {v.is_compliant}")
    check("exception goto == planner_node", cmd.goto == "planner_node", f"got {cmd.goto}")
    check("exception detail 未进入 state", "Connection error" not in str(cmd.update), str(cmd.update))

    # CASE 7/8/9：达到上限的异常（含 structured output failure / 不同文案）→ terminal soft landing
    print("\n[Case 7] critic exception, loop=2 -> terminal soft landing")
    for error_message in ("Connection error", "structured output parsing failed", "random critic backend failure"):
        agents.critic_llm = _FailingCriticLLM(error_message)
        cmd = agents.critic_node(_make_state(2, {"task_1": "草稿"}))
        v = cmd.update.get("critic_verdict")
        check("terminal status == soft_landing", v.status == "soft_landing", f"got {v.status}")
        check("terminal is_compliant is None", v.is_compliant is None, f"got {v.is_compliant}")
        check("terminal goto == finalizer_node", cmd.goto == "finalizer_node", f"got {cmd.goto}")
        check("terminal exception detail 未进入 state", error_message not in str(cmd.update), str(cmd.update))

    # CASE 10：异常终止仍把既有 Evidence Ledger 注入 Finalizer material
    print("\n[Case 10] terminal exception preserves evidence ledger")
    state = _make_state(2, {"task_1": "草稿"})
    state["evidences"] = [
        EvidenceRecord(evidence_id="E001", type="vision", tool_name="vision_expert_tool", task_id="task_1", plan_loop=1, source="a.jpg", content="vision", metadata={}),
        EvidenceRecord(evidence_id="E002", type="knowledge", tool_name="knowledge_expert_tool", task_id="task_1", plan_loop=1, source="a.pdf", content="policy", metadata={}),
    ]
    agents.critic_llm = _FailingCriticLLM("backend failed")
    cmd = agents.critic_node(state)
    material = cmd.update["messages"][0][1]
    check("Evidence Ledger 保留", "Evidence Ledger" in material)
    check("E001 保留", "E001" in material)
    check("E002 保留", "E002" in material)

    # CASE 2：loop=2，通过 → passed
    print("\n[Case 2] loop=2, is_compliant=True -> passed")
    _patch_critic(ReviewResult(is_compliant=True, critique="已引用条例，合规"))
    cmd = agents.critic_node(_make_state(2, {"task_1": "草稿"}))
    v = cmd.update.get("critic_verdict")
    check("status == passed", v.status == "passed", f"got {v.status}")
    check("is_compliant == True", v.is_compliant is True, f"got {v.is_compliant}")
    check("plan_loop == 2", v.plan_loop == 2, f"got {v.plan_loop}")
    check("goto == finalizer_node", cmd.goto == "finalizer_node", f"got {cmd.goto}")

    # CASE 3：loop=2，不通过 → soft_landing
    print("\n[Case 3] loop=2, is_compliant=False -> soft_landing")
    _patch_critic(ReviewResult(is_compliant=False, critique="仍缺具体条款号"))
    cmd = agents.critic_node(_make_state(2, {"task_1": "草稿"}))
    v = cmd.update.get("critic_verdict")
    check("status == soft_landing", v.status == "soft_landing", f"got {v.status}")
    check("is_compliant == False", v.is_compliant is False, f"got {v.is_compliant}")
    check("plan_loop == 2", v.plan_loop == 2, f"got {v.plan_loop}")
    check("critique 保留", v.critique == "仍缺具体条款号", f"got {v.critique}")
    check("goto == finalizer_node", cmd.goto == "finalizer_node", f"got {cmd.goto}")

    # CASE 4（系统死锁软着陆）：loop=2，死锁 → deadlock → finalizer
    print("\n[Case 4] deadlock, loop=2 -> deadlock (降级 finalizer)")
    _patch_critic(ReviewResult(is_compliant=True, critique=""))
    cmd = agents.critic_node(_make_state(2, {"__SYSTEM_DEADLOCK__": "卡死任务: ['x']", "task_1": "草稿"}))
    v = cmd.update.get("critic_verdict")
    check("status == deadlock", v.status == "deadlock", f"got {v.status}")
    check("is_compliant is None", v.is_compliant is None, f"got {v.is_compliant}")
    check("goto == finalizer_node", cmd.goto == "finalizer_node", f"got {cmd.goto}")

    # CASE 5（系统死锁打回）：loop=1，死锁 → replan → planner
    print("\n[Case 5] deadlock, loop=1 -> replan (强制重构)")
    _patch_critic(ReviewResult(is_compliant=True, critique=""))
    cmd = agents.critic_node(_make_state(1, {"__SYSTEM_DEADLOCK__": "卡死任务: ['x']"}))
    v = cmd.update.get("critic_verdict")
    check("status == replan", v.status == "replan", f"got {v.status}")
    check("is_compliant is None", v.is_compliant is None, f"got {v.is_compliant}")
    check("goto == planner_node", cmd.goto == "planner_node", f"got {cmd.goto}")

    print("\n" + "=" * 50)
    print(f"结果: {_PASSED} passed, {_FAILED} failed")
    print("=" * 50)
    if _FAILED:
        print("❌ CRITIC VERDICT TEST FAILED")
        sys.exit(1)
    print("✅ CRITIC VERDICT TEST PASSED")


if __name__ == "__main__":
    main()
