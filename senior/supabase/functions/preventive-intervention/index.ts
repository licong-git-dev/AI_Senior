import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface InterventionRequest {
  userId: string;
  interventionType: string;
  priority: 'urgent' | 'routine' | 'follow_up';
  contextData: Record<string, any>;
}

interface UserProfile {
  id: string;
  user_id: string;
  age: number;
  gender: string;
  height?: number;
  weight?: number;
  medical_history: any;
  current_medications: any;
  lifestyle_data: any;
  preferences: any;
}

interface HealthData {
  id: string;
  user_id: string;
  record_type: string;
  record_value: any;
  recorded_at: string;
}

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
  }

  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const requestData: InterventionRequest = await req.json();
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    );

    // 1. 获取用户画像和健康数据
    const { data: userProfile, error: profileError } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', requestData.userId)
      .single();

    if (profileError) {
      throw new Error(`获取用户画像失败: ${profileError.message}`);
    }

    const { data: healthData, error: healthError } = await supabase
      .from('health_records')
      .select('*')
      .eq('user_id', requestData.userId)
      .order('recorded_at', { ascending: false })
      .limit(30);

    if (healthError) {
      throw new Error(`获取健康数据失败: ${healthError.message}`);
    }

    // 2. 风险评估分析
    const riskAssessment = await performRiskAssessment(userProfile, healthData || []);
    
    // 3. 生成个性化建议
    const personalizedAdvice = await generateQianwenAdvice(
      requestData.interventionType,
      riskAssessment,
      userProfile
    );

    // 4. 存储干预记录
    const { data: interventionRecord, error: insertError } = await supabase
      .from('intervention_records')
      .insert({
        user_id: requestData.userId,
        intervention_type: requestData.interventionType,
        priority: requestData.priority,
        generated_advice: personalizedAdvice,
        risk_assessment: riskAssessment,
        status: 'active'
      })
      .select()
      .single();

    if (insertError) {
      throw new Error(`存储干预记录失败: ${insertError.message}`);
    }

    // 5. 创建多模态内容
    const multiModalContent = await generateMultiModalContent(personalizedAdvice);

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          interventionRecord,
          personalizedAdvice,
          multiModalContent,
          nextSteps: generateNextSteps(riskAssessment)
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('预防性干预处理错误:', error);
    
    return new Response(
      JSON.stringify({ 
        error: {
          code: 'INTERVENTION_ERROR',
          message: error.message || '处理干预请求时发生未知错误'
        }
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});

// 风险评估函数
async function performRiskAssessment(userProfile: UserProfile, healthData: HealthData[]) {
  const riskFactors: any[] = [];
  let overallRisk = 0;
  
  // 基于年龄的风险评估
  if (userProfile.age >= 65) {
    riskFactors.push({
      type: 'age_related',
      description: '高龄风险',
      severity: userProfile.age >= 75 ? 3 : 2,
      score: userProfile.age >= 75 ? 0.8 : 0.6
    });
    overallRisk += userProfile.age >= 75 ? 0.8 : 0.6;
  }

  // 基于BMI的风险评估
  if (userProfile.height && userProfile.weight) {
    const bmi = userProfile.weight / ((userProfile.height / 100) ** 2);
    if (bmi >= 30) {
      riskFactors.push({
        type: 'obesity',
        description: '肥胖相关风险',
        severity: 3,
        score: 0.7
      });
      overallRisk += 0.7;
    } else if (bmi >= 25) {
      riskFactors.push({
        type: 'overweight',
        description: '超重风险',
        severity: 2,
        score: 0.4
      });
      overallRisk += 0.4;
    }
  }

  // 基于健康记录的风险评估
  const recentRecords = healthData.slice(0, 7); // 最近7天数据
  const bloodPressureRecords = recentRecords.filter(r => r.record_type === 'blood_pressure');
  const bloodSugarRecords = recentRecords.filter(r => r.record_type === 'blood_sugar');

  if (bloodPressureRecords.length > 0) {
    const avgSystolic = bloodPressureRecords.reduce((sum, r) => sum + (r.record_value?.systolic || 0), 0) / bloodPressureRecords.length;
    if (avgSystolic >= 140) {
      riskFactors.push({
        type: 'hypertension',
        description: '高血压风险',
        severity: 3,
        score: 0.8
      });
      overallRisk += 0.8;
    }
  }

  if (bloodSugarRecords.length > 0) {
    const avgGlucose = bloodSugarRecords.reduce((sum, r) => sum + (r.record_value?.glucose || 0), 0) / bloodSugarRecords.length;
    if (avgGlucose >= 7.0) {
      riskFactors.push({
        type: 'diabetes',
        description: '糖尿病风险',
        severity: 3,
        score: 0.7
      });
      overallRisk += 0.7;
    }
  }

  // 基于既往病史的风险评估
  if (userProfile.medical_history) {
    const conditions = userProfile.medical_history.conditions || [];
    if (conditions.includes('heart_disease')) {
      riskFactors.push({
        type: 'cardiovascular',
        description: '心血管疾病风险',
        severity: 3,
        score: 0.9
      });
      overallRisk += 0.9;
    }
  }

  // 计算总体风险等级
  let riskLevel = 'low';
  if (overallRisk >= 2.0) {
    riskLevel = 'critical';
  } else if (overallRisk >= 1.5) {
    riskLevel = 'high';
  } else if (overallRisk >= 0.8) {
    riskLevel = 'medium';
  }

  return {
    overallRisk,
    riskLevel,
    riskFactors,
    confidence: Math.min(0.95, 0.6 + (riskFactors.length * 0.1)),
    recommendations: generateRiskBasedRecommendations(riskFactors, riskLevel)
  };
}

// 基于风险生成建议
function generateRiskBasedRecommendations(riskFactors: any[], riskLevel: string) {
  const recommendations: any[] = [];
  
  if (riskLevel === 'critical' || riskLevel === 'high') {
    recommendations.push({
      priority: 'urgent',
      category: 'medical_consultation',
      title: '建议立即就医',
      description: '您的健康风险较高，建议尽快咨询专业医生',
      actions: ['预约医生', '准备既往病历', '记录症状变化']
    });
  }

  riskFactors.forEach(factor => {
    switch (factor.type) {
      case 'hypertension':
        recommendations.push({
          priority: 'high',
          category: 'lifestyle_modification',
          title: '血压管理',
          description: '通过饮食和运动控制血压',
          actions: ['限制盐分摄入', '规律运动', '定期监测血压']
        });
        break;
      case 'diabetes':
        recommendations.push({
          priority: 'high',
          category: 'dietary_management',
          title: '血糖控制',
          description: '调整饮食结构，控制血糖水平',
          actions: ['控制碳水化合物', '增加纤维摄入', '定时用餐']
        });
        break;
      case 'obesity':
        recommendations.push({
          priority: 'medium',
          category: 'weight_management',
          title: '体重控制',
          description: '通过运动和饮食控制体重',
          actions: ['制定运动计划', '控制饮食热量', '定期测量体重']
        });
        break;
    }
  });

  return recommendations;
}

// 通义千问建议生成
async function generateQianwenAdvice(
  interventionType: string,
  riskAssessment: any,
  userProfile: UserProfile
) {
  const prompt = buildQianwenPrompt(interventionType, riskAssessment, userProfile);
  
  try {
    const qianwenResponse = await fetch('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('QIANWEN_API_KEY')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'qwen-max',
        input: {
          prompt: prompt
        },
        parameters: {
          max_tokens: 2000,
          temperature: 0.7,
          top_p: 0.8
        }
      })
    });

    if (!qianwenResponse.ok) {
      throw new Error(`通义千问API调用失败: ${qianwenResponse.status}`);
    }

    const result = await qianwenResponse.json();
    
    if (!result.output || !result.output.text) {
      throw new Error('通义千问API返回数据格式错误');
    }

    return {
      content: result.output.text,
      metadata: {
        model: 'qwen-max',
        generatedAt: new Date().toISOString(),
        confidence: riskAssessment.confidence
      }
    };
    
  } catch (error) {
    console.error('通义千问API调用失败:', error);
    // 返回默认建议
    return generateDefaultAdvice(interventionType, riskAssessment);
  }
}

