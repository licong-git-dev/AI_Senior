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
        const { action, order_id, user_id, payment_method, payment_channel } = await req.json();

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase配置缺失');
        }

        if (action === 'create_payment') {
            // 创建支付订单
            if (!order_id || !user_id || !payment_method) {
                throw new Error('订单ID、用户ID和支付方式不能为空');
            }

            // 获取订单信息
            const orderResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${order_id}`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (!orderResponse.ok) {
                throw new Error('获取订单信息失败');
            }

            const orders = await orderResponse.json();
            if (orders.length === 0) {
                throw new Error('订单不存在');
            }

            const order = orders[0];

            // 创建支付记录
            const paymentData = {
                order_id,
                user_id,
                payment_method,
                payment_channel: payment_channel || payment_method,
                amount: order.total_fee,
                currency: 'CNY',
                payment_status: 'pending',
                transaction_id: `TXN${Date.now()}${Math.floor(Math.random() * 10000)}`,
                metadata: {
                    order_number: order.order_number,
                    service_type: order.service_type
                }
            };

            const paymentResponse = await fetch(`${supabaseUrl}/rest/v1/payment_records`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify(paymentData)
            });

            if (!paymentResponse.ok) {
                throw new Error('创建支付记录失败');
            }

            const paymentRecord = await paymentResponse.json();

            // 模拟支付接口调用（实际应该调用真实的支付网关）
            let paymentResult = {
                success: false,
                payment_url: '',
                qr_code: '',
                message: ''
            };

            if (payment_method === 'wechat') {
                // 模拟微信支付
                paymentResult = {
                    success: true,
                    payment_url: `https://api.mch.weixin.qq.com/pay/unifiedorder`,
                    qr_code: `weixin://wxpay/bizpayurl?pr=${paymentRecord[0].transaction_id}`,
                    message: '请使用微信扫码支付'
                };
            } else if (payment_method === 'alipay') {
                // 模拟支付宝支付
                paymentResult = {
                    success: true,
                    payment_url: `https://openapi.alipay.com/gateway.do`,
                    qr_code: `https://qr.alipay.com/${paymentRecord[0].transaction_id}`,
                    message: '请使用支付宝扫码支付'
                };
            } else if (payment_method === 'medicare') {
                // 模拟医保支付
                paymentResult = {
                    success: true,
                    payment_url: `https://medicare.gov.cn/pay`,
                    message: '请使用医保电子凭证支付'
                };
            }

            return new Response(JSON.stringify({
                data: {
                    payment_record: paymentRecord[0],
                    payment_result: paymentResult,
                    message: '支付订单创建成功'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'confirm_payment') {
            // 确认支付（模拟支付成功回调）
            const { payment_id } = await req.json();

            if (!payment_id) {
                throw new Error('支付ID不能为空');
            }

            // 更新支付状态
            const updatePaymentResponse = await fetch(
                `${supabaseUrl}/rest/v1/payment_records?id=eq.${payment_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        payment_status: 'paid',
                        payment_time: new Date().toISOString()
                    })
                }
            );

            if (!updatePaymentResponse.ok) {
                throw new Error('更新支付状态失败');
            }

            const updatedPayment = await updatePaymentResponse.json();

            // 更新订单支付状态
            await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${updatedPayment[0].order_id}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        payment_status: 'paid'
                    })
                }
            );

            // 创建结算记录（订单完成后陪诊师可提现）
            const orderResponse = await fetch(
                `${supabaseUrl}/rest/v1/service_orders?id=eq.${updatedPayment[0].order_id}`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const orders = await orderResponse.json();
            if (orders.length > 0 && orders[0].worker_id) {
                const order = orders[0];
                const platformFee = order.total_fee * 0.15; // 平台抽成15%
                const workerEarnings = order.total_fee - platformFee;

                await fetch(`${supabaseUrl}/rest/v1/settlement_records`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        worker_id: order.worker_id,
                        order_id: order.id,
                        settlement_amount: order.total_fee,
                        platform_fee: platformFee,
                        worker_earnings: workerEarnings,
                        settlement_status: 'pending'
                    })
                });
            }

            return new Response(JSON.stringify({
                data: {
                    payment: updatedPayment[0],
                    message: '支付确认成功'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else if (action === 'create_settlement') {
            // 创建结算（陪诊师提现）
            const { worker_id } = await req.json();

            if (!worker_id) {
                throw new Error('陪诊师ID不能为空');
            }

            // 获取待结算的记录
            const settlementResponse = await fetch(
                `${supabaseUrl}/rest/v1/settlement_records?worker_id=eq.${worker_id}&settlement_status=eq.pending`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const settlements = await settlementResponse.json();
            
            if (settlements.length === 0) {
                throw new Error('没有待结算的记录');
            }

            // 计算总金额
            const totalEarnings = settlements.reduce((sum, s) => sum + parseFloat(s.worker_earnings), 0);

            // 更新结算状态（模拟打款）
            for (const settlement of settlements) {
                await fetch(
                    `${supabaseUrl}/rest/v1/settlement_records?id=eq.${settlement.id}`,
                    {
                        method: 'PATCH',
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            settlement_status: 'completed',
                            settlement_time: new Date().toISOString(),
                            transaction_reference: `SETTLE${Date.now()}`
                        })
                    }
                );
            }

            return new Response(JSON.stringify({
                data: {
                    total_earnings: totalEarnings,
                    settled_count: settlements.length,
                    message: '结算成功，款项将在1-3个工作日内到账'
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } else {
            throw new Error('不支持的操作类型');
        }

    } catch (error) {
        console.error('支付处理错误:', error);

        const errorResponse = {
            error: {
                code: 'PAYMENT_PROCESSING_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
