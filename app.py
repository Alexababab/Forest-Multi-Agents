import streamlit as st
import os
from langchain_core.messages import HumanMessage

# 严格从你的后端文件导入编译好的图
from graph import forestry_app

# ==========================================
# 1. 页面配置与侧边栏
# ==========================================
st.set_page_config(page_title="林草调度中心", page_icon="🌲", layout="wide")

with st.sidebar:
    st.header("📊 图状态监控")
    loop_val = st.empty()
    step_val = st.empty()
    loop_val.metric("规划循环次数 (Loop)", 0)
    step_val.metric("底层执行步数 (Step)", 0)

    st.markdown("---")
    # 增加一个清空历史记录的实用按钮
    if st.button("🗑️ 清空历史对话"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 2. 主界面：流转控制 & 历史回显
# ==========================================
st.title("🌲 林草综合防护多智能体系统")

# ✨ 核心 1：初始化 session_state 缓存机制
if "messages" not in st.session_state:
    st.session_state.messages = []

# ✨ 核心 2：渲染历史对话记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # 渲染文字内容
        if msg.get("content"):
            st.markdown(msg["content"])
        # 如果历史记录中有图片，一并渲染出来
        if msg.get("image_path") and os.path.exists(msg["image_path"]):
            st.image(msg["image_path"], width=300)

# 多模态聊天输入框
prompt = st.chat_input(
    "请输入您的信息并上传现场照片（支持 jpg/png/jpeg 格式）",
    accept_file=True,
    file_type=["jpg", "png", "jpeg"]
)

# ==========================================
# 3. 处理新的一轮对话
# ==========================================
if prompt:
    user_input = prompt.text
    uploaded_files = prompt.files
    image_path = ""

    # 处理图片保存
    if uploaded_files:
        uploaded_file = uploaded_files[0]
        os.makedirs("./tests", exist_ok=True)
        image_path = f"./tests/{uploaded_file.name}"
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    # ✨ 核心 3：将用户的新输入保存到历史记录中
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "image_path": image_path
    })

    # 在界面上立即渲染刚刚发送的用户消息
    with st.chat_message("user"):
        if user_input:
            st.write(user_input)
        if image_path:
            st.image(image_path, caption="📸 已上传的现场侦测图像", width=300)

    # 构造传给图引擎的初始消息 (仅限当前轮次，防止污染后端推理)
    if image_path:
        content_str = f"{user_input}\n【系统提示：现场图片路径为 {image_path}】"
    else:
        content_str = user_input

    initial_state = {
        "messages": [HumanMessage(content=content_str)],
        "plan_loop_count": 0,
        "execution_step_count": 0,
        "completed_tasks": ["__RESET__"],
        "task_results": {"__RESET__": "__RESET__"},
        "reflections": ["__RESET__"]
    }

    final_report = ""

    # ==========================================
    # 4. 动态流转解析 (在 Assistant 气泡中展示)
    # ==========================================
    with st.chat_message("assistant"):
        with st.status("🔍 智能体正在协同推理中...", expanded=True) as status:
            try:
                for event in forestry_app.stream(initial_state, config={"recursion_limit": 30}):

                    # --- 🧠 Planner ---
                    if "planner_node" in event:
                        data = event["planner_node"]
                        if not data: continue

                        st.markdown("#### 🧠 规划者 (Planner) 构建执行树")
                        loop_val.metric("规划循环次数 (Loop)", data.get("plan_loop_count", 0))

                        if data.get("plan"):
                            for s in data["plan"].steps:
                                st.write(f"- 📍 **{s.task_id}**: {s.task_name} `[{s.tool_required}]`")

                    # --- ⚙️ Executor ---
                    elif "executor_node" in event:
                        data = event["executor_node"]
                        if not data: continue

                        step_val.metric("底层执行步数 (Step)", data.get("execution_step_count", 0))

                        results = data.get("task_results", {})
                        completed = data.get("completed_tasks", [])
                        valid_tasks = [t for t in completed if t != "__RESET__"]

                        if valid_tasks:
                            last_task = valid_tasks[-1]
                            with st.expander(f"⚙️ 底层工具执行完毕: {last_task}", expanded=False):
                                st.info(results.get(last_task, "无结果返回"))

                    # --- ⚖️ Critic ---
                    elif "critic_node" in event:
                        data = event["critic_node"]
                        if not data: continue

                        reflections = data.get("reflections", [])
                        valid_refs = [r for r in reflections if r != "__RESET__"]

                        if valid_refs:
                            st.error(f"⚖️ **[政务合规审查驳回]**\n\n{valid_refs[-1]}")
                            st.warning("🔄 触发 Reflexion 机制，系统正在自动打回给 Planner 重构任务...")
                        else:
                            st.success("⚖️ **[审查通过]** 政策匹配无误，进入公文生成阶段。")

                    # --- 📝 Finalizer ---
                    elif "finalizer_node" in event:
                        data = event["finalizer_node"]
                        if not data: continue

                        status.update(label="✅ 推理彻底闭环，公文生成完毕", state="complete", expanded=False)
                        msg = data["messages"][-1]
                        final_report = msg.content if hasattr(msg, "content") else msg[1]

            except Exception as e:
                status.update(label="❌ 系统遭遇异常", state="error", expanded=True)
                st.error(f"图引擎运行崩溃: {str(e)}")

        # ==========================================
        # 5. 渲染公文并缓存历史
        # ==========================================
        if final_report:
            st.markdown("### 📄 林草异常诊断与应急处置权威报告")
            with st.container(border=True):
                st.markdown(final_report)

            # ✨ 核心 4：将大模型生成的最终报告追加到历史记录中
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"### 📄 林草异常诊断与应急处置权威报告\n\n{final_report}"
            })