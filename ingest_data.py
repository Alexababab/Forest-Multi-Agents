import os
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class KnowledgeBaseBuilder:
    def __init__(self):
        # 1. 初始化 Markdown 智能切分器 (严格按照政务层级)
        self.headers_to_split_on = [
            ("#", "一级标题_章"),
            ("##", "二级标题_节"),
            ("###", "三级标题_条"),
            ("####", "四级标题_项")
        ]
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False # 保留原标题文本
        )

        # 2. 初始化本地 Embedding 模型 (召唤 4070 算力)
        print("🚀 正在加载 BGE 中文向量模型到显存...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-zh-v1.5", 
            model_kwargs={'device': 'cuda'},     # 核心：强制指派给显卡运行
            encode_kwargs={'normalize_embeddings': True} # 余弦相似度必须归一化
        )
        print("✅ 向量模型加载完毕！")

        # 指定数据库持久化路径
        self.db_dir = "database/chroma_db"

    def ingest_markdown(self, md_path: str, source_name: str):
        """将 Markdown 文本切块并存入向量数据库"""
        if not os.path.exists(md_path):
            raise FileNotFoundError(f"找不到 Markdown 文件: {md_path}")
            
        print(f"\n📖 正在读取: {md_path}")
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        # 3. 智能切片
        docs = self.md_splitter.split_text(md_text)
        
        # 注入基础元数据
        for doc in docs:
            doc.metadata["source"] = source_name
            # 清理可能的首尾空白
            doc.page_content = doc.page_content.strip()
            
        print(f"✂️ 成功将文档智能切分为 {len(docs)} 个语义块。")
        
        # 4. 存入 ChromaDB
        print("💾 正在计算向量并写入本地 ChromaDB 数据库...")
        # from_documents 第一次运行会在指定文件夹创建 SQLite 数据库文件
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        print(f"🎉 入库成功！数据库保存在: {self.db_dir}")
        
        return vectorstore

# ==========================================
# 自动化测试与检索验证
# ==========================================
if __name__ == "__main__":
    # 你刚才生成的那个 Markdown 文件路径
    md_file = "database/raw_pdfs/test_marker_output.md"
    
    builder = KnowledgeBaseBuilder()
    
    try:
        # 1. 执行入库
        vectorstore = builder.ingest_markdown(md_file, source_name="松材线虫病防治技术方案(2022)")
        
        # 2. 激动人心的时刻：立刻进行一次本地检索测试！
        print("\n" + "="*50)
        print("🔍 开始极速检索测试 (模拟 Agent 查阅资料)")
        
        # 我们故意问一个藏在附录表格里的刁钻问题，考验系统！
        query = "无人机多光谱遥感监测时，航向的最低重叠度要求是多少？"
        print(f"❓ 提问: {query}")
        
        # k=2 表示只召回最相似的 2 个段落
        results = vectorstore.similarity_search(query, k=2) 
        
        for i, res in enumerate(results):
            print(f"\n[召回结果 {i+1}]")
            print(f"📑 元数据 (Metadata): {res.metadata}")
            print(f"📄 内容片段:\n{res.page_content[:300]}...") # 打印前300字看看
            
        print("="*50)

    except Exception as e:
        print(f"❌ 运行报错: {e}")