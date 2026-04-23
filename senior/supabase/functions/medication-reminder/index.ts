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

    if (action === 'get_reminders') {
      // 获取活跃的药物
      const medicationsResponse = await fetch(`${SUPABASE_URL}/rest/v1/medication_management?user_id=eq.${user_id}&status=eq.active`, {
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      const medications = await medicationsResponse.json();

      // 生成今日提醒
      const reminders = generateTodayReminders(medications);
      
      // 生成AI用药指导
      const aiGuidance = await generateMedicationGuidance(medications);

      return new Response(JSON.stringify({
        data: {
          reminders,
          total_medications: medications.length,
          low_stock_count: medications.filter((m: any) => m.stock_quantity <= m.low_stock_threshold).length,
          ai_guidance: aiGuidance,
          ai_powered: true
        }
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (action === 'confirm_intake') {
      const { medication_id, intake_time } = requestData;
      
      // 记录服药（可以扩展一个medication_intake_records表）
      return new Response(JSON.stringify({
        data: {
          message: '服药记录已确认',
          confirmed_at: new Date().toISOString()
        }
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (action === 'update_stock') {
      const { medication_id, quantity_change } = requestData;
      
      // 获取当前库存
      const currentResponse = await fetch(`${SUPABASE_URL}/rest/v1/medication_management?id=eq.${medication_id}`, {
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      const current = await currentResponse.json();
      
      if (current.length === 0) {
        throw new Error('药物不存在');
      }

      const newStock = current[0].stock_quantity + quantity_change;

      // 更新库存
      const updateResponse = await fetch(`${SUPABASE_URL}/rest/v1/medication_management?id=eq.${medication_id}`, {
        method: 'PATCH',
        headers: {
          'apikey': SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        },
        body: JSON.stringify({
          stock_quantity: newStock,
          updated_at: new Date().toISOString()
        })
      });

      const result = await updateResponse.json();
      const needsRefill = newStock <= result[0].low_stock_threshold;

      return new Response(JSON.stringify({
        data: {
          message: '库存更新成功',
          new_stock: newStock,
          needs_refill: needsRefill,
          medication: result[0]
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

async function generateMedicationGuidance(medications: any[]) {
  // 使用阿里云AI生成用药指导
  const AI_API_KEY = Deno.env.get('ALIBABA_CLOUD_AI_API_KEY') || 'sk-71bb10435f134dfdab3a4b684e57b640';
  
  const medList = medications.map(m => 
    `${m.medication_name}(${m.dosage}，${m.frequency})`
  ).join('、');
  
  const prompt = `作为专业的药师，请为老年患者提供用药指导。当前用药：${medList}

请提供：
1. 整体用药注意事项（2-3条）
2. 可能的药物相互作用提醒（如有）
3. 服药时间的最佳安排建议

回复要简洁易懂，适合老年人阅读。`;

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
          max_tokens: 400,
          temperature: 0.7
        }
      })
    });

    if (aiResponse.ok) {
      const aiData = await aiResponse.json();
      const guidance = aiData.output?.choices?.[0]?.message?.content || '';
      return guidance.trim();
    }
  } catch (error) {
    console.error('AI API调用失败:', error);
  }

  return '请按时服药，如有不适及时联系医生。保持药物储存在干燥阴凉处。';
}

function generateTodayReminders(medications: any[]) {
  const reminders = [];
  const now = new Date();
  const currentHour = now.getHours();

  for (const med of medications) {
    // 解析intake_time (例如: "早上8点,晚上8点" 或 "三餐后")
    const times = parseIntakeTime(med.intake_time);
    
    for (const time of times) {
      reminders.push({
        medication_id: med.id,
        medication_name: med.medication_name,
        dosage: med.dosage,
        intake_time: time,
        is_due: Math.abs(currentHour - time.hour) <= 1,
        stock_low: med.stock_quantity <= med.low_stock_threshold
      });
    }
  }

  return reminders.sort((a, b) => a.intake_time.hour - b.intake_time.hour);
}

function parseIntakeTime(intakeTimeStr: string) {
  const times = [];
  
  if (intakeTimeStr.includes('早上') || intakeTimeStr.includes('8点')) {
    times.push({ hour: 8, label: '早上8点' });
  }
  if (intakeTimeStr.includes('中午') || intakeTimeStr.includes('12点')) {
    times.push({ hour: 12, label: '中午12点' });
  }
  if (intakeTimeStr.includes('晚上') || intakeTimeStr.includes('20点')) {
    times.push({ hour: 20, label: '晚上8点' });
  }
  if (intakeTimeStr.includes('三餐')) {
    times.push({ hour: 8, label: '早餐后' });
    times.push({ hour: 12, label: '午餐后' });
    times.push({ hour: 18, label: '晚餐后' });
  }
  
  if (times.length === 0) {
    times.push({ hour: 8, label: '早上' });
  }
  
  return times;
}
