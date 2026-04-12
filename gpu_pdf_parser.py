import os
import json

# 针对 Marker 1.x 最新版本的全新 API 导入方式
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# 设置环境变量，提示底层的 Surya OCR 引擎主要处理中文，大幅提升准确率
os.environ["DEFAULT_LANG"] = "Chinese"

class GpuMarkerParser:
    def __init__(self):
        print("🚀 [Marker 初始化] 正在将深度学习视觉模型加载到 RTX 4070 显存中...")
        print("⏳ (首次运行会自动下载 Surya 布局模型、OCR 模型等，可能需要几分钟到几十分钟)")
        
        # 1. 自动加载当前环境所需的所有视觉、布局、OCR 模型字典
        self.model_dict = create_model_dict()
        
        # 2. 将模型字典挂载到 PDF 转换器引擎上
        self.converter = PdfConverter(artifact_dict=self.model_dict)
        print("✅ 模型加载完毕！显存已预热。")

    def parse_pdf(self, pdf_path: str, output_md_path: str):
        """
        使用 Marker 将 PDF 转化为极高质量的 Markdown
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"找不到文件: {pdf_path}")

        print(f"\n📄 开始解析: {pdf_path}")
        print("🔍 正在进行页面布局分析、表格结构推断与文字 OCR...")

        try:
            # 3. 核心大模型推理执行：让显卡去读 PDF
            rendered = self.converter(pdf_path)
            
            # 4. 从渲染对象中剥离出纯 Markdown 文本
            full_text, _, images = text_from_rendered(rendered)

            # 写入 Markdown 内容
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            print(f"🎉 解析大功告成！")
            print(f"📝 Markdown 已保存至: {output_md_path}")
            print(f"📊 解析耗时预估: RTX 4070 应该在几秒内搞定单页！")

        except Exception as e:
            print(f"❌ 解析过程中发生严重错误: {e}")

# ==========================================
# 本地运行测试
# ==========================================
if __name__ == "__main__":
    # 请确保 database/raw_pdfs/ 下有你的 test.pdf
    test_pdf_file = "database/raw_pdfs/test.pdf" 
    output_markdown_file = "database/raw_pdfs/test_marker_output.md"

    # 初始化解析器 (这里会占用显存)
    parser = GpuMarkerParser()
    
    # 执行解析
    parser.parse_pdf(test_pdf_file, output_markdown_file)