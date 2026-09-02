"""
Simple chat API for WeChat integration
Run with: python -m http.server 8000
Or deploy as a Cloudflare Worker / Vercel function
"""
import json
import os
from pathlib import Path

# Configuration
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
API_URL = 'https://api.deepseek.com/chat/completions'

def get_ai_response(message, history=None):
    """Get AI response from DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        return "API key not configured. Please set DEEPSEEK_API_KEY environment variable."
    
    messages = []
    if history:
        messages.extend(history[-10:])  # Last 10 messages
    
    messages.append({"role": "user", "content": message})
    
    # System prompt
    system_prompt = """你是 Jinba Auto Export 的 AI 助手。Jinba Auto Export 是一家专注于中国二手车出口的公司。
    
    公司信息：
    - 名称：Jinba Auto Export (金巴汽车出口)
    - 主营：中国二手车出口
    - 品牌：BYD, Chery, Haval, MG 等
    - 联系：jian5222@gmail.com, WhatsApp: +86 180 7908 9999
    - 地址：中国江西省新余市
    - 网站：https://jinbacars.com
    
    你可以帮忙：
    1. 介绍出口流程
    2. 回答车辆相关问题
    3. 提供联系方式
    4. 解释价格和付款方式
    
    用中文回答，保持专业友好。"""
    
    messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        import urllib.request
        import urllib.error
        
        data = json.dumps({
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }).encode('utf-8')
        
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
            
    except Exception as e:
        return f"抱歉，我遇到了一些问题：{str(e)}\n\n请直接联系我们的销售团队：WhatsApp +86 180 7908 9999"

def handle_chat(request_body):
    """Handle chat request"""
    try:
        body = json.loads(request_body)
        message = body.get('message', '')
        history = body.get('history', [])
        
        if not message:
            return {"error": "Message is required"}, 400
        
        reply = get_ai_response(message, history)
        return {"reply": reply}, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

# For testing
if __name__ == '__main__':
    print("Chat API ready!")
    print("To use with web interface, deploy this as:")
    print("1. Cloudflare Worker")
    print("2. Vercel Function")
    print("3. Railway App")
    print("4. Or use local server for testing")
