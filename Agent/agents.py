import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from state import ReviewResult, CriticVerdict, FinalizerResult
from state import AgentState, Plan, EvidenceRecord
from langgraph.graph import END

# ==========================================
# 初始化阶段
# ==========================================
load_dotenv()

planner_llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.01,
    max_retries=3
)
structured_planner = planner_llm.with_structured_output(Plan)

from tools import tools_list

# 1. 构建工具路由字典 (利用 LangChain tool 的 .name 属性)
tool_map = {t.name: t for t in tools_list}

# 2. 初始化底层执行器专属 LLM (建议 temperature 设为 0.1，保证参数提取的稳定性)
executor_llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.1,
    max_retries=3
)

# ==========================================
# 全局规划者节点
# ==========================================
def planner_node(state: AgentState) -> Command:
    print("\n🧠 [Planner] -> 正在构建/重构全局执行树...")

    # 1. 提取上下文数据
    user_input = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            user_input = m.content
            break

    reflections_list = state.get("reflections", [])
    recent_reflections = reflections_list[-2:] if reflections_list else []
    reflections_str = "\n".join(recent_reflections) if recent_reflections else "无历史反思。"

    system_prompt = "你是一位资深的林草防护应急响应指挥官。\n"
    system_prompt += "【可用工具库严格限制】：\n"
    system_prompt += "1. 'vision_expert_tool': Qwen-VL-Plus 多模态视觉识别（分析林区现场照片，提取病虫害或火灾特征）。\n"
    system_prompt += "2. 'knowledge_expert_tool': RAG 知识库检索（必须查阅政策原文）。\n"
    system_prompt += "【执行策略】：\n"
    system_prompt += "- 遵循「先视觉识别，后政务检索」逻辑。\n"
    system_prompt += "- 合理设置 context_needed，串联任务数据。\n"
    system_prompt += "- 若存在「历史反思记录」，必须针对性补充知识检索步骤以满足合规审查。\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "当前线索: {user_input}\n\n历史反思: {reflections_str}\n\n请输出执行蓝图。")
    ])

    current_loop = state.get("plan_loop_count", 0)

    # 3. 容错解析与自我纠错引擎
    try:
        chain = prompt | structured_planner
        plan = chain.invoke({
            "user_input": user_input,
            "reflections_str": reflections_str
        })
    except Exception as e:
        print(f"⚠️ [Planner 异常] JSON 约束失败，触发自我重试机制: {e}")

        if current_loop >= 3:
            print("❌ [Planner 熔断] 达到最大重试次数，终止规划。")
            return Command(goto="END")

        error_feedback = f"系统提示：你的 JSON 输出格式不合法，请严格遵守 Schema。错误详情：{str(e)}"
        return Command(
            update={
                "messages": [("user", error_feedback)],
                "plan_loop_count": current_loop + 1
            },
            goto="planner_node"
        )

    # 4. 下发执行指令
    return Command(
        update={
            "plan": plan,
            "completed_tasks": ["__RESET__"],
            "task_results": {"__RESET__": "__RESET__"},
            "plan_loop_count": current_loop + 1,
            "execution_step_count": 0
        },
        goto="executor_node"
    )

import json

# ==========================================
# Evidence Provenance V1：证据台账辅助函数
# ==========================================
def _build_evidence_record(
    tool_name: str,
    task_id: str,
    plan_loop: int,
    tool_args: dict,
    content: str,
    seq: int,
) -> EvidenceRecord:
    """根据真实 Tool 输出包装一条 EvidenceRecord（id 由代码生成，不依赖 LLM）。"""
    if tool_name == "vision_expert_tool":
        etype = "vision"
        source = tool_args.get("image_path", "")
        metadata = {}
        if tool_args.get("user_description"):
            metadata["user_description"] = tool_args["user_description"]
    else:
        # knowledge_expert_tool 一次调用可能命中多个文档，V1 不拆分，source 记为工具名
        etype = "knowledge"
        source = "knowledge_expert_tool"
        metadata = {}
        if tool_args.get("query"):
            metadata["query"] = tool_args["query"]

    return EvidenceRecord(
        evidence_id=f"E{seq:03d}",
        type=etype,
        tool_name=tool_name,
        task_id=task_id,
        plan_loop=plan_loop,
        source=source,
        content=content,
        metadata=metadata,
    )


