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
        const { action, provider_data, application_id, review_notes } = await req.json();

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

        let result = {};

        if (action === 'submit_application') {
            // 提交服务商申请
            // 首先创建服务商记录
            const providerResponse = await fetch(`${supabaseUrl}/rest/v1/service_providers`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify({
                    name: provider_data.name,
                    license_number: provider_data.license_number,
                    contact_info: provider_data.contact_info,
                    service_types: provider_data.service_types,
                    certification_status: 'pending'
                })
            });

            if (!providerResponse.ok) {
                const errorText = await providerResponse.text();
                throw new Error(`Provider creation failed: ${errorText}`);
            }

            const providerResult = await providerResponse.json();
            const providerId = providerResult[0].id;

            // 创建申请记录
            const applicationResponse = await fetch(`${supabaseUrl}/rest/v1/provider_applications`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify({
                    provider_id: providerId,
                    application_data: provider_data,
                    status: 'pending'
                })
            });

            if (!applicationResponse.ok) {
                const errorText = await applicationResponse.text();
                throw new Error(`Application creation failed: ${errorText}`);
            }

            const applicationResult = await applicationResponse.json();
            result = {
                application_id: applicationResult[0].id,
                provider_id: providerId,
                status: 'pending',
                message: '申请已提交，等待审核'
            };

        } else if (action === 'review_application') {
            // 审核服务商申请
            const approved = review_notes && review_notes.includes('approved');

            // 更新申请记录
            const updateApplicationResponse = await fetch(`${supabaseUrl}/rest/v1/provider_applications?id=eq.${application_id}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify({
                    status: approved ? 'approved' : 'rejected',
                    review_notes: review_notes,
                    reviewed_at: new Date().toISOString(),
                    reviewed_by: userId
                })
            });

            if (!updateApplicationResponse.ok) {
                const errorText = await updateApplicationResponse.text();
                throw new Error(`Application update failed: ${errorText}`);
            }

            // 如果批准，更新服务商状态
            if (approved) {
                const getApplicationResponse = await fetch(`${supabaseUrl}/rest/v1/provider_applications?select=provider_id&id=eq.${application_id}`, {
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey
                    }
                });

                const appData = await getApplicationResponse.json();
                if (appData.length > 0) {
                    const providerId = appData[0].provider_id;

                    await fetch(`${supabaseUrl}/rest/v1/service_providers?id=eq.${providerId}`, {
                        method: 'PATCH',
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            certification_status: 'approved'
                        })
                    });
                }
            }

            result = {
                application_id: application_id,
                status: approved ? 'approved' : 'rejected',
                message: approved ? '申请已批准' : '申请被拒绝'
            };

        } else if (action === 'verify_credentials') {
            // 使用AI验证服务商资质
            if (dashscopeKey) {
                const aiPrompt = `作为养老服务平台审核专家，请审核以下服务商信息并给出评估：
服务商名称: ${provider_data.name}
许可证号: ${provider_data.license_number}
服务类型: ${provider_data.service_types.join(', ')}
联系信息: ${JSON.stringify(provider_data.contact_info)}

请评估该服务商是否符合平台准入标准，并给出简短的审核建议。`;

                const aiResponse = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${dashscopeKey}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        model: 'qwen-plus',
                        messages: [{ role: 'user', content: aiPrompt }],
                        max_tokens: 300
                    })
                });

                if (aiResponse.ok) {
                    const aiData = await aiResponse.json();
                    result = {
                        verification_result: aiData.choices[0].message.content,
                        verified_at: new Date().toISOString()
                    };
                }
            } else {
                result = {
                    verification_result: '资质验证功能需要AI服务支持',
                    verified_at: new Date().toISOString()
                };
            }
        }

        return new Response(JSON.stringify({
            data: result
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Provider verification error:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'VERIFICATION_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