// 构建通义千问提示词
function buildQianwenPrompt(interventionType: string, riskAssessment: any, userProfile: UserProfile) {
  return `
角色：你是一位资深的预防医学专家和老年健康顾问，拥有20年的临床经验。

任务：为用户生成个性化的健康预防建议和干预方案。

用户基本信息：
- 年龄：${userProfile.age}岁
- 性别：${userProfile.gender}
- 身高：${userProfile.height ? userProfile.height + 'cm' : '未知'}
- 体重：${userProfile.weight ? userProfile.weight + 'kg' : '未知'}
- 既往病史：${JSON.stringify(userProfile.medical_history)}
- 当前用药：${JSON.stringify(userProfile.current_medications)}
- 生活方式：${JSON.stringify(userProfile.lifestyle_data)}
- 个人偏好：${JSON.stringify(userProfile.preferences)}

风险评估结果：
- 总体风险等级：${riskAssessment.riskLevel}
- 风险评分：${riskAssessment.overallRisk.toFixed(2)}
- 主要风险因素：${riskAssessment.riskFactors.map((f: any) => f.description).join(', ')}
- 建议优先级：${riskAssessment.recommendations.map((r: any) => r.priority).join(', ')}

干预类型：${interventionType}

请生成包含以下内容的详细建议：

## 1. 风险因素分析
- 详细解释当前存在的健康风险
- 评估风险的可控程度
- 说明预防的重要性

## 2. 分级建议
### 立即行动建议（1-7天内执行）
- 具体可操作的第一步行动
- 紧急情况的应对措施

### 短期目标（1-4周内）
- 可衡量的健康改善目标
- 渐进式实施计划

### 长期计划（3-6个月）
- 持续的健康管理策略
- 生活方式改变的维持方法

## 3. 具体行动步骤
### 日常管理
- 每日需要执行的具体行动
- 监测指标和方法

### 饮食建议
- 推荐的食材和营养搭配
- 需要避免的食物

### 运动计划
- 适合的运动类型和强度
- 运动频率和持续时间

### 用药管理
- 用药时间和注意事项
- 与医生的沟通要点

## 4. 预期效果和监测指标
- 执行建议后预期出现的改善
- 需要重点监测的健康指标
- 什么情况下需要调整方案

## 5. 安全注意事项
- 哪些情况需要立即停止当前行动
- 出现异常症状时的处理方法
- 什么情况下需要紧急就医

## 6. 自我激励和支持
- 建立健康习惯的心理技巧
- 寻求家人朋友支持的方法
- 记录进展的有效方式

要求：
1. 语言通俗易懂，避免过于复杂的医学术语
2. 建议具体可操作，考虑老年人的身体特点
3. 提供多种选择方案，适应不同情况
4. 语气关怀温暖，体现专业和关爱
5. 总字数控制在1500-2000字
`;
}