def _evidence_records_from_artifact(
    tool_name: str,
    task_id: str,
    plan_loop: int,
    tool_args: dict,
    content: str,
    artifact,
    tool_call_id,
    seq: int,
):
    """根据结构化 Tool artifact 决定是否登记 Evidence。

    返回 (records, contract_error)。content 仅作为可读文本，绝不参与状态判断。
    """
    if not isinstance(artifact, dict):
        return [], "工具返回契约无效，未登记证据。"

    status = artifact.get("status")
    if status not in {"success", "empty", "error"}:
        return [], "工具返回契约无效，未登记证据。"
    if status in {"empty", "error"}:
        return [], None

    if not isinstance(content, str) or not content.strip():
        return [], "工具返回契约无效，未登记证据。"

    if tool_name == "vision_expert_tool":
        evidence = artifact.get("evidence")
        if not isinstance(evidence, dict) or not evidence.get("image_path"):
            return [], "工具返回契约无效，未登记证据。"
        return [(_build_evidence_record(
            tool_name=tool_name,
            task_id=task_id,
            plan_loop=plan_loop,
            tool_args=tool_args,
            content=content,
            seq=seq,
        ))], None

    if tool_name == "knowledge_expert_tool":
        documents = artifact.get("documents")
        if not isinstance(documents, list) or not documents:
            return [], "工具返回契约无效，未登记证据。"
        records = []
        next_seq = seq
        for item in documents:
            if not isinstance(item, dict) or not isinstance(item.get("content"), str) or not item.get("content", "").strip():
                return [], "工具返回契约无效，未登记证据。"
            next_seq += 1
            records.append(_build_knowledge_evidence(
                task_id=task_id,
                plan_loop=plan_loop,
                tool_args=tool_args,
                tool_call_id=tool_call_id,
                item=item,
                seq=next_seq,
            ))
        return records, None

    return [], "工具返回契约无效，未登记证据。"


def _build_knowledge_evidence(
    task_id: str,
    plan_loop: int,
    tool_args: dict,
    tool_call_id,
    item: dict,
    seq: int,
) -> EvidenceRecord:
    """由单条 RAG 检索结果（artifact item）构建 document-level EvidenceRecord。"""
    src_meta = dict(item.get("metadata") or {})
    metadata = {
        "query": tool_args.get("query", ""),
        "rank": item.get("rank"),
        "raw_score": item.get("raw_score"),
        "score_semantics": item.get("score_semantics", "distance"),
    }
    if tool_call_id:
        metadata["tool_call_id"] = tool_call_id
    # 仅透传数据库真实存在的标题层级（Document 自带，非人为制造）
    for key in ("一级标题_章", "二级标题_节", "三级标题_条", "四级标题_项"):
        if src_meta.get(key):
            metadata[key] = src_meta[key]
    return EvidenceRecord(
        evidence_id=f"E{seq:03d}",
        type="knowledge",
        tool_name="knowledge_expert_tool",
        task_id=task_id,
        plan_loop=plan_loop,
        source=item.get("source", ""),
        content=item.get("content", ""),
        metadata=metadata,
    )


