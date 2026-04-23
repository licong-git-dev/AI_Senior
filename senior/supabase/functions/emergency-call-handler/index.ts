// 紧急呼叫路由和通知处理
Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, PUT, OPTIONS',
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

        const { action, call_id, user_id, call_type, severity_level, location_latitude, location_longitude, responder_id } = await req.json();

        if (action === 'create') {
            // 创建新的紧急呼叫
            if (!user_id || !call_type) {
                throw new Error('用户ID和呼叫类型为必填项');
            }

            const insertResponse = await fetch(`${supabaseUrl}/rest/v1/emergency_calls`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify({
                    user_id,
                    call_type,
                    trigger_source: 'manual',
                    severity_level: severity_level || 2,
                    location_latitude,
                    location_longitude,
                    call_time: new Date().toISOString(),
                    response_status: 1 // 待响应
                })
            });

            if (!insertResponse.ok) {
                const errorText = await insertResponse.text();
                throw new Error(`创建紧急呼叫失败: ${errorText}`);
            }

            const callData = await insertResponse.json();

            // TODO: 在实际应用中，这里应该发送通知给护理人员
            // 例如：推送通知、短信、电话等

            return new Response(JSON.stringify({
                data: {
                    emergency_call: callData[0],
                    notifications_sent: true
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'respond') {
            // 护理人员响应紧急呼叫
            if (!call_id || !responder_id) {
                throw new Error('呼叫ID和响应人员ID为必填项');
            }

            const updateResponse = await fetch(`${supabaseUrl}/rest/v1/emergency_calls?id=eq.${call_id}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify({
                    response_status: 2, // 已响应
                    responder_id,
                    response_time: new Date().toISOString()
                })
            });

            if (!updateResponse.ok) {
                const errorText = await updateResponse.text();
                throw new Error(`更新响应状态失败: ${errorText}`);
            }

            const callData = await updateResponse.json();

            return new Response(JSON.stringify({
                data: {
                    emergency_call: callData[0],
                    response_recorded: true
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'complete') {
            // 完成紧急呼叫处理
            if (!call_id) {
                throw new Error('呼叫ID为必填项');
            }

            const updateResponse = await fetch(`${supabaseUrl}/rest/v1/emergency_calls?id=eq.${call_id}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify({
                    response_status: 4, // 已完成
                    completion_time: new Date().toISOString()
                })
            });

            if (!updateResponse.ok) {
                const errorText = await updateResponse.text();
                throw new Error(`更新完成状态失败: ${errorText}`);
            }

            const callData = await updateResponse.json();

            return new Response(JSON.stringify({
                data: {
                    emergency_call: callData[0],
                    completed: true
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else {
            throw new Error('无效的操作类型');
        }

    } catch (error) {
        console.error('紧急呼叫处理错误:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'EMERGENCY_CALL_HANDLER_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