// 生成默认建议（当API调用失败时）
function generateDefaultAdvice(interventionType: string, riskAssessment: any) {
  const riskLevel = riskAssessment.riskLevel;
  let defaultAdvice = '';

  if (riskLevel === 'critical' || riskLevel === 'high') {
    defaultAdvice = `
# 紧急健康建议

基于您的风险评估，建议您立即采取以下行动：

## 立即行动
1. **预约医生**：尽快咨询专业医生，进行全面健康检查
2. **准备资料**：整理既往病史、用药清单、检查报告
3. **症状监测**：密切观察身体变化，记录异常症状

## 短期目标（2周内）
1. **完善检查**：按照医生建议完成必要的医学检查
2. **调整用药**：根据医嘱优化用药方案
3. **生活方式调整**：开始实施基础的健康习惯改变

## 长期管理（3-6个月）
1. **定期随访**：建立规律的医疗随访机制
2. **持续监测**：建立健康数据监测记录
3. **家庭支持**：动员家庭成员参与健康管理

## 每日行动清单
- 按时服药
- 测量血压（如有需要）
- 记录身体状况
- 适度运动
- 均衡饮食
- 充足休息

如出现胸痛、呼吸困难、严重头晕等症状，请立即就医。
`;
  } else if (riskLevel === 'medium') {
    defaultAdvice = `
# 健康改善建议

根据您的健康状况，以下是一些改善建议：

## 生活方式优化
1. **规律运动**：每天至少30分钟中等强度运动
2. **均衡饮食**：多蔬菜水果，少油少盐
3. **充足睡眠**：保证每天7-8小时睡眠
4. **定期体检**：每半年进行一次健康检查

## 具体行动计划
### 第1-2周：建立基础习惯
- 设定固定的运动时间
- 调整饮食结构
- 建立睡眠规律

### 第3-4周：强化健康行为
- 增加运动强度
- 优化饮食搭配
- 学习压力管理技巧

### 长期维持（3个月以上）
- 持续健康生活方式
- 定期健康评估
- 根据效果调整计划

## 监测指标
- 体重变化
- 血压水平
- 睡眠质量
- 整体精神状态

建议您记录每日健康数据，定期评估改善效果。
`;
  } else {
    defaultAdvice = `
# 预防性健康建议

恭喜！您的健康状况良好，建议继续保持并进一步优化：

## 健康维持策略
1. **预防为主**：定期体检，及早发现潜在问题
2. **均衡生活**：保持工作与休息的平衡
3. **积极社交**：维持良好的人际关系
4. **持续学习**：保持大脑活跃，预防认知衰退

## 建议活动
- 规律的有氧运动（如快走、游泳）
- 力量训练（每周2-3次）
- 脑力活动（阅读、益智游戏）
- 社交活动（与朋友聚会、社区活动）

## 健康生活方式
- 饮食多样化，营养均衡
- 充足睡眠，质量良好
- 压力管理，心理健康
- 戒烟限酒，远离不良习惯

定期关注健康变化，及时调整生活方式。如有任何健康疑虑，建议咨询医生。
`;
  }

  return {
    content: defaultAdvice.trim(),
    metadata: {
      model: 'default-fallback',
      generatedAt: new Date().toISOString(),
      confidence: 0.6,
      isDefault: true
    }
  };
}

