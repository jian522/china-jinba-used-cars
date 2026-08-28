/**
 * Cloudflare Worker for WeChat AI Assistant
 * 
 * Deploy to: https://workers.cloudflare.com
 * 
 * Required Variables:
 * - DEEPSEEK_API_KEY: Your DeepSeek API key
 */

const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

const SYSTEM_PROMPT = `你是 Jinba Auto Export 的 AI 助手。Jinba Auto Export 是一家专注于中国二手车出口的公司。

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

用中文回答，保持专业友好。`;

export default {
  async fetch(request, env, ctx) {
    // Handle CORS
    const headers = {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers });
    }

    // Handle chat endpoint
    if (request.method === 'POST' && request.url.includes('/api/chat')) {
      try {
        const body = await request.json();
        const { message, history = [] } = body;

        if (!message) {
          return Response.json({ error: 'Message is required' }, { status: 400, headers });
        }

        // Build messages array
        const messages = [
          { role: 'system', content: SYSTEM_PROMPT },
          ...history.slice(-10),
          { role: 'user', content: message }
        ];

        // Call DeepSeek API
        const response = await fetch(DEEPSEEK_API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${env.DEEPSEEK_API_KEY}`,
          },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages,
            max_tokens: 500,
            temperature: 0.7,
          }),
        });

        const data = await response.json();
        
        if (data.choices && data.choices[0]) {
          return Response.json({ reply: data.choices[0].message.content }, { headers });
        } else {
          return Response.json({ 
            reply: '抱歉，我遇到了一些问题。请直接联系我们的销售团队：WhatsApp +86 180 7908 9999' 
          }, { headers });
        }
      } catch (error) {
        return Response.json({ 
          error: error.message,
          reply: '抱歉，服务暂时不可用。请联系：WhatsApp +86 180 7908 9999'
        }, { status: 500, headers });
      }
    }

    // Handle simple echo for testing
    if (request.method === 'GET') {
      return Response.json({ 
        status: 'ok',
        message: 'AI Chat API is running',
        endpoints: ['/api/chat']
      }, { headers });
    }

    return Response.json({ error: 'Not found' }, { status: 404, headers });
  }
};
