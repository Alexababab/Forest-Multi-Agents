import re
import fitz  # PyMuPDF 库，读取 PDF 速度极快且排版保留较好
from langchain_core.documents import Document

class LegalDocumentChunker:
    def __init__(self):
        # 魔法在这里：使用正则表达式精准捕捉红头文件的层级结构
        # 匹配 "第一章"、"第二章" 等
        self.chapter_pattern = re.compile(r'^(第[一二三四五六七八九十百]+章\s+.*)', re.MULTILINE)
        # 匹配 "第一条"、"第二条" 等
        self.article_pattern = re.compile(r'^(第[一二三四五六七八九十百]+条\s+.*)', re.MULTILINE)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从 PDF 中提取纯文本，并做基础清理"""
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        # 清理多余的空白符和换行，防止切块正则失效
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        return full_text

    def split_into_chunks(self, text: str, source_metadata: dict) -> list[Document]:
        """将全文本按照 '章' 和 '条' 切分为 Document 对象集合"""
        chunks = []
        
        # 1. 先按“章”切分
        chapters = self.chapter_pattern.split(text)
        current_chapter = "未命名章节"
        
        # chapter_pattern.split 会产生 [内容, 章标题, 内容, 章标题...] 的结构
        for i in range(1, len(chapters), 2):
            current_chapter = chapters[i].strip()
            chapter_content = chapters[i+1]
            
            # 2. 在每一章内，按“条”切分
            articles = self.article_pattern.split(chapter_content)
            
            # 如果这一章里面没有“条”（比如引言），就把它整体作为一个 Chunk
            if len(articles) == 1 and articles[0].strip():
                metadata = {**source_metadata, "chapter": current_chapter, "article": "引言/概述"}
                chunks.append(Document(page_content=articles[0].strip(), metadata=metadata))
                continue
                
            # 正常按“条”组装 Chunk
            for j in range(1, len(articles), 2):
                current_article = articles[j].strip()
                article_content = articles[j+1].strip()
                
                # 将“条”的标题和具体内容合并，这就是一个完整的语义块
                chunk_content = f"{current_article}\n{article_content}"
                
                if chunk_content:
                    # 组装超级元数据（Metadata），这是解决政策冲突消解的关键！
                    metadata = {
                        **source_metadata,
                        "chapter": current_chapter,
                        "article": current_article
                    }
                    chunks.append(Document(page_content=chunk_content, metadata=metadata))
                    
        return chunks

# ==========================================
# 本地单测区（可以直接运行本文件测试切块效果）
# ==========================================
if __name__ == "__main__":
    # 模拟测试：请确保 database/raw_pdfs/ 下有一份测试 PDF
    test_pdf = "database/raw_pdfs/test.pdf" 
    
    # 模拟一份基础元数据
    sample_metadata = {
        "source": "松材线虫病防治技术方案.pdf",
        "administrative_level": "国家级", # 用于后续“知识域上浮”的权限判定
        "domain": "病害防治",
        "year": 2022
    }
    
    chunker = LegalDocumentChunker()
    
    try:
        raw_text = chunker.extract_text_from_pdf(test_pdf)
        documents = chunker.split_into_chunks(raw_text, sample_metadata)
        
        print(f"✅ 成功将 PDF 切分为 {len(documents)} 个政务语义块！\n")
        
        # 打印前两个切块看看效果
        for i, doc in enumerate(documents[:2]):
            print(f"--- Chunk {i+1} ---")
            print(f"元数据 (Metadata): {doc.metadata}")
            print(f"内容摘要: {doc.page_content[:150]}...\n")
            
    except Exception as e:
        print(f"测试失败，请确保 PDF 路径正确。错误信息: {e}")