def _format_evidence_ledger(evidences) -> str:
    """将证据台账序列化为给 Finalizer 的可读文本清单。"""
    if not evidences:
        return "（本轮无已登记的工具证据）"
    lines = []
    for ev in evidences:
        lines.append(f"[EVIDENCE {ev.evidence_id}]")
        lines.append(f"type: {ev.type}")
        lines.append(f"tool: {ev.tool_name}")
        lines.append(f"task: {ev.task_id}")
        lines.append(f"plan_loop: {ev.plan_loop}")
        lines.append(f"source: {ev.source}")
        for k, v in ev.metadata.items():
            lines.append(f"{k}: {v}")
        lines.append("content:")
        lines.append(ev.content)
        lines.append("")
    return "\n".join(lines)


# ==========================================
# 动态执行者节点 (Executor Node) - V2 修复版
# ==========================================
def executor_node(state: AgentState) -> Command:
    print("\n⚙️ [Executor] -> 扫描执行树，寻找就绪的子任务...")

    plan = state.get("plan")
    completed_tasks = state.get("completed_tasks", [])
    task_results = state.get("task_results", {})
    execution_step_count = state.get("execution_step_count", 0)

    # 1. 每次 Executor 自循环都必须完成一个 task，或在无可执行任务时转入
    #    Critic/deadlock。合法任务总数不应被固定阈值截断；全图仍由
    #    recursion_limit 提供最后一道系统级保险。
    if not plan or not plan.steps:
        print("   ⚠️ [Executor] 执行树为空，移交合规审查。")
        return Command(goto="critic_node")

    # 2. 扫描策略：寻找第一个未完成且前置依赖已全部满足的有效任务
    next_task = None
    for task in plan.steps:
        if task.task_id not in completed_tasks:
            if all(dep in completed_tasks for dep in task.context_needed):
                next_task = task
                break

    # 3. 路由判决与死锁检测
    if next_task is None:
        uncompleted_tasks = [t.task_id for t in plan.steps if t.task_id not in completed_tasks]

        if uncompleted_tasks:
            error_msg = f"系统执行器异常：存在 {len(uncompleted_tasks)} 个任务因前置依赖死锁或缺失无法执行。卡死任务ID: {uncompleted_tasks}"
            print(f"   ❌ {error_msg}")

            return Command(
                update={"task_results": {"__SYSTEM_DEADLOCK__": error_msg}},
                goto="critic_node"
            )
        else:
            print("   ✅ [Executor] 所有子任务均已遍历完毕，跳出微循环。")
            return Command(update={}, goto="critic_node")

    print(f"   -> 锁定就绪任务: [{next_task.task_id}] {next_task.task_name}")

    # 4. 手术刀式的数据切片
    context_str = ""
    if next_task.context_needed:
        for dep_id in next_task.context_needed:
            if dep_id in task_results:
                context_str += f"【前置任务 {dep_id} 的输出】:\n{task_results[dep_id]}\n\n"
    if not context_str:
        context_str = "无前置数据依赖。"

    user_input = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            user_input = m.content
            break

    # 5. 指令封箱与参数解析
    executor_prompt = f"""你是一个高度专注的底层工具参数解析器。
【全局线索】：{user_input}
【当前任务】：{next_task.task_name}
【详细指令】：{next_task.description}
【可用的前置数据上下文】：
{context_str}

请严格结合上述信息，提取调用工具所需的参数。"""

    target_tool = tool_map.get(next_task.tool_required)
    if not target_tool:
        error_msg = f"执行失败：系统未注册底层工具 '{next_task.tool_required}'，请检查规划逻辑。"
        print(f"   ❌ {error_msg}")
        return Command(
            update={
                "completed_tasks": [next_task.task_id],
                "task_results": {next_task.task_id: error_msg},
                "execution_step_count": execution_step_count + 1
            },
            goto="executor_node"
        )

    llm_with_target_tool = executor_llm.bind_tools(
        [target_tool],
        tool_choice=next_task.tool_required
    )

    # 6. 物理执行工具与类型防御
    evidence_records = []
    new_evidence_seq = state.get("evidence_seq", 0)
    try:
        print(f"   -> 正在驱动工具: {next_task.tool_required} ...")
        response = llm_with_target_tool.invoke([("system", executor_prompt)])

        tool_calls = response.tool_calls
        if tool_calls:
            tool_call = tool_calls[0]
            print(f"   -> 成功提取参数: {tool_call['args']}")

            # 以 ToolCall 结构调用，保证 content_and_artifact 工具的 artifact 不被丢弃
            tool_call_input = {
                "type": "tool_call",
                "id": tool_call.get("id") or "",
                "name": tool_call.get("name") or next_task.tool_required,
                "args": tool_call.get("args") or {},
            }
            raw_output = target_tool.invoke(tool_call_input)

            artifact = None
            if hasattr(raw_output, "content") and hasattr(raw_output, "artifact"):
                # ToolMessage：content 给 LLM/台账，artifact 仅用于 provenance
                tool_output_string = raw_output.content if isinstance(raw_output.content, str) else str(raw_output.content)
                artifact = raw_output.artifact
            elif isinstance(raw_output, str):
                tool_output_string = raw_output
            elif isinstance(raw_output, (dict, list)):
                tool_output_string = json.dumps(raw_output, ensure_ascii=False)
            else:
                tool_output_string = str(raw_output)

            # Evidence Provenance V2：只依据结构化 artifact 登记证据。
            plan_loop = state.get("plan_loop_count", 0)
            records, contract_error = _evidence_records_from_artifact(
                tool_name=next_task.tool_required,
                task_id=next_task.task_id,
                plan_loop=plan_loop,
                tool_args=tool_call.get("args") or {},
                content=tool_output_string,
                artifact=artifact,
                tool_call_id=tool_call.get("id"),
                seq=new_evidence_seq,
            )
            if contract_error:
                tool_output_string = contract_error
            else:
                evidence_records = records
                new_evidence_seq += len(records)

        else:
            tool_output_string = "执行失败：模型未能生成合法的工具参数。"

    except Exception as e:
        print(f"   ❌ [Executor 异常] 工具调用崩溃: {e}")
        tool_output_string = "系统执行异常，未登记证据。"

    # 7. 基于 Command 的动态微循环重载
    update = {
        "completed_tasks": [next_task.task_id],
        "task_results": {next_task.task_id: tool_output_string},
        "execution_step_count": execution_step_count + 1,
    }
    if evidence_records:
        update["evidences"] = evidence_records
        update["evidence_seq"] = new_evidence_seq
        for er in evidence_records:
            rank_suffix = f" rank={er.metadata.get('rank')}" if er.metadata.get("rank") else ""
            print(f"   📌 [Evidence] 登记 {er.evidence_id} ({er.type}) <- {er.tool_name}{rank_suffix}")

    return Command(update=update, goto="executor_node")


