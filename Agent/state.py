from typing import Annotated, Dict, List, Literal, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator, model_validator
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# ==========================================
# 1. Pydantic 模型的数据契约定义 (保持不变)
# ==========================================
RESERVED_TASK_IDS = frozenset({"__RESET__", "__SYSTEM_DEADLOCK__"})


class Task(BaseModel):
    task_id: str = Field(..., description="任务的全局唯一标识符，例如 'step_1'")
    task_name: str = Field(..., description="清晰的任务名称，如林区枯死木图像特征提取")
    tool_required: str = Field(..., description="指定使用的底层工具，仅限 'vision_expert_tool' 或 'knowledge_expert_tool'")
    context_needed: List[str] = Field(default_factory=list, description="前置任务 ID 列表")
    description: str = Field(..., description="详细指令与预期目标")

    @field_validator("task_id")
    @classmethod
    def reject_reserved_task_id(cls, value: str) -> str:
        if value in RESERVED_TASK_IDS:
            raise ValueError(f"task_id 使用了系统保留标识: {value}")
        return value

    @field_validator("context_needed")
    @classmethod
    def reject_reserved_dependencies(cls, value: List[str]) -> List[str]:
        reserved = RESERVED_TASK_IDS.intersection(value)
        if reserved:
            raise ValueError(f"context_needed 使用了系统保留标识: {sorted(reserved)}")
        return value

class Plan(BaseModel):
    steps: List[Task] = Field(..., description="按依赖顺序排列的待执行任务列表")

    @model_validator(mode="after")
    def reject_duplicate_task_ids(self):
        task_ids = [task.task_id for task in self.steps]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Plan 中 task_id 必须唯一")
        return self

class ReviewResult(BaseModel):
    is_compliant: bool = Field(..., description="是否完全满足合规性要求")
    critique: str = Field(..., description="详细的反思意见")


class CriticVerdict(BaseModel):
    """Critic 结构化裁决：把「重新规划 / 通过 / 质量软着陆 / 系统死锁降级」写入 state，防止语义在 Critic→State→SSE 链上丢失。"""
    status: Literal["replan", "passed", "soft_landing", "deadlock"] = Field(..., description="裁决类型")
    is_compliant: Optional[bool] = Field(default=None, description="合规结论；系统级分支（死锁/异常）无合规结论时为 None")
    plan_loop: int = Field(..., description="裁决发生时所在的规划轮次")
    critique: Optional[str] = Field(default=None, description="审查意见；系统级分支无审查意见时为 None")


class FinalizerResult(BaseModel):
    """Finalizer 业务结果：区分真实报告与生成失败。"""
    status: Literal["success", "error"] = Field(..., description="报告生成状态")
    report: Optional[str] = Field(default=None, description="成功时的最终报告")
    error_type: Optional[str] = Field(default=None, description="失败时的稳定错误类型")


class EvidenceRecord(BaseModel):
    evidence_id: str = Field(..., description="run 内唯一证据编号，如 E001")
    type: Literal["vision", "knowledge"] = Field(..., description="证据类型")
    tool_name: str = Field(..., description="产生证据的底层工具名")
    task_id: str = Field(..., description="产生证据的任务 ID")
    plan_loop: int = Field(..., description="第几轮规划产生")
    source: str = Field(..., description="证据来源（vision=图片路径，knowledge=工具名）")
    content: str = Field(..., description="工具原始输出文本")
    metadata: dict = Field(default_factory=dict, description="附加元数据（query / user_description 等）")

# ==========================================
# 2. 具备重置能力的高级 Reducers (修复风险一)
# ==========================================
def manage_list(left: List[str], right: List[str]) -> List[str]:
    """支持清空指令的列表聚合器"""
    if right and right[0] == "__RESET__":
        return []
    return (left or []) + (right or [])

def merge_task_results(left: Dict[str, str], right: Dict[str, str]) -> Dict[str, str]:
    """支持清空指令的字典聚合器"""
    if right and right.get("__RESET__") == "__RESET__":
        return {}
    if not left: return right
    if not right: return left
    return {**left, **right}

def append_evidences(left: List[EvidenceRecord], right: List[EvidenceRecord]) -> List[EvidenceRecord]:
    """证据台账聚合器：只追加、不清空（跨 Planner Replan 持久，不随 task_results 重置）。"""
    return (left or []) + (right or [])

# ==========================================
# 3. 全局 AgentState 定义
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    plan: Optional[Plan]
    
    # 注入高级 Reducer
    completed_tasks: Annotated[List[str], manage_list]
    task_results: Annotated[Dict[str, str], merge_task_results]
    reflections: Annotated[List[str], manage_list]
    
    # 移除整型的 operator.add，改为业务层显式覆盖，便于直接清零
    plan_loop_count: int
    execution_step_count: int

    # Evidence Provenance V1：证据台账（跨 Planner Replan 持久，不随 task_results 重置）
    evidences: Annotated[List[EvidenceRecord], append_evidences]
    evidence_seq: int

    # Critic Verdict V1.1：最近一次 Critic 裁决（Planner Replan 后保留，直到下一次 Critic 覆盖）
    critic_verdict: Optional[CriticVerdict]

    # Finalizer Result V1：最终报告生成的结构化业务状态
    finalizer_result: Optional[FinalizerResult]
