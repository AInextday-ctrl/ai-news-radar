"""
Test script to verify Google Gemini API connectivity.
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ 未检测到有效的 GEMINI_API_KEY！")
        print("💡 请先在项目根目录的 .env 文件中填入从 https://aistudio.google.com/ 获取的 Key。")
        return False

    preferred_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    candidates = [
        preferred_model,
        "gemini-flash-latest",
        "gemini-3.7-flash",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-3.8-flash"
    ]
    # Deduplicate while preserving order
    models_to_try = []
    for m in candidates:
        if m not in models_to_try:
            models_to_try.append(m)

    print(f"🔑 正在使用 API Key 测试连接 Google Gemini (优先: {preferred_model})...")
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        last_error = None
        for m in models_to_try:
            try:
                print(f"  👉 正在尝试调用模型: {m} ...")
                response = client.models.generate_content(
                    model=m,
                    contents="用中文简短回答一句话：你是谁，你能帮AI资讯雷达网站做什么？"
                )
                if response and response.text:
                    print(f"\n✅ Gemini 响应成功 (成功模型: {m})：")
                    print("-" * 40)
                    print(response.text.strip())
                    print("-" * 40)
                    return True
            except Exception as e:
                print(f"     ⚠️ 模型 {m} 暂时不可用: {str(e)[:90]}")
                last_error = e
                continue

        print(f"\n❌ 所有候选模型连接均失败: {last_error}")
        return False
    except Exception as e:
        print(f"\n❌ 初始化客户端失败: {e}")
        return False

if __name__ == "__main__":
    test_gemini()