# ==========================================
# 审查者节点初始化
# ==========================================
critic_llm = planner_llm.with_structured_output(ReviewResult)

# ==========================================
# 合规审查者节点 (Critic Node)
# ==========================================
def critic_node(state: AgentState) -> Command:
    print("\n⚖️ [Critic] -> 启动政务合规与逻辑审查...")

    task_results = state.get("task_results", {})
    current_loops = state.get("plan_loop_count", 0)
    MAX_ALLOWABLE_LOOPS = 2

    # ---------------------------------------------------------
    # 防线：承接 Executor 抛出的拓扑死锁异常（系统级错误，无草稿可审查，先行拦截）
    # ---------------------------------------------------------
    if "__SYSTEM_DEADLOCK__" in task_results:
        deadlock_msg = task_results["__SYSTEM_DEADLOCK__"]
        if current_loops >= MAX_ALLOWABLE_LOOPS:
            print(f"   ⚠️ [Critic 质量软着陆] 执行器依赖死锁且已达最大重规划次数 ({MAX_ALLOWABLE_LOOPS})，停止迭代。")
            fallback_warning = (
                f"【质量软着陆提示】执行过程中出现任务依赖死锁，且系统已达到本次任务的最大重规划次数（{MAX_ALLOWABLE_LOOPS}），"
                f"因此停止继续迭代，输出当前最佳可用结果，建议人工复核。"
            )
            draft = "\n".join([f"【任务 {k}】: {v}" for k, v in task_results.items() if k not in ("__RESET__", "__SYSTEM_DEADLOCK__")])
            return Command(
                update={
                    "messages": [("ai", f"{fallback_warning}\n\n【死锁详情】{deadlock_msg}\n\n{draft}")],
                    "critic_verdict": CriticVerdict(status="deadlock", is_compliant=None, plan_loop=current_loops),
                },
                goto="finalizer_node"
            )

        print("   ❌ [Critic 拦截] 检测到执行器依赖死锁，强制打回重构计划。")
        reflection_log = f"【系统架构驳回】 你的上一次计划导致了底层执行器死锁。错误详情：{deadlock_msg}。请重新审视 context_needed 依赖关系，生成无环且连贯的新计划。"

        return Command(
            update={
                "reflections": [reflection_log],
                "critic_verdict": CriticVerdict(status="replan", is_compliant=None, plan_loop=current_loops),
            },
            goto="planner_node"
        )

    # ---------------------------------------------------------
    # 核心审查逻辑：聚合数据并进行政务合规判断
    # ---------------------------------------------------------
    draft_content = "\n\n".join([f"【任务 {k} 执行汇报】:\n{v}" for k, v in task_results.items() if k != "__RESET__"])
    if not draft_content.strip():
        draft_content = "无任何有效执行数据。"

    # Evidence Provenance V1：序列化证据台账，供 Finalizer 透传（Critic 本身不产生证据）
    evidences = state.get("evidences", [])
    evidence_ledger = _format_evidence_ledger(evidences)

    critic_prompt = f"""
你现在担任林草防护多智能体系统的质量审查器。你的职责是审查底层子系统汇总提交上来的异常事件处理草稿，判断其是否具备成为正式报告的基础；你不是知识补充器，不得引入任何新的外部事实。

【草稿综合内容】：
{draft_content}

【不可逾越的政务审查准则】：
1. 生物学准确性验证：草稿是否明确了具体的病虫害种类或异常隐患状态？
2. 政策红线验证：草稿中是否包含对官方政务 PDF 文件的直接引用（例如明确指出了某某条例、防治指导意见、或安全操作规范）？

【Critic 证据边界】（必须严格遵守）：
1. 你是质量审查器，不是知识补充器。你的 critique 只能评价"已有材料是否充分"，不得新增任何外部事实。
2. 所有具体事实只能来自上面【草稿综合内容】；草稿中没有出现的信息，不得自行补全。
3. 如果发现缺少某类证据，只能描述"缺什么"，例如："缺少权威政策依据""缺少病害鉴别依据""缺少来源支撑""建议补充检索相关政策或技术规范"；不得自行给出具体的新文件名、文号、条款号、发布日期、行政机关或定量指标。
4. critique 应描述"缺什么证据"，而不是断言"正确答案应该是什么"。
5. 若草稿中已经出现某文件名、文号、条款或日期，可以引用它进行批评；若草稿中没有出现，禁止自行新增。
6. 对专业事实同样适用：草稿未出现的具体数值、指标、发生条件等，不得凭模型知识写入 critique。

【裁决逻辑】：
- 如果草稿仅仅提供了通用的大语言模型建议（如"建议喷洒农药"），而没有任何来自本地知识库的具体政策法规名称与条款作为支撑，你必须判定为违规（is_compliant=False）！
- 如果违规，在 critique 中严厉指出草稿缺失了哪一类（哪方面）的政策依据，并给出"应补充检索哪类政策/规范"的修正方向，但不得给出未经检索验证的具体文件名、文号、条款号或日期。
- 如果合规（is_compliant=True），在 critique 中简要总结其合规依据。
"""

    try:
        review: ReviewResult = critic_llm.invoke([("system", critic_prompt)])
    except Exception as e:
        print(f"   ⚠️ [Critic 异常] 审查模型调用失败: {e}")
        if current_loops < MAX_ALLOWABLE_LOOPS:
            controlled_critique = "Critic 审查调用失败，已进入重新规划。"
            return Command(
                update={
                    "reflections": [f"【审查系统异常】 {controlled_critique}"],
                    "critic_verdict": CriticVerdict(
                        status="replan",
                        is_compliant=None,
                        plan_loop=current_loops,
                        critique=controlled_critique,
                    ),
                },
                goto="planner_node"
            )

        controlled_critique = "Critic 多次无法完成有效审查，已达到最大规划轮次，进入降级输出。"
        fallback_warning = (
            "【质量软着陆提示】质量审查服务未能完成有效审查，系统已达到本次任务的最大规划轮次，"
            "因此停止继续迭代，并基于当前已有证据与执行结果生成降级报告；本结果未经 Critic 审查通过，建议人工复核。"
        )
        finalizer_material = (
            f"{fallback_warning}\n\n"
            f"【审查状态】\n{controlled_critique}\n\n"
            f"【证据清单 Evidence Ledger】\n{evidence_ledger}\n\n"
            f"【当前轮执行汇总】\n{draft_content}"
        )
        return Command(
            update={
                "messages": [("ai", finalizer_material)],
                "critic_verdict": CriticVerdict(
                    status="soft_landing",
                    is_compliant=None,
                    plan_loop=current_loops,
                    critique=controlled_critique,
                ),
            },
            goto="finalizer_node"
        )

    # ---------------------------------------------------------
    # 动态路由分发 (Command API)
    # ---------------------------------------------------------
    if review.is_compliant:
        print("   ✅ [Critic 裁决] 合规审查通过！移交报告生成节点。")
        finalizer_material = (
            f"【合规审查通过】\n\n"
            f"【证据清单 Evidence Ledger】\n{evidence_ledger}\n\n"
            f"【当前轮执行汇总】\n{draft_content}"
        )
        return Command(
            update={
                "messages": [("ai", finalizer_material)],
                "critic_verdict": CriticVerdict(status="passed", is_compliant=True, plan_loop=current_loops, critique=review.critique),
            },
            goto="finalizer_node"
        )

    # 审查未通过：根据剩余重规划额度决定 Replan 或质量软着陆
    if current_loops < MAX_ALLOWABLE_LOOPS:
        print(f"   ❌ [Critic 裁决] 审查未通过，打回重做！\n   -> 反思意见: {review.critique}")
        reflection_log = f"【合规审查被驳回】 驳回原因及强制修改指令: {review.critique}"
        return Command(
            update={
                "reflections": [reflection_log],
                "critic_verdict": CriticVerdict(status="replan", is_compliant=False, plan_loop=current_loops, critique=review.critique),
            },
            goto="planner_node"
        )

    # 达到最大重规划次数：质量软着陆，保留本轮真实审查意见，不再 Replan
    print(f"   ⚠️ [Critic 质量软着陆] 已达最大重规划次数 ({MAX_ALLOWABLE_LOOPS})，停止迭代，携带真实审查意见进入报告生成。")
    fallback_warning = (
        f"【质量软着陆提示】经多轮规划、执行与质量审查后，当前结果仍有部分审查项未完全满足。"
        f"系统已达到本次任务的最大重规划次数（{MAX_ALLOWABLE_LOOPS}），"
        f"因此停止继续迭代，输出当前最佳可用结果，建议对以下未完全满足的审查项进行人工复核。"
    )
    critique_note = f"【最后一次质量审查未通过的原因】\n{review.critique}"
    draft = "\n".join([f"【任务 {k}】: {v}" for k, v in task_results.items() if k != "__RESET__"])
    finalizer_material = (
        f"{fallback_warning}\n\n"
        f"{critique_note}\n\n"
        f"【证据清单 Evidence Ledger】\n{evidence_ledger}\n\n"
        f"【当前轮执行汇总】\n{draft}"
    )
    return Command(
        update={
            "messages": [("ai", finalizer_material)],
            "critic_verdict": CriticVerdict(status="soft_landing", is_compliant=False, plan_loop=current_loops, critique=review.critique),
        },
        goto="finalizer_node"
    )


