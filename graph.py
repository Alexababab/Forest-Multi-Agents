from typing import TypedDict, Annotated
from operator import add
from langchain_core.messages import BaseMessage, HumanMessage

from langgraph.graph import StateGraph, START, END
# 核心引入：专门用来处理 tool_calls 的预置节点和路由逻辑
from langgraph.prebuilt import ToolNode, tools_condition

from tools import tools_list
from agents import decision_agent

# ==========================================
# 1. 状态定义 (State)
# ==========================================
class ForestryState(TypedDict):
    messages: Annotated[list[BaseMessage], add]

# ==========================================
# 2. 构建图 (Graph)
# ==========================================
workflow = StateGraph(ForestryState)

# ==========================================
# 3. 注册节点 (Nodes)
# ==========================================
# 决策节点（调用我们刚才写的 decision_agent）
workflow.add_node("agent", decision_agent)

# 工具节点（传入 tools.py 里的 tools_list，它会自动根据 tool_calls 里的 name 去执行对应函数）
tool_executor = ToolNode(tools_list)
workflow.add_node("tools", tool_executor)

# ==========================================
# 4. 连线与路由 (Edges)
# ==========================================
workflow.add_edge(START, "agent")

# 核心路由：这里代替了手工写 if/else 判断 response.tool_calls
# tools_condition 内部逻辑：
# 如果 agent 返回的 AIMessage 中有 tool_calls -> 走向 "tools"
# 如果没有 tool_calls (说明准备输出最终报告了) -> 走向 END
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# 工具执行完毕后，必须把结果还给大脑，形成闭环
workflow.add_edge("tools", "agent")

# ==========================================
# 5. 编译应用
# ==========================================
forestry_app = workflow.compile()

# ==========================================
# 测试运行
# ==========================================
if __name__ == "__main__":
    print("=== 林业多智能体系统启动 ===")
    
    initial_state = {
        "messages": [HumanMessage(content="这是昨天在林区拍到的生病的树木照片，图片路径是 test.jpg ，请给我一份详细的诊断和处置报告。")]
    }
    
    # 逐步流式打印，观察 Agent 如何自主循环
    for event in forestry_app.stream(initial_state):
        for node_name, node_state in event.items():
            print(f"\n✅ [图流转] 节点 '{node_name}' 执行完毕。")
            
            latest_message = node_state["messages"][-1]
            # 这里呼应你的第三张截图：如果有 tool_calls，说明大模型决定用工具了
            if hasattr(latest_message, 'tool_calls') and latest_message.tool_calls:
                print(f"   -> 大脑发出了工具调度指令: {[t['name'] for t in latest_message.tool_calls]}")
            elif latest_message.content:
                print(f"   -> 输出: {latest_message.content[:100]}...")