// 生成多模态内容
async function generateMultiModalContent(personalizedAdvice: any) {
  const content = personalizedAdvice.content;
  
  try {
    // 这里可以调用多模态内容生成服务
    // 目前返回基础的多模态内容结构
    
    const multiModalContent = {
      images: [], // 将包含解释性图片
      audio: null, // 将包含语音播报
      video: null, // 将包含演示视频
      interactive: null, // 将包含互动内容
      textFormatted: formatContentForDisplay(content)
    };

    return multiModalContent;
  } catch (error) {
    console.error('多模态内容生成失败:', error);
    return {
      images: [],
      audio: null,
      video: null,
      interactive: null,
      textFormatted: content
    };
  }
}

// 格式化内容用于展示
function formatContentForDisplay(content: string) {
  // 将markdown格式的内容转换为适合显示的格式
  return content
    .split('\n')
    .map(line => {
      if (line.startsWith('# ')) {
        return { type: 'title', content: line.replace('# ', '') };
      } else if (line.startsWith('## ')) {
        return { type: 'section', content: line.replace('## ', '') };
      } else if (line.startsWith('### ')) {
        return { type: 'subsection', content: line.replace('### ', '') };
      } else if (line.match(/^\d+\./)) {
        return { type: 'listitem', content: line };
      } else if (line.trim()) {
        return { type: 'paragraph', content: line };
      }
      return null;
    })
    .filter(item => item !== null);
}

// 生成后续步骤建议
function generateNextSteps(riskAssessment: any) {
  const nextSteps = [];
  
  // 基于风险等级的建议
  if (riskAssessment.riskLevel === 'critical') {
    nextSteps.push({
      action: '紧急就医',
      timeframe: '立即',
      description: '预约医生进行紧急健康评估'
    });
  }
  
  // 基于具体风险因素的建议
  riskAssessment.riskFactors.forEach((factor: any) => {
    switch (factor.type) {
      case 'hypertension':
        nextSteps.push({
          action: '血压监测',
          timeframe: '每日',
          description: '开始每日血压记录，建立健康档案'
        });
        break;
      case 'diabetes':
        nextSteps.push({
          action: '血糖管理',
          timeframe: '每餐前后',
          description: '注意餐食搭配，控制血糖水平'
        });
        break;
      case 'obesity':
        nextSteps.push({
          action: '体重管理',
          timeframe: '每周',
          description: '制定并执行减重计划'
        });
        break;
    }
  });

  return nextSteps;
}