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
        const { order_id, worker_id, action } = await req.json();

        if (!order_id) {
            throw new Error('订单ID不能为空');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase配置缺失');
        }

        // 根据不同的操作执行相应的派单逻辑
        if (action === 'accept') {
            // 陪诊师接单
            if (!worker_id) {
                throw new Error('陪诊师ID不能为空');
            }

            // 更新订单状态
            const updateOrderResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${order_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        worker_id,
                        order_status: 'accepted',
                        accepted_time: new Date().toISOString()
                    })
                }
            );

            if (!updateOrderResponse.ok) {
                throw new Error('更新订单失败');
            }

            const updatedOrder = await updateOrderResponse.json();

            // 更新陪诊师状态为工作中
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
                        work_status: 'busy',
                        total_orders: 'total_orders + 1'
                    })
                }
            );

            return new Response(JSON.stringify({
                data: {
                    order: updatedOrder[0],
                    message: '陪诊师接单成功'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'start') {
            // 开始服务
            const updateResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${order_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        order_status: 'in_progress',
                        actual_start_time: new Date().toISOString()
                    })
                }
            );

            if (!updateResponse.ok) {
                throw new Error('开始服务失败');
            }

            const updatedOrder = await updateResponse.json();

            return new Response(JSON.stringify({
                data: {
                    order: updatedOrder[0],
                    message: '服务已开始'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'arrive') {
            // 到达目的地
            const updateResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${order_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        arrived_time: new Date().toISOString()
                    })
                }
            );

            if (!updateResponse.ok) {
                throw new Error('更新到达状态失败');
            }

            const updatedOrder = await updateResponse.json();

            return new Response(JSON.stringify({
                data: {
                    order: updatedOrder[0],
                    message: '已到达目的地'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'complete') {
            // 完成服务
            const updateResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${order_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        order_status: 'completed',
                        actual_end_time: new Date().toISOString(),
                        completed_time: new Date().toISOString()
                    })
                }
            );

            if (!updateResponse.ok) {
                throw new Error('完成服务失败');
            }

            const updatedOrder = await updateResponse.json();

            // 获取订单的陪诊师ID
            if (updatedOrder[0].worker_id) {
                // 更新陪诊师状态为可用，并增加完成订单数
                await fetch(
                    `${supabaseUrl}/rest/v1/escort_workers?id=eq.${updatedOrder[0].worker_id}`,
                    {
                        method: 'PATCH',
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            work_status: 'available'
                        })
                    }
                );

                // 单独增加completed_orders计数
                await fetch(
                    `${supabaseUrl}/rest/v1/rpc/increment_completed_orders`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            worker_id: updatedOrder[0].worker_id
                        })
                    }
                ).catch(() => {
                    // 如果RPC不存在，使用直接更新
                    console.log('RPC不存在，使用直接更新');
                });
            }

            return new Response(JSON.stringify({
                data: {
                    order: updatedOrder[0],
                    message: '服务已完成'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'cancel') {
            // 取消订单
            const { cancellation_reason } = await req.json();

            const updateResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${order_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        order_status: 'cancelled',
                        cancelled_time: new Date().toISOString(),
                        cancellation_reason
                    })
                }
            );

            if (!updateResponse.ok) {
                throw new Error('取消订单失败');
            }

            const updatedOrder = await updateResponse.json();

            // 如果已分配陪诊师，将其状态改回可用
            if (updatedOrder[0].worker_id) {
                await fetch(
                    `${supabaseUrl}/rest/v1/escort_workers?id=eq.${updatedOrder[0].worker_id}`,
                    {
                        method: 'PATCH',
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            work_status: 'available'
                        })
                    }
                );
            }

            return new Response(JSON.stringify({
                data: {
                    order: updatedOrder[0],
                    message: '订单已取消'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else {
            throw new Error('不支持的操作类型');
        }

    } catch (error) {
        console.error('派单处理错误:', error);

        const errorResponse = {
            error: {
                code: 'ORDER_DISPATCH_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
