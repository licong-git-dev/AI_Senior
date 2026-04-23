Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
        'Access-Control-Allow-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'false'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const { report_type, reporting_period, community_ids } = await req.json();

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const dashscopeKey = Deno.env.get('DASHSCOPE_API_KEY');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        const authHeader = req.headers.get('authorization');
        if (!authHeader) {
            throw new Error('No authorization header');
        }

        const token = authHeader.replace('Bearer ', '');
        const userResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'apikey': serviceRoleKey
            }
        });

        if (!userResponse.ok) {
            throw new Error('Invalid token');
        }

        const userData = await userResponse.json();
        const userId = userData.id;

        // 收集报告数据
        const reportData = {
            summary: {},
            details: [],
            recommendations: []
        };

        // 老人总数
        const eldersResponse = await fetch(`${supabaseUrl}/rest/v1/profiles?select=count&role=eq.elderly`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const eldersData = await eldersResponse.json();
        reportData.summary.total_elderly = eldersData.length;

        // 紧急事件统计
        const emergencyResponse = await fetch(`${supabaseUrl}/rest/v1/emergency_calls?select=id,status,created_at&order=created_at.desc&limit=100`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const emergencyData = await emergencyResponse.json();
        reportData.summary.emergency_calls = emergencyData.length;
        reportData.summary.emergency_response_rate = emergencyData.filter(e => e.status === 'completed').length / Math.max(emergencyData.length, 1) * 100;

        // 健康监测数据
        const healthResponse = await fetch(`${supabaseUrl}/rest/v1/health_data?select=count`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const healthData = await healthResponse.json();
        reportData.summary.health_records = healthData.length;

        // 陪诊服务统计
        const ordersResponse = await fetch(`${supabaseUrl}/rest/v1/service_orders?select=id,status,total_amount&order=created_at.desc&limit=100`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const ordersData = await ordersResponse.json();
        reportData.summary.escort_services = ordersData.length;
        reportData.summary.service_revenue = ordersData.reduce((sum, order) => sum + (order.total_amount || 0), 0);

        // 使用AI生成报告摘要和建议
        if (dashscopeKey) {
            try {
                const aiPrompt = `作为智慧养老平台监管报告生成专家，基于以下数据生成${reporting_period || '本月'}的监管报告摘要：

老人总数: ${reportData.summary.total_elderly}人
紧急呼叫: ${reportData.summary.emergency_calls}次
应急响应率: ${reportData.summary.emergency_response_rate.toFixed(1)}%
健康监测记录: ${reportData.summary.health_records}条
陪诊服务: ${reportData.summary.escort_services}单
服务收入: ${reportData.summary.service_revenue}元

请生成简洁的报告摘要（200字以内）和3条改进建议。`;

                const aiResponse = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${dashscopeKey}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        model: 'qwen-plus',
                        messages: [{ role: 'user', content: aiPrompt }],
                        max_tokens: 500
                    })
                });

                if (aiResponse.ok) {
                    const aiData = await aiResponse.json();
                    const aiContent = aiData.choices[0].message.content;
                    reportData.ai_summary = aiContent;

                    // 提取建议（简单文本解析）
                    const lines = aiContent.split('\n');
                    const recommendations = lines.filter(line => 
                        line.includes('建议') || line.match(/^\d+\./) || line.match(/^[一二三四五]/)
                    );
                    reportData.recommendations = recommendations.slice(0, 5);
                }
            } catch (aiError) {
                console.error('AI report generation error:', aiError);
            }
        }

        // 保存报告到数据库
        const saveReportResponse = await fetch(`${supabaseUrl}/rest/v1/government_reports`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify({
                report_type: report_type || 'monthly',
                reporting_period: reporting_period || new Date().toISOString().slice(0, 7),
                data_content: reportData,
                status: 'generated',
                created_by: userId
            })
        });

        if (!saveReportResponse.ok) {
            const errorText = await saveReportResponse.text();
            throw new Error(`Report save failed: ${errorText}`);
        }

        const savedReport = await saveReportResponse.json();

        return new Response(JSON.stringify({
            data: {
                report_id: savedReport[0].id,
                report_data: reportData,
                generated_at: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Regulatory report generation error:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'REPORT_GENERATION_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
