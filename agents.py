import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from state import ReviewResult
from state import AgentState, Plan

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

    system_prompt = """你是一位资深的林草防护应急响应指挥官。
【可用工具库严格限制】：
1. 'vision_expert_tool': 解析林区图像。
2. 'knowledge_expert_tool': RAG 知识库检索（必须查阅政策原文）。
【执行策略】：
- 遵循“先视觉识别，后政务检索”逻辑。
- 合理设置 context_needed，串联任务数据。
- 若存在“历史反思记录”，必须针对性补充知识检索步骤以满足合规审查。
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "当前线索: {user_input}\n\n历史反思: {reflections_str}\n\n请输出执行蓝图。")
    ])

    current_loop = state.get("plan_loop_count", 0)

    # 3. 容错解析与自我纠错引擎
    try:
        chain = prompt | structured_planner
        # 修正风险一：严格对齐模板变量名
        plan = chain.invoke({
            "user_input": user_input, 
            "reflections_str": reflections_str
        })
    except Exception as e:
        print(f"⚠️ [Planner 异常] JSON 约束失败，触发自我重试机制: {e}")
        
        # 修正风险二：增加熔断机制
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
# 动态执行者节点 (Executor Node) - V2 修复版
# ==========================================
def executor_node(state: AgentState) -> Command:
    print("\n⚙️ [Executor] -> 扫描执行树，寻找就绪的子任务...")

    plan = state.get("plan")
    completed_tasks = state.get("completed_tasks", [])
    task_results = state.get("task_results", {})
    execution_step_count = state.get("execution_step_count", 0)

    # 1. 架构级防弹机制：防止图状态陷入无底线微循环死锁
    if execution_step_count >= 8:
        print("   ⚠️ [Executor 熔断] 任务队列微循环次数超限，强制移交合规审查。")
        return Command(goto="critic_node")

    if not plan or not plan.steps:
        print("   ⚠️ [Executor] 执行树为空，移交合规审查。")
        return Command(goto="critic_node")

    # 2. 扫描策略：寻找第一个未完成且前置依赖已全部满足的有效任务
    next_task = None
    for task in plan.steps:
        if task.task_id not in completed_tasks:
            # 校验当前任务所需的所有上下文(依赖任务)是否已执行完毕
            if all(dep in completed_tasks for dep in task.context_needed):
                next_task = task
                break

    # 3. 路由判决与死锁检测 (修复风险一)
    if next_task is None:
        # 提取尚未执行的任务列表
        uncompleted_tasks = [t.task_id for t in plan.steps if t.task_id not in completed_tasks]
        
        if uncompleted_tasks:
            # 发生依赖死锁或幽灵依赖，任务队列卡死
            error_msg = f"系统执行器异常：存在 {len(uncompleted_tasks)} 个任务因前置依赖死锁或缺失无法执行。卡死任务ID: {uncompleted_tasks}"
            print(f"   ❌ {error_msg}")
            
            # 将死锁信息作为特殊结果注入，交由 Critic 节点审判并打回 Planner
            return Command(
                update={"task_results": {"__SYSTEM_DEADLOCK__": error_msg}},
                goto="critic_node"
            )
        else:
            print("   ✅ [Executor] 所有子任务均已遍历完毕，跳出微循环。")
            return Command(goto="critic_node")

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

    # 6. 物理执行工具与类型防御 (修复风险二)
    try:
        print(f"   -> 正在驱动工具: {next_task.tool_required} ...")
        response = llm_with_target_tool.invoke([("system", executor_prompt)])
        
        tool_calls = response.tool_calls
        if tool_calls:
            tool_call = tool_calls[0]
            print(f"   -> 成功提取参数: {tool_call['args']}")
            
            # 执行底层工具
            raw_output = target_tool.invoke(tool_call["args"])
            
            # 防御性转换：确保最终写入 task_results 的一定是 str 类型
            if isinstance(raw_output, str):
                tool_output_string = raw_output
            elif isinstance(raw_output, (dict, list)):
                tool_output_string = json.dumps(raw_output, ensure_ascii=False)
            else:
                tool_output_string = str(raw_output)
                
        else:
            tool_output_string = "执行失败：模型未能生成合法的工具参数。"

    except Exception as e:
        print(f"   ❌ [Executor 异常] 工具调用崩溃: {e}")
        tool_output_string = f"执行阶段发生内部异常：{str(e)}"

    # 7. 基于 Command 的动态微循环重载
    return Command(
        update={
            "completed_tasks": [next_task.task_id],
            "task_results": {next_task.task_id: tool_output_string},
            "execution_step_count": execution_step_count + 1
        },
        goto="executor_node"
    )



# ==========================================
# 审查者节点初始化
# ==========================================
# 复用 planner_llm 的配置（低温度保证逻辑严密），绑定 ReviewResult 结构化输出
critic_llm = planner_llm.with_structured_output(ReviewResult)

# ==========================================
# 合规审查者节点 (Critic Node)
# ==========================================
def critic_node(state: AgentState) -> Command:
    print("\n⚖️ [Critic] -> 启动政务合规与逻辑审查...")

    task_results = state.get("task_results", {})
    current_loops = state.get("plan_loop_count", 0)
    MAX_ALLOWABLE_LOOPS = 3  # 最多允许打回重试 3 次

    # ---------------------------------------------------------
    # 防线一：业务优雅降级 (Soft Fallback) - 拦截无限死循环
    # 对应 PDF 第 13-14 页深度工程实践
    # ---------------------------------------------------------
    if current_loops > MAX_ALLOWABLE_LOOPS:
        print("   ⚠️ [Critic 降级] 达到最大打回次数，触发业务软着陆。")
        fallback_warning = (
            "【系统高级警报】经过多次深度检索分析，由于本地政务知识库未覆盖匹配文件，"
            "系统无法完全构建具备红头文件支撑的合规报告。为保证响应时效，"
            "以下为基于视觉诊断与大模型预训练数据生成的降级参考方案，请务必安排人工复核："
        )
        # 过滤掉状态重置的占位符
        draft = "\n".join([f"【任务 {k}】: {v}" for k, v in task_results.items() if k != "__RESET__"])
        
        # 强制流转至 Finalizer 输出阶段，中止无意义的死循环
        return Command(
            update={"messages": [("ai", f"{fallback_warning}\n\n{draft}")]},
            goto="finalizer_node"
        )

    # ---------------------------------------------------------
    # 防线二：承接 Executor 抛出的拓扑死锁异常
    # ---------------------------------------------------------
    if "__SYSTEM_DEADLOCK__" in task_results:
        print("   ❌ [Critic 拦截] 检测到执行器依赖死锁，强制打回重构计划。")
        deadlock_msg = task_results["__SYSTEM_DEADLOCK__"]
        reflection_log = f"【系统架构驳回】 你的上一次计划导致了底层执行器死锁。错误详情：{deadlock_msg}。请重新审视 context_needed 依赖关系，生成无环且连贯的新计划。"
        
        return Command(
            update={"reflections": [reflection_log]},
            goto="planner_node"
        )

    # ---------------------------------------------------------
    # 核心审查逻辑：聚合数据并进行政务合规判断
    # ---------------------------------------------------------
    # 将所有的碎片化执行结果进行格式化拼接
    draft_content = "\n\n".join([f"【任务 {k} 执行汇报】:\n{v}" for k, v in task_results.items() if k != "__RESET__"])
    if not draft_content.strip():
        draft_content = "无任何有效执行数据。"

    # 构建严格的审查 Prompt (复刻 PDF 第 10-11 页的红线准则)
    critic_prompt = f"""
