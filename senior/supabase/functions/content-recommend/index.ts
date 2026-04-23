// 个性化内容推荐 Edge Function
// 基于用户偏好、情感状态、历史行为推荐个性化内容

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
    const { userId, contentType, emotionState, limit = 10 } = await req.json();

    if (!userId) {
      return new Response(
        JSON.stringify({ error: { code: 'MISSING_USER_ID', message: '缺少用户ID' } }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !supabaseKey) {
      return new Response(
        JSON.stringify({ error: { code: 'CONFIG_ERROR', message: '服务配置错误' } }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 构建查询条件
    let query = `${supabaseUrl}/rest/v1/content_library?`;
    
    if (contentType && contentType !== 'all') {
      query += `content_type=eq.${contentType}&`;
    }

    // 根据情感状态过滤内容
    if (emotionState) {
      if (emotionState === 'sad' || emotionState === 'anxious') {
        query += `emotional_tone=in.(uplifting,comforting,peaceful)&`;
      } else if (emotionState === 'happy') {
        query += `emotional_tone=in.(joyful,energetic,inspiring)&`;
      }
    }

    query += `order=rating.desc,view_count.desc&limit=${limit}`;

    const contentsResponse = await fetch(query, {
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'apikey': supabaseKey
      }
    });

    if (!contentsResponse.ok) {
      throw new Error('获取内容失败');
    }

    let contents = await contentsResponse.json();

    // 如果结果太少，放宽条件再查询
    if (contents.length < 5) {
      const fallbackQuery = `${supabaseUrl}/rest/v1/content_library?${contentType && contentType !== 'all' ? `content_type=eq.${contentType}&` : ''}order=rating.desc&limit=${limit}`;
      
      const fallbackResponse = await fetch(fallbackQuery, {
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'apikey': supabaseKey
        }
      });

      if (fallbackResponse.ok) {
        contents = await fallbackResponse.json();
      }
    }

    // 使用AI生成推荐理由
    const apiKey = Deno.env.get('ALIBABA_CLOUD_API_KEY') || Deno.env.get('DASHSCOPE_API_KEY');
    
    if (apiKey && contents.length > 0) {
      // 为前3个内容生成推荐理由
      const topContents = contents.slice(0, 3);
      
      for (const content of topContents) {
        const prompt = `为老年人推荐以下内容，生成一句温暖的推荐语（20字以内）：
内容类型：${content.content_type}
标题：${content.title}
描述：${content.description || ''}
${emotionState ? `用户当前情绪：${emotionState}` : ''}

只输出推荐语，不要其他内容。`;

        try {
          const aiResponse = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${apiKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              model: 'qwen-plus',
              messages: [{ role: 'user', content: prompt }],
              temperature: 0.8,
              max_tokens: 50
            })
          });

          if (aiResponse.ok) {
            const aiData = await aiResponse.json();
            content.recommendReason = aiData.choices[0]?.message?.content || '为您精心推荐';
          }
        } catch (error) {
          console.error('生成推荐理由失败:', error);
          content.recommendReason = '为您精心推荐';
        }
      }
    }

    return new Response(
      JSON.stringify({
        data: {
          contents: contents,
          totalCount: contents.length,
          recommendedAt: new Date().toISOString()
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('content-recommend错误:', error);
    return new Response(
      JSON.stringify({ 
        error: { 
          code: 'RECOMMEND_ERROR', 
          message: error.message || '内容推荐失败' 
        } 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
