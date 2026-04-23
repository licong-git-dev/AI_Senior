// 情感分析和心理健康评估 Edge Function
// 基于对话历史和行为数据，分析老人的情感状态和心理健康

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
    const { userId, analysisType = 'current' } = await req.json();

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

    // 获取最近7天的对话记录
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const interactionsResponse = await fetch(
      `${supabaseUrl}/rest/v1/voice_interactions?user_id=eq.${userId}&interaction_time=gte.${sevenDaysAgo.toISOString()}&order=interaction_time.desc&limit=50`,
      {
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'apikey': supabaseKey
        }
      }
    );

    if (!interactionsResponse.ok) {
      throw new Error('获取对话记录失败');
    }

    const interactions = await interactionsResponse.json();

    // 统计情感数据
    const emotionStats: any = {
      happy: 0,
      sad: 0,
      anxious: 0,
      angry: 0,
      neutral: 0
    };

    let totalScore = 0;
    let count = 0;

    interactions.forEach((interaction: any) => {
      if (interaction.emotion_detected) {
        emotionStats[interaction.emotion_detected] = (emotionStats[interaction.emotion_detected] || 0) + 1;
      }
      if (interaction.emotion_score) {
        totalScore += parseFloat(interaction.emotion_score);
        count++;
      }
    });

    const avgEmotionScore = count > 0 ? (totalScore / count).toFixed(2) : 0.5;

    // 分析心理状态
    let psychologicalState = 'stable';
    let companionshipNeedLevel = 'moderate';
    let riskLevel = 'low';

    const sadRatio = interactions.length > 0 ? emotionStats.sad / interactions.length : 0;
    const anxiousRatio = interactions.length > 0 ? emotionStats.anxious / interactions.length : 0;

    if (sadRatio > 0.4 || anxiousRatio > 0.3) {
      psychologicalState = 'needs_attention';
      companionshipNeedLevel = 'high';
      riskLevel = 'medium';
    } else if (sadRatio > 0.2 || anxiousRatio > 0.15) {
      psychologicalState = 'somewhat_unstable';
      companionshipNeedLevel = 'moderate_high';
      riskLevel = 'low';
    }

    // 使用AI生成分析报告
    const apiKey = Deno.env.get('ALIBABA_CLOUD_API_KEY') || Deno.env.get('DASHSCOPE_API_KEY');
    let aiAnalysis = '';
    let supportSuggestions = '';

    if (apiKey && interactions.length > 0) {
      const recentDialogues = interactions.slice(0, 10).map((i: any) => 
        `用户：${i.user_input}\nAI：${i.ai_response}\n情绪：${i.emotion_detected || '未知'}`
      ).join('\n\n');

      const prompt = `作为心理健康专家，分析以下老年人最近的对话记录和情感数据：

对话记录（最近10条）：
${recentDialogues}

情感统计：
- 开心：${emotionStats.happy}次
- 伤心：${emotionStats.sad}次
- 焦虑：${emotionStats.anxious}次
- 愤怒：${emotionStats.angry}次
- 平静：${emotionStats.neutral}次

请提供：
1. 心理健康分析（100字以内）
2. 陪伴建议（3-5条具体建议）

格式：
分析：[你的分析]
建议：
1. [建议1]
2. [建议2]
3. [建议3]`;

      const aiResponse = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'qwen-plus',
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          max_tokens: 500
        })
      });

      if (aiResponse.ok) {
        const aiData = await aiResponse.json();
        const aiReply = aiData.choices[0]?.message?.content || '';
        
        // 解析AI回复
        const analysisPart = aiReply.match(/分析[：:]([\s\S]*?)(?=建议|$)/);
        const suggestionsPart = aiReply.match(/建议[：:]([\s\S]*)/);
        
        aiAnalysis = analysisPart ? analysisPart[1].trim() : '情绪状态基本稳定，需要持续关注';
        supportSuggestions = suggestionsPart ? suggestionsPart[1].trim() : '定期陪伴聊天，关注情绪变化';
      }
    }

    // 保存情感状态记录
    const emotionStateData = {
      user_id: userId,
      emotion_type: Object.keys(emotionStats).reduce((a, b) => emotionStats[a] > emotionStats[b] ? a : b),
      emotion_intensity: parseFloat(avgEmotionScore),
      trigger_event: `过去7天共${interactions.length}次对话`,
      psychological_state: psychologicalState,
      companionship_need_level: companionshipNeedLevel,
      ai_analysis: aiAnalysis || '基于对话历史的情感分析',
      support_suggestions: supportSuggestions || '保持日常陪伴和关怀'
    };

    const saveResponse = await fetch(`${supabaseUrl}/rest/v1/emotional_states`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'apikey': supabaseKey,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify(emotionStateData)
    });

    if (!saveResponse.ok) {
      console.error('保存情感状态失败:', await saveResponse.text());
    }

    return new Response(
      JSON.stringify({
        data: {
          emotionStats: emotionStats,
          averageEmotionScore: avgEmotionScore,
          psychologicalState: psychologicalState,
          companionshipNeedLevel: companionshipNeedLevel,
          riskLevel: riskLevel,
          interactionCount: interactions.length,
          aiAnalysis: aiAnalysis,
          supportSuggestions: supportSuggestions,
          analyzedAt: new Date().toISOString()
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('emotion-analysis错误:', error);
    return new Response(
      JSON.stringify({ 
        error: { 
          code: 'ANALYSIS_ERROR', 
          message: error.message || '情感分析失败' 
        } 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
