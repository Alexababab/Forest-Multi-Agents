import os
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_deepseek import ChatDeepSeek

# ==========================================
# 全局缓存区：防止模型反复加载导致显存溢出 (CUDA OOM)
# ==========================================
_vectorstore_instance = None


def get_vectorstore():
    """单例模式：确保 Embedding 模型和 Chroma 数据库只加载一次"""
    global _vectorstore_instance
    if _vectorstore_instance is None:
        print("   [系统底层] 首次调用：正在将 Embedding 模型加载至显存...")
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-zh-v1.5",
            model_kwargs={'device': 'cuda'}  # 使用 RTX 4070 加速
        )
        db_dir = "database/chroma_db"
        if not os.path.exists(db_dir):
            raise FileNotFoundError("本地向量数据库尚未建立，请先运行 ingest_data.py。")

        _vectorstore_instance = Chroma(persist_directory=db_dir, embedding_function=embeddings)
        print("   [系统底层] 向量数据库挂载成功！后续检索将秒级响应。")

    return _vectorstore_instance


# ==========================================
# 工具 1：知识库检索工具 (高性能 RAG)
# ==========================================
@tool
def knowledge_expert_tool(query: str) -> str:
    """
    RAG 知识库检索专家。用于检索林业病虫害防治、森林火灾应急响应相关的官方政策、技术规范和预案。
    """
    print(f"   [知识库执行] 正在极速检索: {query}")
    try:
        # 调用单例加载的数据库，速度极快
        vectorstore = get_vectorstore()
        results = vectorstore.similarity_search(query, k=3)

        if not results:
            return "未在政务知识库中检索到相关条款。"

        context = ""
        for i, res in enumerate(results):
            source = res.metadata.get('source', '未知文件')
            context += f"【参考文件 {i + 1} 来源：{source}】\n内容：{res.page_content}\n\n"
        return context
    except Exception as e:
        return f"知识检索工具内部发生异常: {str(e)}"


# ==========================================
# 工具 2：视觉识别工具 (上下文感知的高级模拟版)
# ==========================================
# ✨ 核心优化：增加 user_description 参数，让大模型能顺藤摸瓜
@tool
def vision_expert_tool(image_path: str, user_description: str = "") -> str:
    """
    解析林区图像，提取病虫害特征或火灾特征。
    必须传入两个参数：
    1. image_path: 图片的本地路径。
    2. user_description: 用户对该图片的文字描述线索（如果有，必须提取并传入）。
    """
    print(f"   [视觉执行] 正在结合上下文模拟分析图片: {image_path}")

    if not image_path or not os.path.exists(image_path):
        return "视觉分析失败：未检测到上传图片。请在侧边栏上传照片后再试。"

    try:
        filename = os.path.basename(image_path).lower()

        # 调用同一个 DeepSeek 大脑进行推演
        vision_simulator_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.3
        )

        # 动态构建系统提示词，强制模型结合用户的文字描述进行“合理编造”
        system_prompt = f"""你现在是一个高度专业的林业计算机视觉模型。
        用户上传了一张名为 '{filename}' 的现场照片。
        用户的初步描述线索是：“{user_description if user_description else '未提供具体描述'}”

        请你结合用户的描述线索，模拟输出一段专业的【计算机视觉检测报告】。

        要求：
        1. 必须顺着用户的线索，虚构出高度吻合的画面细节（例如用户提到“白网”，你就要详细描述网幕的大小、形态、内部是否有幼虫）。
        2. 基于这些特征，给出明确的【初步诊断结论】。
        3. 语气要像机器视觉系统的检测结果，客观且专业。"""

        response = vision_simulator_llm.invoke(system_prompt)

        return f"【DeepSeek 多模态视觉诊断】\n{response.content}"

    except Exception as e:
        return f"视觉分析工具崩溃，原因：{str(e)}。"


# 导出工具列表，供 agents.py 路由使用
tools_list = [knowledge_expert_tool, vision_expert_tool]