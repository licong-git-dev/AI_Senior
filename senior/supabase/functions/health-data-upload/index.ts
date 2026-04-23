// 健康数据实时上传和处理
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

        const { user_id, device_id, data_type, data_value, unit, systolic_pressure, diastolic_pressure, heart_rate, blood_sugar, temperature } = await req.json();

        if (!user_id || !data_type) {
            throw new Error('用户ID和数据类型为必填项');
        }

        // 分析健康数据是否异常
        let abnormal_flag = 0;
        const ai_analysis_result: any = {};

        if (data_type === 'blood_pressure' && systolic_pressure && diastolic_pressure) {
            if (systolic_pressure >= 140 || diastolic_pressure >= 90) {
                abnormal_flag = 2; // 高血压预警
                ai_analysis_result.warning = '血压偏高，建议休息并监测';
            } else if (systolic_pressure < 90 || diastolic_pressure < 60) {
                abnormal_flag = 2; // 低血压预警
                ai_analysis_result.warning = '血压偏低，注意安全';
            }
        }

        if (data_type === 'heart_rate' && heart_rate) {
            if (heart_rate > 100) {
                abnormal_flag = Math.max(abnormal_flag, 1); // 心率偏快
                ai_analysis_result.heart_rate_note = '心率偏快，请注意休息';
            } else if (heart_rate < 60) {
                abnormal_flag = Math.max(abnormal_flag, 1); // 心率偏慢
                ai_analysis_result.heart_rate_note = '心率偏慢';
            }
        }

        if (data_type === 'blood_sugar' && blood_sugar) {
            if (blood_sugar > 7.0) {
                abnormal_flag = 2; // 血糖偏高
                ai_analysis_result.warning = '血糖偏高，请注意饮食控制';
            } else if (blood_sugar < 3.9) {
                abnormal_flag = 2; // 低血糖预警
                ai_analysis_result.warning = '血糖偏低，立即补充糖分';
            }
        }

        // 插入健康数据
        const insertResponse = await fetch(`${supabaseUrl}/rest/v1/health_data`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify({
                user_id,
                device_id,
                data_type,
                data_value,
                unit,
                systolic_pressure,
                diastolic_pressure,
                heart_rate,
                blood_sugar,
                temperature,
                measurement_time: new Date().toISOString(),
                abnormal_flag,
                ai_analysis_result,
                alert_sent: abnormal_flag === 2
            })
        });

        if (!insertResponse.ok) {
            const errorText = await insertResponse.text();
            throw new Error(`数据库插入失败: ${errorText}`);
        }

        const healthData = await insertResponse.json();

        // 如果有异常，创建紧急呼叫记录
        if (abnormal_flag === 2) {
            await fetch(`${supabaseUrl}/rest/v1/emergency_calls`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id,
                    device_id,
                    call_type: 'health_alert',
                    trigger_source: 'auto_detection',
                    severity_level: 2,
                    call_time: new Date().toISOString(),
                    response_status: 1,
                    health_data_snapshot: {
                        data_type,
                        data_value,
                        systolic_pressure,
                        diastolic_pressure,
                        heart_rate,
                        blood_sugar,
                        temperature,
                        ai_analysis: ai_analysis_result
                    }
                })
            });
        }

        return new Response(JSON.stringify({
            data: {
                health_data: healthData[0],
                abnormal_flag,
                ai_analysis: ai_analysis_result,
                alert_created: abnormal_flag === 2
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('健康数据上传错误:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'HEALTH_DATA_UPLOAD_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
