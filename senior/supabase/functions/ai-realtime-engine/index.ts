// 实时AI分析引擎
// 优化目标：处理延迟 < 100ms
Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Max-Age': '86400',
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    const startTime = Date.now();

    try {
        const { userId, realtimeData } = await req.json();

        // 快速特征提取（< 20ms）
        const features = extractFastFeatures(realtimeData);

        // 实时推理（< 30ms）
        const inference = performFastInference(features);

        // 即时决策（< 10ms）
        const decision = makeInstantDecision(inference);

        // 边缘计算优化结果
        const result = {
            userId,
            features,
            inference,
            decision,
            processingTime: Date.now() - startTime,
            timestamp: new Date().toISOString()
        };

        // 异步保存结果（不阻塞响应）
        saveResultAsync(userId, result).catch(err => 
            console.error('Async save failed:', err)
        );

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Realtime engine error:', error);
        return new Response(JSON.stringify({
            error: { code: 'REALTIME_ERROR', message: error.message },
            processingTime: Date.now() - startTime
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// 快速特征提取（优化为< 20ms）
function extractFastFeatures(data: any) {
    return {
        vitals: {
            hr: data.heartRate || 75,
            bp: data.bloodPressure || { systolic: 120, diastolic: 80 },
            temp: data.temperature || 36.5
        },
        activity: data.activityLevel || 0.5,
        environment: data.environment || { temp: 22, humidity: 50 },
        timestamp: Date.now()
    };
}

// 快速推理（优化为< 30ms）
function performFastInference(features: any) {
    const riskScore = calculateQuickRiskScore(features);
    const alerts = generateQuickAlerts(features, riskScore);

    return {
        riskScore,
        alerts,
        status: riskScore > 0.7 ? 'high_risk' : riskScore > 0.4 ? 'medium_risk' : 'normal'
    };
}

// 即时决策（优化为< 10ms）
function makeInstantDecision(inference: any) {
    if (inference.status === 'high_risk') {
        return {
            action: 'alert_medical_staff',
            priority: 'urgent',
            message: '检测到高风险状况，立即通知医护人员'
        };
    }

    if (inference.alerts.length > 0) {
        return {
            action: 'notify_caregiver',
            priority: 'normal',
            message: '检测到健康指标异常'
        };
    }

    return {
        action: 'continue_monitoring',
        priority: 'low',
        message: '健康状况正常'
    };
}

function calculateQuickRiskScore(features: any) {
    let score = 0;

    if (features.vitals.hr > 100 || features.vitals.hr < 50) score += 0.4;
    if (features.vitals.bp.systolic > 140) score += 0.3;
    if (features.vitals.temp > 37.5) score += 0.2;

    return Math.min(1, score);
}

function generateQuickAlerts(features: any, riskScore: number) {
    const alerts = [];

    if (riskScore > 0.7) {
        alerts.push({
            type: 'urgent',
            message: '多项健康指标异常',
            timestamp: new Date().toISOString()
        });
    }

    return alerts;
}

async function saveResultAsync(userId: string, result: any) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !serviceRoleKey) return;

    await fetch(`${supabaseUrl}/rest/v1/sensor_data`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            device_type: 'realtime_engine',
            data_type: 'realtime_analysis',
            raw_value: result.features,
            processed_value: result.inference,
            quality_score: 1 - result.inference.riskScore,
            timestamp: result.timestamp,
            metadata: { processingTime: result.processingTime, decision: result.decision }
        })
    });
}
