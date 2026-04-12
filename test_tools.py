import os
# 导入我们刚刚编写好的工具
from tools import vision_expert_tool, knowledge_expert_tool

def run_vision_test():
    print("\n" + "="*50)
    print("▶️ 开始测试: 视觉专家工具 (Vision API)")
    print("="*50)
    
    # ⚠️ 请确保你的本地确实有这张图片，或者修改为你的真实图片路径
    test_image_path = "database/raw_pdfs/test.jpg" 
    
    if not os.path.exists(test_image_path):
        print(f"❌ 测试阻断: 找不到图片文件 {test_image_path}")
        print("请在对应目录放入一张树木照片用于测试。")
        return

    # 检查环境变量
    if not os.getenv("ZHIPU_API_KEY"):
        print("⚠️ 警告: 未检测到 ZHIPU_API_KEY 环境变量，API 调用可能会失败。")

    try:
        # LangChain 工具的标准调用语法：使用 .invoke() 并传入参数字典
        result = vision_expert_tool.invoke({"image_path": test_image_path})
        print("\n[视觉工具返回结果]:")
        print(result)
    except Exception as e:
        print(f"\n❌ 视觉工具测试抛出异常: {e}")

def run_rag_test():
    print("\n" + "="*50)
    print("▶️ 开始测试: 知识库 RAG 工具 (ChromaDB + BGE)")
    print("="*50)
    
    # 我们用一个确定的关键词测试向量检索召回能力
    test_disease_name = "松材线虫病"
    
    try:
        result = knowledge_expert_tool.invoke({"disease_name": test_disease_name})
        print("\n[知识库检索返回结果]:")
        print(result)
    except Exception as e:
        print(f"\n❌ 知识库测试抛出异常: {e}")

if __name__ == "__main__":
    # 执行测试集
    run_vision_test()
    run_rag_test()