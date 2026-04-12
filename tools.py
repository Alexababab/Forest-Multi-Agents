import os
import base64
import requests
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 辅助函数：将本地图片转为 Base64 编码
def encode_image_to_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"图片读取报错: {e}")
        return ""

# ==========================================
# 全局初始化：知识库组件 (避免每次调用工具时重复加载)
# ==========================================
print("⚙️ [系统初始化] 正在加载本地知识库与向量检索组件到显存...")
try:
    _embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-zh-v1.5", 
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'normalize_embeddings': True}
    )
    # 绑定我们在 ingest_data.py 中生成的数据库目录
    _vectorstore = Chroma(
        persist_directory="database/chroma_db",
        embedding_function=_embeddings
    )
    print("✅ 知识库加载完成！")
except Exception as e:
    print(f"❌ 知识库加载失败，请检查模型路径或依赖: {e}")
    _vectorstore = None

@tool
def vision_expert_tool(image_path: str) -> str:
    """视觉专家工具：当你需要分析图片、识别树木病害时，必须严格调用此工具。
    参数 image_path: 图片的本地文件绝对路径或相对路径。
    返回: 识别出的树木病害名称及基础诊断结果。
    """
    print(f"\n   👁️ [真实视觉执行] -> 正在通过智谱 API 底层请求分析图片: {image_path}")
    
    # 1. 检查图片并转码
    if not os.path.exists(image_path):
        return f"视觉分析失败：找不到图片路径 {image_path}，请提醒用户提供正确的图片路径。"
        
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return "视觉分析失败：图片读取错误。"

    # 2. 从环境变量获取 API Key
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return "视觉分析失败：未配置 ZHIPU_API_KEY 环境变量。"

    # 3. 完美复刻你的 curl 调用（构造 Headers 和 Payload）
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4v-flash",  # 使用多模态视觉模型
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "你是一位国家级林业病理学专家。请仔细分析这张图片，识别图中的树木得了什么病（例如是否为松材线虫病、美国白蛾等）。请给出明确的【病害名称】和【视觉诊断依据】。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "stream": False,
        "temperature": 0.1
    }
    
    # 4. 发起 HTTP POST 请求
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status() # 检查 HTTP 状态码
        
        # 5. 解析返回的 JSON 数据
        result_json = response.json()
        diagnosis_text = result_json["choices"][0]["message"]["content"]
        
        print("   ✅ [视觉分析完成] -> 成功获取智谱底层 API 响应")
        return diagnosis_text
        
    except requests.exceptions.RequestException as e:
        return f"视觉API(HTTP)调用失败，网络或请求错误：{str(e)}"
    except KeyError:
        return f"视觉API(HTTP)解析失败，返回的数据格式不符合预期：{response.text}"

# ==========================================
# 知识库工具 (保持现状)
# ==========================================
@tool
def knowledge_expert_tool(disease_name: str) -> str:
    """知识库专家工具：当你已经明确获取了具体的病害名称，需要查阅国家官方红头文件和防治方案时，必须调用此工具。
    参数 disease_name: 具体的病害名称。
    返回: 官方防控制度原文摘要和处置指导。
    """
    print(f"\n   ⚙️ [知识库执行] -> 正在从 ChromaDB 检索关于【{disease_name}】的官方档案...")
    
    if _vectorstore is None:
        return "本地知识库未正确初始化，无法执行检索。"

    try:
        # 1. 构造检索 Query（适当增加上下文词汇以提升召回率）
        query = f"{disease_name} 的诊断标准、防治技术方案、无人机监测要求及处置指导"
        
        # 2. 执行向量相似度检索 (召回 Top 3 相关片段)
        results = _vectorstore.similarity_search(query, k=3)
        
        if not results:
            return f"未能在官方数据库中检索到关于【{disease_name}】的规定。"
        
        # 3. 组装返回给 Agent 的上下文
        response_text = f"以下是关于【{disease_name}】的官方文件检索结果：\n\n"
        for i, doc in enumerate(results):
            # 获取元数据中的来源信息，如果不存在则为'未知'
            source = doc.metadata.get('source', '未知文件')
            chapter = doc.metadata.get('chapter', '')
            
            response_text += f"--- 来源 {i+1}: {source} {chapter} ---\n"
            response_text += f"{doc.page_content}\n\n"
            
        print("   ✅ [知识库检索完成] -> 成功提取相关政务片段")
        return response_text
        
    except Exception as e:
        return f"知识库检索发生异常: {str(e)}"

# 导出工具列表
tools_list = [vision_expert_tool, knowledge_expert_tool]