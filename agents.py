import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import tools_list

# ==========================================
# 步骤 1：环境与模型初始化
# ==========================================
# 加载 .env 文件中的机密环境变量
load_dotenv()
if os.getenv('DEEPSEEK_API_KEY') is None:
    raise ValueError("❌ DEEPSEEK_API_KEY 环境变量未设置，请检查 .env 文件！")

# 全局只初始化一次模型！使用官方专属接口，原生支持 Tool Calling 和 Pydantic
llm_deep = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.1 
)

# 核心步骤：把 tools.py 里的工具列表“绑”在大脑上
llm_with_tools = llm_deep.bind_tools(tools_list)

# ==========================================
# 步骤 2：编写总指挥的 System Prompt
# ==========================================
system_prompt = """你是一位国家级林草综合防护与应急响应多智能体系统的【总指挥中枢】。
你的职责是：接收前线的林业异常情况报告，并通过调度专业工具来完成精准诊断和出具处置方案。

【严格的工作流规范】：
1. 当用户提供图片线索时，你必须优先调用 `vision_expert_tool` 识别具体的树木病害名称。
2. 明确病害名称后，你必须继续调用 `knowledge_expert_tool` 查阅国家官方的处置标准和防控制度。
3. 综合视觉诊断和知识库的权威数据，向用户输出一份结构清晰、权威严谨的最终处置报告。

【纪律要求】：
- 保持客观理性，注重逻辑分析，减少无意义的寒暄。
- 绝对不要捏造政策或凭空诊断，所有结论必须基于工具返回的真实数据！
"""

# 将系统提示词和 LangGraph 传来的历史消息组装起来
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    # 占位符，用于接收图流转过程中产生的全部对话历史（包含工具的返回结果）
    MessagesPlaceholder(variable_name="messages"),
])

# 将 Prompt 和 挂载了工具的大模型串联成一个执行链
agent_runnable = prompt | llm_with_tools

# ==========================================
# 步骤 3：暴露给 LangGraph 调用的节点函数
# ==========================================
def decision_agent(state: dict):
    print("\n🧠 [决策中枢] -> 正在阅读当前状态，思考下一步行动...")
    
    # 拿到最新的流转状态（messages列表）喂给大模型
    response = agent_runnable.invoke({"messages": state["messages"]})
    
    # 返回的内容（一个 AIMessage 对象，包含文本或 tool_calls）
    # 会被 LangGraph 自动 append 到全局的 messages 列表中
    return {"messages": [response]}