你现在担任省级林草综合防护体系的高级合规监察专员。
你的职责是审查底层子系统汇总提交上来的异常事件处理草稿，判断其是否具备成为正式公文的资格。

【草稿综合内容】：
{draft_content}

【不可逾越的政务审查准则】：
1. 生物学准确性验证：草稿是否明确了具体的病虫害种类或异常隐患状态？
2. 政策红线验证：草稿中是否包含对官方政务 PDF 文件的直接引用（例如明确指出了某某条例、防治指导意见、或安全操作规范）？

【裁决逻辑】：
- 如果草稿仅仅提供了通用的大语言模型建议（如“建议喷洒农药”），而没有任何来自本地知识库的具体政策法规名称与条款作为支撑，你必须判定为违规（is_compliant=False）！
- 如果违规，在 critique 中严厉指出草稿中缺失了哪方面的政策依据，并给出来源于政务视角的详细修正建议。
- 如果合规（is_compliant=True），在 critique 中简要总结其合规依据。
"""

    # 启动审查推理
    try:
        review: ReviewResult = critic_llm.invoke([("system", critic_prompt)])
    except Exception as e:
        print(f"   ⚠️ [Critic 异常] 审查模型调用失败: {e}，触发安全重试。")
        # 如果审查本身崩溃，视同打回，逼迫 Planner 重新生成可能更短的数据
        return Command(
            update={"reflections": [f"【审查系统异常】 审查过程发生崩溃: {str(e)}。请检查输出数据结构并重试。"]},
            goto="planner_node"
        )

    # ---------------------------------------------------------
    # 动态路由分发 (Command API)
    # ---------------------------------------------------------
    if review.is_compliant:
        print("   ✅ [Critic 裁决] 合规审查通过！移交报告生成节点。")
        return Command(
            update={"messages": [("ai", f"【合规审查通过】\n最终汇总材料如下:\n{draft_content}")]},
            goto="finalizer_node"
        )
    else:
        print(f"   ❌ [Critic 裁决] 审查未通过，打回重做！\n   -> 反思意见: {review.critique}")
        # 启动 Reflexion 宏循环，驳回修改请求
        reflection_log = f"【合规审查被驳回】 驳回原因及强制修改指令: {review.critique}"
        return Command(
            update={
                "reflections": [reflection_log] # 追加历史记录，化作 Planner 下一次的“血泪教训”
            },
            goto="planner_node" # 返回原点，逼迫规划者重新分解任务并调取知识库
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
    
    # 提取 Critic 节点传递过来的合规材料（或降级警告材料）
    approved_data = state["messages"][-1].content

    prompt = f"""你是一位省级林业局的资深公文笔杆子。
请根据以下经过合规审查的【基础材料】，撰写一份正式的《林草异常诊断与应急处置权威报告》。

【撰写要求】：
1. 格式规范：必须包含标题、事件概述、诊断结论、政策依据、处置建议等标准公文模块。
2. 语气风格：严肃、客观、专业，符合政府公文行文规范。
3. 事实红线：必须绝对忠实于基础材料，严禁捏造材料中未提及的病害名称或政策条款！如果材料中包含【系统高级警报】等降级提示，请在报告开头以“红色预警”形式显著标出。

【基础材料】：
{approved_data}
"""
    
    try:
        response = finalizer_llm.invoke([("user", prompt)])
        final_report = response.content
        print("   ✅ [Finalizer] 政务公文报告生成完毕！")
    except Exception as e:
        print(f"   ❌ [Finalizer 异常] 报告生成失败: {e}")
        final_report = f"报告生成发生异常: {str(e)}\n\n原始数据备份:\n{approved_data}"

    # 抵达终点，结束图的流转
    return Command(
        update={"messages": [("ai", final_report)]},
        goto=END
    )