# ==========================================
# 文件：graph.py
# 职责：负责 LangGraph 拓扑结构的组装、编译与运行入口
# ==========================================

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

# 导入状态定义
from state import AgentState

# 导入所有独立的智能体节点
from agents import (
    planner_node,
    executor_node,
    critic_node,
    finalizer_node
)

# 业务层已有 Planner/Critic/Executor 边界；该值仅作为异常 runaway 的最后保险。
GRAPH_RECURSION_LIMIT = 64

def build_forestry_graph():
    """
    构建并编译林草综合防护多智能体有向带环图
    """
    print("\n⚙️ [System] 正在装载高阶混合推理架构 (Plan-Execute-Critic) ...")
    
    # 1. 初始化状态图
    workflow = StateGraph(AgentState)

    # 2. 注册所有核心节点
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("critic_node", critic_node)
    workflow.add_node("finalizer_node", finalizer_node)

    # 3. 极简拓扑连线 (基于 Command API 的动态路由架构)
    # 唯一需要静态定义的只有入口边，其余全部由节点内部的 Command(goto=...) 动态接管
    workflow.add_edge(START, "planner_node")

    # 4. 编译图引擎
    app = workflow.compile()
    print("✅ [System] 架构编译完成，系统就绪！")
    
    return app

# 暴露全局单例，供 FastAPI / Streamlit 等外部服务导入
forestry_app = build_forestry_graph()

# ==========================================
# 生产级本地测试运行入口
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🌲 林草综合防护与应急响应多智能体系统 V2 启动")
    print("="*50)
    
    # 模拟巡林员上报的真实多模态场景
    test_input = "这是昨天在林区拍到的生病的树木照片，图片路径是 ./tests/test.jpg ，请给我一份详细的诊断和处置报告。"
    
    # 初始化纯净的全局状态
    initial_state = {
        "messages": [HumanMessage(content=test_input)],
        "plan_loop_count": 0,
        "execution_step_count": 0,
        # 触发 Reducer 的重置机制，确保累加器环境干净
        "completed_tasks": ["__RESET__"],
        "task_results": {"__RESET__": "__RESET__"},
        "reflections": ["__RESET__"],
        "evidences": [],
        "evidence_seq": 0,
        "critic_verdict": None,
        "finalizer_result": None,
    }
    
    # 架构级硬性熔断配置 (对应 PDF 第 13 页)
    config = {
        "recursion_limit": GRAPH_RECURSION_LIMIT
    }
    
    try:
        # 使用 stream 流式输出，监控微循环与宏循环的流转过程
        for event in forestry_app.stream(initial_state, config=config):
            for node_name, node_state in event.items():
                # 节点内部已有详细 print，此处可用于外部日志埋点
                pass
                
        # 提取并打印最终报告
        print("\n\n" + "🌟 "*20)
        print("【系统最终输出公文】")
        print("🌟 "*20)
        
        # 兼容不同版本的 langgraph stream 返回结构提取最终消息
        # --- graph.py 测试运行入口修改 ---
        # 兼容不同版本的 langgraph stream 返回结构提取最终消息
        if "finalizer_node" in event:
            last_msg = event["finalizer_node"]["messages"][-1]
            # 防御性解析：判断是 AIMessage 对象还是原始 Tuple
            report_text = last_msg.content if hasattr(last_msg, "content") else last_msg[1]
            print(report_text)
        else:
            for k, v in event.items():
                if "messages" in v:
                     last_msg = v["messages"][-1]
                     report_text = last_msg.content if hasattr(last_msg, "content") else last_msg[1]
                     print(report_text)
                     
    except Exception as e:
        print(f"\n❌ [系统致命异常] 引擎触发硬性熔断或发生底层崩溃: {e}")
