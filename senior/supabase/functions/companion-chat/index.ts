// 智能对话生成和陪伴聊天 Edge Function
// 集成阿里云通义千问API，提供温暖的情感陪伴对话

Deno.serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders, status: 200 });
  }

  try {
    const { userInput, conversationContext, userId, emotionState } = await req.json();

    if (!userInput || !userId) {
      return new Response(
        JSON.stringify({ error: { code: 'MISSING_PARAMS', message: '缺少必要参数' } }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 获取阿里云API Key
    const apiKey = Deno.env.get('ALIBABA_CLOUD_API_KEY') || Deno.env.get('DASHSCOPE_API_KEY');
    if (!apiKey) {
      return new Response(
        JSON.stringify({ error: { code: 'NO_API_KEY', message: '未配置API密钥' } }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 构建对话上下文
    const messages = [];
    
    // 系统提示词 - 温暖的陪伴型AI
    const systemPrompt = `你是一个温暖、善解人意的AI陪伴助手，专门为老年人提供情感支持和陪伴。你的特点：
1. 说话温柔亲切，像家人朋友一样关心老人
2. 善于倾听，给予情感支持和积极鼓励
3. 使用简单易懂的语言，避免复杂术语
4. 关心老人的日常生活、健康状况和心情
5. 适时提供健康建议、生活小贴士
6. 营造轻松愉快的对话氛围
${emotionState ? `\n当前用户情绪状态：${emotionState}，请根据情绪给予适当的关怀和支持。` : ''}`;

    messages.push({
      role: 'system',
      content: systemPrompt
    });

    // 添加对话历史（最多保留最近5轮）
    if (conversationContext && Array.isArray(conversationContext)) {
      const recentContext = conversationContext.slice(-5);
      recentContext.forEach((ctx: any) => {
        if (ctx.user) messages.push({ role: 'user', content: ctx.user });
        if (ctx.assistant) messages.push({ role: 'assistant', content: ctx.assistant });
      });
    }

    // 添加当前用户输入
    messages.push({
      role: 'user',
      content: userInput
    });

    // 调用阿里云通义千问API
    const aiResponse = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'qwen-plus',
        messages: messages,
        temperature: 0.8,
        max_tokens: 500
      })
    });

    if (!aiResponse.ok) {
      const errorText = await aiResponse.text();
      console.error('阿里云API错误:', errorText);
      return new Response(
        JSON.stringify({ error: { code: 'AI_API_ERROR', message: 'AI服务调用失败' } }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const aiData = await aiResponse.json();
    const aiReply = aiData.choices[0]?.message?.content || '抱歉，我现在有点累了，稍后再聊好吗？';

    // 情感检测（简单关键词匹配）
    let emotionDetected = 'neutral';
    let emotionScore = 0.5;

    const sadKeywords = ['难过', '伤心', '孤独', '想念', '寂寞', '痛苦', '不开心'];
    const happyKeywords = ['开心', '高兴', '快乐', '幸福', '愉快', '满意', '舒服'];
    const anxiousKeywords = ['担心', '焦虑', '害怕', '紧张', '不安', '恐惧'];
    const angryKeywords = ['生气', '愤怒', '烦躁', '讨厌', '恼火'];

    const inputLower = userInput.toLowerCase();
    if (sadKeywords.some(kw => inputLower.includes(kw))) {
      emotionDetected = 'sad';
      emotionScore = 0.7;
    } else if (happyKeywords.some(kw => inputLower.includes(kw))) {
      emotionDetected = 'happy';
      emotionScore = 0.8;
    } else if (anxiousKeywords.some(kw => inputLower.includes(kw))) {
      emotionDetected = 'anxious';
      emotionScore = 0.6;
    } else if (angryKeywords.some(kw => inputLower.includes(kw))) {
      emotionDetected = 'angry';
      emotionScore = 0.7;
    }

    // 保存对话记录到数据库
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (supabaseUrl && supabaseKey) {
      const saveResponse = await fetch(`${supabaseUrl}/rest/v1/voice_interactions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'apikey': supabaseKey,
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal'
        },
        body: JSON.stringify({
          user_id: userId,
          interaction_type: 'text',
          user_input: userInput,
          ai_response: aiReply,
          emotion_detected: emotionDetected,
          emotion_score: emotionScore,
          conversation_context: conversationContext || []
        })
      });

      if (!saveResponse.ok) {
        console.error('保存对话记录失败:', await saveResponse.text());
      }
    }

    return new Response(
      JSON.stringify({
        data: {
          reply: aiReply,
          emotionDetected: emotionDetected,
          emotionScore: emotionScore,
          timestamp: new Date().toISOString()
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('companion-chat错误:', error);
    return new Response(
      JSON.stringify({ 
        error: { 
          code: 'INTERNAL_ERROR', 
          message: error.message || '服务器内部错误' 
        } 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
