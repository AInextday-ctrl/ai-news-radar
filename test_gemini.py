"""
Test script to verify Google Gemini API connectivity.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ 未检测到有效的 GEMINI_API_KEY！")
        print("💡 请先在项目根目录的 .env 文件中填入从 https://aistudio.google.com/ 获取的 Key。")
        return False

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    print(f"🔑 正在使用 API Key 测试连接 Google Gemini ({model_name})...")
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents="用中文简短回答一句话：你是谁，你能帮AI资讯雷达网站做什么？"
        )
        print("\n✅ Gemini 响应成功：")
        print("-" * 40)
        print(response.text.strip())
        print("-" * 40)
        return True
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    test_gemini()
