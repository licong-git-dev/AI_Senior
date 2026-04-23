// 护理数据分析和报告生成
Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'false'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase配置缺失');
        }

        const { user_id, start_date, end_date } = await req.json();

        if (!user_id) {
            throw new Error('用户ID为必填项');
        }

        const startTime = start_date || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
        const endTime = end_date || new Date().toISOString();

        // 获取用户健康数据
        const healthResponse = await fetch(
            `${supabaseUrl}/rest/v1/health_data?user_id=eq.${user_id}&measurement_time=gte.${startTime}&measurement_time=lte.${endTime}&order=measurement_time.desc`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        if (!healthResponse.ok) {
            throw new Error('获取健康数据失败');
        }

        const healthData = await healthResponse.json();

        // 数据统计分析
        const analytics = {
            total_records: healthData.length,
            data_by_type: {} as Record<string, any>,
            abnormal_events: 0,
            fall_events: 0,
            health_trends: {} as Record<string, any>
        };

        // 按数据类型分组统计
        healthData.forEach((record: any) => {
            const type = record.data_type;
            
            if (!analytics.data_by_type[type]) {
                analytics.data_by_type[type] = {
                    count: 0,
                    values: [],
                    abnormal_count: 0
                };
            }

            analytics.data_by_type[type].count++;
            
            if (record.data_value !== null) {
                analytics.data_by_type[type].values.push(record.data_value);
            }

            if (record.abnormal_flag > 0) {
                analytics.data_by_type[type].abnormal_count++;
                analytics.abnormal_events++;
            }

            if (record.fall_detected) {
                analytics.fall_events++;
            }
        });

        // 计算各类型数据的统计指标
        for (const type in analytics.data_by_type) {
            const values = analytics.data_by_type[type].values;
            if (values.length > 0) {
                const sum = values.reduce((a: number, b: number) => a + b, 0);
                analytics.data_by_type[type].average = sum / values.length;
                analytics.data_by_type[type].max = Math.max(...values);
                analytics.data_by_type[type].min = Math.min(...values);
            }
        }

        // 获取紧急呼叫记录
        const callsResponse = await fetch(
            `${supabaseUrl}/rest/v1/emergency_calls?user_id=eq.${user_id}&call_time=gte.${startTime}&call_time=lte.${endTime}&order=call_time.desc`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        const emergencyCalls = callsResponse.ok ? await callsResponse.json() : [];

        // 获取护理计划
        const plansResponse = await fetch(
            `${supabaseUrl}/rest/v1/care_plans?user_id=eq.${user_id}&status=eq.1&order=created_at.desc&limit=1`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        const carePlans = plansResponse.ok ? await plansResponse.json() : [];

        // 健康风险评估
        let risk_score = 0;
        let risk_level = 1; // 1-低风险 2-中风险 3-高风险

        if (analytics.fall_events > 2) risk_score += 30;
        else if (analytics.fall_events > 0) risk_score += 15;

        if (analytics.abnormal_events > 10) risk_score += 25;
        else if (analytics.abnormal_events > 5) risk_score += 15;

        if (emergencyCalls.length > 3) risk_score += 20;
        else if (emergencyCalls.length > 0) risk_score += 10;

        if (risk_score >= 50) risk_level = 3;
        else if (risk_score >= 25) risk_level = 2;

        // 生成建议
        const recommendations = [];
        if (analytics.fall_events > 0) {
            recommendations.push('建议加强环境安全评估，预防跌倒');
        }
        if (analytics.data_by_type['blood_pressure']?.abnormal_count > 3) {
            recommendations.push('血压波动较大，建议定期就医检查');
        }
        if (analytics.data_by_type['blood_sugar']?.abnormal_count > 3) {
            recommendations.push('血糖控制不理想，建议调整饮食和用药');
        }
        if (emergencyCalls.length > 2) {
            recommendations.push('紧急呼叫频繁，建议增加日常监护频率');
        }

        return new Response(JSON.stringify({
            data: {
                user_id,
                analysis_period: {
                    start: startTime,
                    end: endTime
                },
                analytics,
                emergency_calls: {
                    total: emergencyCalls.length,
                    by_type: emergencyCalls.reduce((acc: any, call: any) => {
                        acc[call.call_type] = (acc[call.call_type] || 0) + 1;
                        return acc;
                    }, {})
                },
                care_plans: carePlans,
                risk_assessment: {
                    score: risk_score,
                    level: risk_level,
                    level_text: risk_level === 3 ? '高风险' : risk_level === 2 ? '中风险' : '低风险'
                },
                recommendations,
                report_generated_at: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('护理数据分析错误:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'CARE_DATA_ANALYTICS_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
