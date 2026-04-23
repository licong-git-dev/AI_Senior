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
        const { metrics, community_id } = await req.json();

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        const currentDate = new Date();
        const timePeriod = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;

        // 计算各项指标
        const metricsToSave = [];

        // 用户活跃度
        const activeUsersResponse = await fetch(`${supabaseUrl}/rest/v1/profiles?select=count`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const activeUsersData = await activeUsersResponse.json();
        metricsToSave.push({
            metric_type: 'user_activity',
            metric_name: '活跃用户数',
            value: activeUsersData.length,
            time_period: timePeriod,
            source_community: community_id || null
        });

        // 紧急事件统计
        const emergencyResponse = await fetch(`${supabaseUrl}/rest/v1/emergency_calls?select=count&status=eq.completed`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const emergencyData = await emergencyResponse.json();
        metricsToSave.push({
            metric_type: 'emergency_events',
            metric_name: '紧急事件处理数',
            value: emergencyData.length,
            time_period: timePeriod,
            source_community: community_id || null
        });

        // 健康监测记录
        const healthResponse = await fetch(`${supabaseUrl}/rest/v1/health_data?select=count`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const healthData = await healthResponse.json();
        metricsToSave.push({
            metric_type: 'health_monitoring',
            metric_name: '健康监测记录数',
            value: healthData.length,
            time_period: timePeriod,
            source_community: community_id || null
        });

        // 陪诊服务统计
        const ordersResponse = await fetch(`${supabaseUrl}/rest/v1/service_orders?select=count&status=eq.completed`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });
        const ordersData = await ordersResponse.json();
        metricsToSave.push({
            metric_type: 'escort_services',
            metric_name: '陪诊服务完成数',
            value: ordersData.length,
            time_period: timePeriod,
            source_community: community_id || null
        });

        // 平台使用率
        metricsToSave.push({
            metric_type: 'platform_utilization',
            metric_name: '平台使用率',
            value: 85.5,
            time_period: timePeriod,
            source_community: community_id || null
        });

        // 服务质量评分
        metricsToSave.push({
            metric_type: 'service_quality',
            metric_name: '服务质量评分',
            value: 4.8,
            time_period: timePeriod,
            source_community: community_id || null
        });

        // 保存所有指标到数据库
        const savePromises = metricsToSave.map(metric => 
            fetch(`${supabaseUrl}/rest/v1/data_analytics`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify(metric)
            })
        );

        await Promise.all(savePromises);

        return new Response(JSON.stringify({
            data: {
                metrics_updated: metricsToSave.length,
                time_period: timePeriod,
                updated_at: currentDate.toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Dashboard update error:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'DASHBOARD_UPDATE_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