finalizer_llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.3,
    max_retries=3
)

# ==========================================
# 报告生成者节点 (Finalizer Node)
# ==========================================
def finalizer_node(state: AgentState) -> Command:
    print("\n📝 [Finalizer] -> 正在将碎片化数据重组为政务公文报告...")

    approved_data = state["messages"][-1].content

    prompt = f"""你是一位林业领域的专业分析报告撰写专家。本系统是智能辅助决策系统，并非行政机关，你撰写的报告是"辅助决策分析结果"，而非正式行政公文。

请根据以下经过合规审查的【基础材料】，撰写一份专业的《林草异常诊断与应急处置智能分析报告》。

【撰写要求】：
1. 格式规范：包含标题、事件概述、诊断结论、政策依据、处置建议等标准报告模块。
2. 语气风格：严肃、客观、专业，符合专业分析报告行文规范。
3. 事实红线：必须绝对忠实于基础材料，严禁捏造材料中未提及的病害名称或政策条款！如果材料中明确包含【系统高级警报】等环境/系统故障提示，才可在报告开头以"红色预警"形式显著标出；如果材料中包含【质量软着陆提示】（表示多轮审查后仍有部分项未完全满足、系统已停止迭代），则必须在报告开头用中性、客观的语气说明"本报告基于当前最佳可用结果生成，尚需人工复核完善"，禁止使用"红色预警""最高级""特急"等系统事故表述。

【事实来源约束】（必须严格遵守）：
1. 报告中的每一处具体事实，只能来源于下面的【基础材料】，不得凭常识或经验自行补全。
2. 日期：本系统不提供可靠当前日期，禁止自行生成"报告生成时间"或任何具体日期；如确需标注时间，只能写"生成时间：未提供"，或直接不写。
3. 政策/法律/规范性文件：只能引用【基础材料】中明确出现的文件名、文号、条款号、发布日期、修订日期；当材料只提供文件名而未提供具体日期或文号时，只能写文件名，不得补日期、文号或发布机关。
4. 行政身份：不得声称本报告由任何真实或虚构的政府机关（如××省林业局、国家林草局、某处室）正式发布，不得生成"盖章""正式文件编号""内部机密""抄送单位""联系人""联系电话"等行政公文要素。
5. 对无法确认的具体事实：必须明确写"当前证据不足以确认""知识库检索结果未提供具体信息""建议以正式文件原文为准"，严禁猜测或补全。

【基础材料】：
{approved_data}
"""

    try:
        response = finalizer_llm.invoke([("user", prompt)])
        report = response.content
        if not isinstance(report, str) or not report.strip():
            print("   ❌ [Finalizer 异常] 模型返回空报告")
            finalizer_result = FinalizerResult(
                status="error",
                report=None,
                error_type="empty_finalizer_response",
            )
            final_report = "最终报告生成失败。"
        else:
            finalizer_result = FinalizerResult(
                status="success",
                report=report,
                error_type=None,
            )
            final_report = report
            print("   ✅ [Finalizer] 政务公文报告生成完毕！")
    except Exception as e:
        print(f"   ❌ [Finalizer 异常] 报告生成失败: {e}")
        finalizer_result = FinalizerResult(
            status="error",
            report=None,
            error_type="finalizer_llm_error",
        )
        final_report = "最终报告生成失败。"

    return Command(
        update={
            "messages": [("ai", final_report)],
            "finalizer_result": finalizer_result,
        },
        goto=END
    )
