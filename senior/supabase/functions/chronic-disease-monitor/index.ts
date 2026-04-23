Deno.serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'false'
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const requestData = await req.json();
    const { user_id, action } = requestData;

    const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
    const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    if (action === 'analyze_risk') {
      // 获取用户慢性病数据
      const conditionsResponse = await fetch(`${SUPABASE_URL}/rest/v1/chronic_conditions?user_id=eq.${user_id}&current_status=eq.active`, {
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      const conditions = await conditionsResponse.json();

      // 获取最近健康数据
      const healthResponse = await fetch(`${SUPABASE_URL}/rest/v1/health_data?user_id=eq.${user_id}&order=recorded_at.desc&limit=30`, {
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      const healthData = await healthResponse.json();

      // 风险评估逻辑
      let riskLevel = 'low';
      const riskFactors = [];

      // 分析血压数据
      const bpData = healthData.filter((d: any) => d.data_type === 'blood_pressure');
      if (bpData.length > 0) {
        const recentBP = bpData[0];
        const systolic = parseInt(recentBP.value.split('/')[0]);
        const diastolic = parseInt(recentBP.value.split('/')[1]);
        
        if (systolic >= 180 || diastolic >= 110) {
          riskLevel = 'high';
          riskFactors.push('血压严重偏高');
        } else if (systolic >= 140 || diastolic >= 90) {
          riskLevel = riskLevel === 'low' ? 'medium' : riskLevel;
          riskFactors.push('血压偏高');
        }
      }

      // 分析血糖数据
      const glucoseData = healthData.filter((d: any) => d.data_type === 'blood_glucose');
      if (glucoseData.length > 0) {
        const recentGlucose = glucoseData[0];
        const glucoseValue = parseFloat(recentGlucose.value);
        
        if (glucoseValue >= 11.1) {
          riskLevel = 'high';
          riskFactors.push('血糖严重偏高');
        } else if (glucoseValue >= 7.0) {
          riskLevel = riskLevel === 'low' ? 'medium' : riskLevel;
          riskFactors.push('血糖偏高');
        }
      }

      // 检查慢性病类型
      const highRiskConditions = ['heart_disease', 'diabetes', 'hypertension'];
      const userHighRiskConditions = conditions.filter((c: any) => 
        highRiskConditions.includes(c.condition_type) && c.severity_level === 'severe'
      );
      
      if (userHighRiskConditions.length > 0) {
        riskLevel = 'high';
        riskFactors.push(`有${userHighRiskConditions.length}个严重慢性病`);
      }

      // 生成AI个性化建议
      const recommendations = await generateRecommendations(riskLevel, riskFactors, conditions, healthData);

      return new Response(JSON.stringify({
        data: {
          risk_level: riskLevel,
          risk_factors: riskFactors,
          conditions_count: conditions.length,
          recommendations,
          needs_attention: riskLevel !== 'low',
          ai_powered: true
        }
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (action === 'update_condition') {
      const { condition_id, updates } = requestData;
      
      const updateResponse = await fetch(`${SUPABASE_URL}/rest/v1/chronic_conditions?id=eq.${condition_id}`, {
        method: 'PATCH',
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        },
        body: JSON.stringify({
          ...updates,
          updated_at: new Date().toISOString()
        })
      });

      const result = await updateResponse.json();

      return new Response(JSON.stringify({
        data: {
          message: '慢性病信息更新成功',
          condition: result[0]
        }
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({
      error: { message: '未知的操作类型' }
    }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    return new Response(JSON.stringify({
      error: {
        code: 'FUNCTION_ERROR',
        message: error.message
      }
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

async function generateRecommendations(riskLevel: string, riskFactors: string[], conditions: any[], healthData: any[]) {
  // 使用阿里云AI生成个性化建议
  const AI_API_KEY = Deno.env.get('ALIBABA_CLOUD_AI_API_KEY') || 'sk-71bb10435f134dfdab3a4b684e57b640';
  
  const prompt = `作为专业的健康管理AI助手，请基于以下老年患者信息提供个性化健康建议：

风险等级：${riskLevel}
风险因素：${riskFactors.join('、')}
慢性病情况：${conditions.map(c => `${c.condition_type}(${c.severity_level})`).join('、')}
最近健康数据数量：${healthData.length}条

请提供3-5条具体的、可操作的健康管理建议，每条建议要简洁明了，适合老年人理解。`;

  try {
    const aiResponse = await fetch('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'qwen-plus',
        input: {
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        },
        parameters: {
          result_format: 'message',
          max_tokens: 500,
          temperature: 0.7
        }
      })
    });

    if (aiResponse.ok) {
      const aiData = await aiResponse.json();
      const aiText = aiData.output?.choices?.[0]?.message?.content || '';
      
      // 解析AI返回的建议
      const recommendations = aiText.split('\n').filter((line: string) => 
        line.trim() && (line.match(/^\d+[\.、]/) || line.includes('建议'))
      ).map((line: string) => line.replace(/^\d+[\.、]\s*/, '').trim());
      
      if (recommendations.length > 0) {
        return recommendations;
      }
    }
  } catch (error) {
    console.error('AI API调用失败:', error);
  }

  // AI失败时的备选建议
  const fallbackRecommendations = [];
  
  if (riskLevel === 'high') {
    fallbackRecommendations.push('建议立即联系医生或就诊');
    fallbackRecommendations.push('密切监测生命体征');
    fallbackRecommendations.push('按时服药，不可擅自停药');
  } else if (riskLevel === 'medium') {
    fallbackRecommendations.push('增加健康监测频率');
    fallbackRecommendations.push('注意饮食控制和适量运动');
    fallbackRecommendations.push('定期复查');
  } else {
    fallbackRecommendations.push('保持良好生活习惯');
    fallbackRecommendations.push('继续坚持健康管理计划');
  }
  
  return fallbackRecommendations;
}
