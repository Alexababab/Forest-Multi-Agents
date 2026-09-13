import os
import base64
from openai import OpenAI
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

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
def retrieve_knowledge(query: str) -> list:
    """
    底层 RAG 检索 helper：一次相似度检索，返回结构化结果（供 provenance 使用）。
    只记录数据库真实提供的信息（source + 标题层级 + page_content + distance），
    绝不人为制造 page / chunk_id / document UUID。
    """
    vectorstore = get_vectorstore()
    scored_results = vectorstore.similarity_search_with_score(query, k=3)
    docs = []
    for rank, (doc, distance) in enumerate(scored_results, start=1):
        item = {
            "content": doc.page_content,
            "source": (doc.metadata or {}).get("source", ""),
            "metadata": dict(doc.metadata or {}),
            "rank": rank,
            "raw_score": float(distance),
            "score_semantics": "distance",
        }
        docs.append(item)
    return docs


def _format_knowledge_text(docs: list) -> str:
    """将结构化检索结果格式化为给 LLM 阅读的文本（与 V1 输出格式保持一致）。"""
    if not docs:
        return "未在政务知识库中检索到相关条款。"
    context = ""
    for item in docs:
        source = item.get("source") or "未知文件"
        context += f"【参考文件 {item['rank']} 来源：{source}】\n内容：{item['content']}\n\n"
    return context


@tool(response_format="content_and_artifact")
def knowledge_expert_tool(query: str):
    """
    RAG 知识库检索专家。用于检索林业病虫害防治、森林火灾应急响应相关的官方政策、技术规范和预案。
    """
    print(f"   [知识库执行] 正在极速检索: {query}")
    try:
        docs = retrieve_knowledge(query)
        if not isinstance(docs, list):
            raise TypeError("检索结果不是文档列表")
        formatted_text = _format_knowledge_text(docs)
        if docs:
            return formatted_text, {"status": "success", "documents": docs}
        return formatted_text, {"status": "empty", "documents": []}
    except Exception as e:
        print(f"   [知识库执行异常] {type(e).__name__}: {e}")
        return (
            "知识检索暂时不可用，未能完成本次检索。",
            {"status": "error", "error_type": "retrieval_error"},
        )


# ==========================================
# 工具 2：视觉识别工具 (Qwen-VL-Plus 真实多模态 API)
# ==========================================
@tool(response_format="content_and_artifact")
def vision_expert_tool(image_path: str, user_description: str = ""):
    """
    解析林区图像，提取病虫害特征或火灾特征。
    必须传入两个参数：
    1. image_path: 图片的本地路径。
    2. user_description: 用户对该图片的文字描述线索（如果有，必须提取并传入）。
    """
    print(f"   [视觉执行] 正在调用 Qwen-VL-Plus 分析图片: {image_path}")

    if not image_path or not os.path.exists(image_path):
        return (
            "视觉分析失败：未检测到上传图片。请在侧边栏上传照片后再试。",
            {"status": "error", "error_type": "image_not_found"},
        )

    try:
        # 1. 读取图片并 Base64 编码
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # 2. 根据文件扩展名匹配 MIME 类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        # 3. 构建 Qwen-VL-Plus 分析提示词
        analysis_prompt = f"""你是一位资深的林业病虫害计算机视觉识别专家。请仔细观察这张现场照片，结合以下线索进行专业分析。

【用户提供的线索】：{user_description if user_description else '未提供具体文字描述'}

请按以下格式输出专业视觉检测报告：
1. **图像可见特征**：详细描述观察到的颜色、形态、纹理、分布范围等
2. **初步诊断结论**：基于图像特征，判断可能的病虫害类型或异常状态
3. **置信度评估**：对诊断结论的确定程度（高/中/低），并说明依据
4. **建议**：如需进一步确认，建议补充哪些信息或采取什么措施

注意：只描述你实际在图像中观察到的内容，不要编造不存在的细节。"""

        # 4. 调用 Qwen-VL-Plus API（OpenAI 兼容模式）
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    },
                    {"type": "text", "text": analysis_prompt},
                ],
            }],
        )

        result = completion.choices[0].message.content
        if not isinstance(result, str) or not result.strip():
            print("   [视觉执行异常] Qwen-VL-Plus 返回空内容")
            return (
                "视觉分析未返回有效结果，请稍后重试。",
                {"status": "error", "error_type": "empty_vision_response"},
            )
        print(f"   [视觉执行] Qwen-VL-Plus 分析完成")
        return (
            f"【Qwen-VL-Plus 多模态视觉诊断】\n{result}",
            {
                "status": "success",
                "evidence": {
                    "image_path": image_path,
                    "user_description": user_description,
                },
            },
        )

    except Exception as e:
        print(f"   [视觉执行异常] {type(e).__name__}: {e}")
        return (
            "视觉分析服务暂时不可用，未能完成本次图像分析。",
            {"status": "error", "error_type": "vision_api_error"},
        )


# 导出工具列表，供 agents.py 路由使用
tools_list = [knowledge_expert_tool, vision_expert_tool]
