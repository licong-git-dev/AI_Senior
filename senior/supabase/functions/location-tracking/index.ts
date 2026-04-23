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
        const { action, order_id, worker_id, latitude, longitude, altitude, accuracy, speed, heading, status, notes } = requestData;

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase配置缺失');
        }

        if (action === 'update' || !action) {
            // 更新位置信息
            if (!order_id || !worker_id || latitude === undefined || longitude === undefined) {
                throw new Error('订单ID、陪诊师ID和位置坐标不能为空');
            }

            // 插入位置追踪记录
            const locationData = {
                order_id,
                worker_id,
                latitude,
                longitude,
                altitude: altitude || null,
                accuracy: accuracy || null,
                speed: speed || null,
                heading: heading || null,
                status: status || 'tracking',
                notes: notes || null,
                recorded_at: new Date().toISOString()
            };

            const insertResponse = await fetch(`${supabaseUrl}/rest/v1/location_tracking`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify(locationData)
            });

            if (!insertResponse.ok) {
                const errorText = await insertResponse.text();
                throw new Error(`插入位置记录失败: ${errorText}`);
            }

            const locationResult = await insertResponse.json();

            // 更新陪诊师的最新位置
            await fetch(
                `${supabaseUrl}/rest/v1/escort_workers?id=eq.${worker_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        location_latitude: latitude,
                        location_longitude: longitude,
                        last_location_update: new Date().toISOString()
                    })
                }
            );

            return new Response(JSON.stringify({
                data: {
                    location: locationResult[0],
                    message: '位置更新成功'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'get_history') {
            // 获取历史轨迹
            if (!order_id) {
                throw new Error('订单ID不能为空');
            }

            const historyResponse = await fetch(
                `${supabaseUrl}/rest/v1/location_tracking?order_id=eq.${order_id}&order=recorded_at.asc`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (!historyResponse.ok) {
                throw new Error('获取历史轨迹失败');
            }

            const historyData = await historyResponse.json();

            return new Response(JSON.stringify({
                data: {
                    locations: historyData,
                    count: historyData.length
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'get_latest') {
            // 获取最新位置
            if (!order_id) {
                throw new Error('订单ID不能为空');
            }

            const latestResponse = await fetch(
                `${supabaseUrl}/rest/v1/location_tracking?order_id=eq.${order_id}&order=recorded_at.desc&limit=1`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (!latestResponse.ok) {
                throw new Error('获取最新位置失败');
            }

            const latestData = await latestResponse.json();

            return new Response(JSON.stringify({
                data: {
                    location: latestData[0] || null
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'calculate_distance') {
            // 计算距离（简单的直线距离计算）
            const { lat1, lon1, lat2, lon2 } = requestData;

            if (lat1 === undefined || lon1 === undefined || lat2 === undefined || lon2 === undefined) {
                throw new Error('需要提供两个坐标点');
            }

            // Haversine公式计算两点间距离（单位：公里）
            const R = 6371; // 地球半径（公里）
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            const distance = R * c;

            return new Response(JSON.stringify({
                data: {
                    distance: distance.toFixed(2),
                    unit: 'km'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else {
            throw new Error('不支持的操作类型');
        }

    } catch (error) {
        console.error('位置追踪错误:', error);

        const errorResponse = {
            error: {
                code: 'LOCATION_TRACKING_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
