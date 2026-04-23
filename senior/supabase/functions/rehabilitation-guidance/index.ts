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

    if (action === 'generate_plan') {
      const { condition_type, intensity_preference } = requestData;
      
      // 根据病情生成个性化康复计划（AI增强）
      const plan = await generateRehabilitationPlan(condition_type, intensity_preference);

      // 保存到数据库
      const createResponse = await fetch(`${SUPABASE_URL}/rest/v1/rehabilitation_plans`, {
        method: 'POST',
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        },
        body: JSON.stringify({
          user_id,
          ...plan,
          start_date: new Date().toISOString().split('T')[0],
          status: 'active',
          completion_rate: 0
        })
      });

      const result = await createResponse.json();

      return new Response(JSON.stringify({
        data: {
          message: 'AI个性化康复计划生成成功',
          plan: result[0],
          ai_powered: plan.ai_powered || false
        }
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (action === 'record_session') {
      const { plan_id, duration, completed } = requestData;
      
      // 更新完成率
      const planResponse = await fetch(`${SUPABASE_URL}/rest/v1/rehabilitation_plans?id=eq.${plan_id}`, {
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      const plans = await planResponse.json();
      
      if (plans.length > 0) {
        const plan = plans[0];
        const newCompletionRate = Math.min(100, plan.completion_rate + 5); // 每次训练增加5%

        await fetch(`${SUPABASE_URL}/rest/v1/rehabilitation_plans?id=eq.${plan_id}`, {
          method: 'PATCH',
          headers: {
            'apikey': SERVICE_ROLE_KEY,
            'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            completion_rate: newCompletionRate,
            updated_at: new Date().toISOString()
          })
        });

        return new Response(JSON.stringify({
          data: {
            message: '训练记录已保存',
            new_completion_rate: newCompletionRate,
            encouragement: getEncouragement(newCompletionRate)
          }
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    if (action === 'get_today_exercises') {
      // 获取用户的活跃康复计划
      const plansResponse = await fetch(
        `${SUPABASE_URL}/rest/v1/rehabilitation_plans?user_id=eq.${user_id}&status=eq.active`,
        {
          headers: {
            'apikey': SERVICE_ROLE_KEY,
            'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
            'Content-Type': 'application/json'
          }
        }
      );
      const plans = await plansResponse.json();

      const exercises = plans.map((plan: any) => ({
        plan_id: plan.id,
        exercise_name: plan.plan_name,
        exercise_type: plan.exercise_type,
        duration: plan.duration_minutes,
        intensity: plan.intensity_level,
        instructions: plan.instructions,
        video_url: plan.video_url,
        completion_rate: plan.completion_rate
      }));

      return new Response(JSON.stringify({
        data: {
          exercises,
          total_duration: exercises.reduce((sum: number, e: any) => sum + e.duration, 0)
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

async function generateRehabilitationPlan(conditionType: string, intensity: string, userProfile?: any) {
  // 使用阿里云AI生成个性化康复计划
  const AI_API_KEY = Deno.env.get('ALIBABA_CLOUD_AI_API_KEY') || 'sk-71bb10435f134dfdab3a4b684e57b640';
  
  const prompt = `作为专业的康复治疗师，请为患有${conditionType}的老年患者制定康复计划。

患者情况：
- 慢性病类型：${conditionType}
- 期望强度：${intensity}
- 年龄群体：老年人

请提供：
1. 康复计划名称
2. 运动类型和强度
3. 建议时长和频率
4. 详细的训练指导（3-5条）
5. 注意事项（2-3条）

回复格式：JSON格式，包含plan_name, exercise_type, intensity_level, duration_minutes, frequency_per_week, instructions, precautions字段。`;

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
          temperature: 0.8
        }
      })
    });

    if (aiResponse.ok) {
      const aiData = await aiResponse.json();
      const aiText = aiData.output?.choices?.[0]?.message?.content || '';
      
      // 尝试解析JSON
      try {
        const jsonMatch = aiText.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const aiPlan = JSON.parse(jsonMatch[0]);
          return {
            plan_name: aiPlan.plan_name || `${conditionType}康复计划`,
            exercise_type: aiPlan.exercise_type || '综合训练',
            intensity_level: intensity,
            duration_minutes: aiPlan.duration_minutes || 30,
            frequency_per_week: aiPlan.frequency_per_week || 5,
            instructions: aiPlan.instructions || '循序渐进，量力而行',
            precautions: aiPlan.precautions || '避免过度疲劳',
            ai_powered: true
          };
        }
      } catch (parseError) {
        console.log('AI返回非标准JSON，使用文本提取');
      }
    }
  } catch (error) {
    console.error('AI API调用失败:', error);
  }

  // AI失败时的备选方案
  const plans: any = {
    hypertension: {
      plan_name: '高血压康复计划',
      exercise_type: '有氧运动',
      intensity_level: intensity || 'moderate',
      duration_minutes: 30,
      frequency_per_week: 5,
      instructions: '1. 进行快走或慢跑\n2. 保持心率在最大心率的60-70%\n3. 每周至少5次\n4. 运动前后测量血压',
      precautions: '避免突然用力，感觉不适立即停止'
    },
    diabetes: {
      plan_name: '糖尿病康复计划',
      exercise_type: '综合训练',
      intensity_level: intensity || 'moderate',
      duration_minutes: 40,
      frequency_per_week: 4,
      instructions: '1. 有氧运动20分钟（快走、游泳）\n2. 阻力训练15分钟\n3. 伸展运动5分钟\n4. 运动前后监测血糖',
      precautions: '随身携带糖果，防止低血糖'
    },
    arthritis: {
      plan_name: '关节炎康复计划',
      exercise_type: '关节活动训练',
      intensity_level: intensity || 'low',
      duration_minutes: 25,
      frequency_per_week: 7,
      instructions: '1. 关节活动度训练\n2. 温和的力量训练\n3. 水中运动（如条件允许）\n4. 避免剧烈冲击',
      precautions: '关节疼痛时减少强度，适度休息'
    },
    heart_disease: {
      plan_name: '心脏病康复计划',
      exercise_type: '心脏康复运动',
      intensity_level: 'low',
      duration_minutes: 20,
      frequency_per_week: 3,
      instructions: '1. 低强度有氧运动\n2. 循序渐进增加强度\n3. 监测心率和血压\n4. 避免屏气用力',
      precautions: '必须在医生指导下进行，出现胸闷、气短立即停止'
    }
  };

  return plans[conditionType] || plans['hypertension'];
}

function getEncouragement(completionRate: number) {
  if (completionRate >= 80) {
    return '太棒了！您的坚持会带来显著的健康改善！';
  } else if (completionRate >= 50) {
    return '做得不错！继续保持，您已经完成了一半的目标！';
  } else if (completionRate >= 20) {
    return '很好的开始！每一步都是进步，继续加油！';
  } else {
    return '万事开头难，相信自己，您可以做到！';
  }
}
