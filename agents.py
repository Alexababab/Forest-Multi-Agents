import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import tools_list

load_dotenv()

# 初始化大模型并绑定工具
llm_deep = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.1
)
llm_with_tools = llm_deep.bind_tools(tools_list)

def decision_agent(state: dict) -> dict:
    """对应你截图中的 llm_node"""
    print("\n=> [决策大脑] 正在审视全局上下文，推理下一步操作...")
    
    # 1. 从状态中提取消息列表
    messages = state.get("messages", [])
    
    # 2. 构建 Prompt 模板（完美契合你的习惯，并修复了历史消息注入问题）
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        你是国家林业局病虫害多智能体诊断系统的总指挥。
        第一步：检测到用户图片或描述后，调用 vision_expert_tool 提取病害名称。
        第二步：拿到病害名称后，调用 knowledge_expert_tool 查阅防治方案。
        第三步：综合所有工具返回的信息，撰写最终的 Markdown 诊断报告。
        绝不允许产生幻觉编造数据。
        """),
        # 核心：使用 MessagesPlaceholder 完整、无损地将历史消息列表注入进模板
        MessagesPlaceholder(variable_name="messages")
    ])
    
    # 3. 组装 Chain (你的习惯用法)
    chain = prompt | llm_with_tools
    
    # 4. 执行 Chain
    response = chain.invoke({"messages": messages})
    
    # 5. 返回更新（利用 Annotated[list, add] 的特性，只需返回增量）
    return {"messages": [response]}