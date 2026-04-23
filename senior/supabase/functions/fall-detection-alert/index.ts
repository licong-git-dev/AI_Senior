// 跌倒检测算法和自动报警
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

        const { user_id, device_id, accelerometer_data, location_latitude, location_longitude } = await req.json();

        if (!user_id || !accelerometer_data) {
            throw new Error('用户ID和加速度计数据为必填项');
        }

        // 简化的跌倒检测算法：基于加速度阈值
        const { x, y, z } = accelerometer_data;
        const magnitude = Math.sqrt(x * x + y * y + z * z);
        
        // 跌倒检测：加速度突变超过阈值（通常 > 2.5g）
        const FALL_THRESHOLD = 24.5; // m/s² (约2.5g)
        const fall_detected = magnitude > FALL_THRESHOLD;
        
        // 跌倒严重程度评估
        let fall_severity = 0;
        if (fall_detected) {
            if (magnitude > 39.2) { // > 4g
                fall_severity = 3; // 严重跌倒
            } else if (magnitude > 29.4) { // > 3g
                fall_severity = 2; // 中度跌倒
            } else {
                fall_severity = 1; // 轻度跌倒
            }
        }

        // 记录跌倒检测数据
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
                data_type: 'fall_detection',
                data_value: magnitude,
                unit: 'm/s²',
                fall_detected,
                fall_severity,
                location_latitude,
                location_longitude,
                measurement_time: new Date().toISOString(),
                abnormal_flag: fall_detected ? 2 : 0,
                ai_analysis_result: {
                    accelerometer: { x, y, z, magnitude },
                    fall_detected,
                    severity: fall_severity,
                    confidence: magnitude > FALL_THRESHOLD ? 0.85 : 0.15
                },
                alert_sent: fall_detected
            })
        });

        if (!insertResponse.ok) {
            const errorText = await insertResponse.text();
            throw new Error(`数据库插入失败: ${errorText}`);
        }

        const fallData = await insertResponse.json();

        // 如果检测到跌倒，创建紧急呼叫
        let emergencyCall = null;
        if (fall_detected) {
            const callResponse = await fetch(`${supabaseUrl}/rest/v1/emergency_calls`, {
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
                    call_type: 'fall_detected',
                    trigger_source: 'auto_detection',
                    severity_level: fall_severity,
                    location_latitude,
                    location_longitude,
                    call_time: new Date().toISOString(),
                    response_status: 1, // 待响应
                    health_data_snapshot: {
                        fall_detected: true,
                        fall_severity,
                        accelerometer_magnitude: magnitude,
                        detection_time: new Date().toISOString()
                    }
                })
            });

            if (callResponse.ok) {
                emergencyCall = await callResponse.json();
            }
        }

        return new Response(JSON.stringify({
            data: {
                fall_detected,
                fall_severity,
                magnitude,
                fall_data: fallData[0],
                emergency_call: emergencyCall ? emergencyCall[0] : null,
                alert_created: fall_detected
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('跌倒检测错误:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'FALL_DETECTION_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
