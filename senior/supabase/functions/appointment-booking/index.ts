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
        const { 
            elderly_id, 
            elderly_name, 
            elderly_phone, 
            appointment_time, 
            hospital_name, 
            hospital_address, 
            department, 
            doctor_name, 
            service_type, 
            urgency_level, 
            special_needs 
        } = await req.json();

        if (!elderly_id || !appointment_time || !hospital_name) {
            throw new Error('必填字段缺失：elderly_id、appointment_time、hospital_name');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase配置缺失');
        }

        // 1. 创建预约记录
        const appointmentData = {
            elderly_id,
            elderly_name,
            elderly_phone,
            appointment_time,
            hospital_name,
            hospital_address,
            department,
            doctor_name,
            service_type: service_type || 'standard',
            urgency_level: urgency_level || 1,
            special_needs,
            status: 'pending'
        };

        const insertResponse = await fetch(`${supabaseUrl}/rest/v1/appointments`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(appointmentData)
        });

        if (!insertResponse.ok) {
            const errorText = await insertResponse.text();
            throw new Error(`创建预约失败: ${errorText}`);
        }

        const appointmentResult = await insertResponse.json();
        const newAppointment = appointmentResult[0];

        // 2. 智能匹配陪诊师
        // 查询可用的陪诊师，按照评分和完成订单数排序
        const workersResponse = await fetch(
            `${supabaseUrl}/rest/v1/escort_workers?work_status=eq.available&order=rating.desc,completed_orders.desc&limit=10`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json'
                }
            }
        );

        if (!workersResponse.ok) {
            throw new Error('查询陪诊师失败');
        }

        const availableWorkers = await workersResponse.json();

        // 简单的匹配算法：选择评分最高的可用陪诊师
        let matchedWorker = null;
        if (availableWorkers && availableWorkers.length > 0) {
            // 如果有紧急需求，优先选择经验丰富的
            if (urgency_level >= 3) {
                matchedWorker = availableWorkers.find(w => w.experience_years >= 3) || availableWorkers[0];
            } else {
                matchedWorker = availableWorkers[0];
            }
        }

        // 3. 创建服务订单
        const orderNumber = `ORD${Date.now()}${Math.floor(Math.random() * 1000)}`;
        
        const orderData = {
            appointment_id: newAppointment.id,
            elderly_id,
            worker_id: matchedWorker?.id || null,
            order_number: orderNumber,
            service_type: service_type || 'standard',
            scheduled_time: appointment_time,
            estimated_duration: urgency_level >= 3 ? 180 : 120, // 紧急情况预估3小时，普通2小时
            destination_location: hospital_address,
            base_fee: 50.00,
            distance_fee: 0,
            time_fee: 0,
            total_fee: 50.00,
            payment_status: 'unpaid',
            order_status: matchedWorker ? 'assigned' : 'pending',
            dispatch_time: matchedWorker ? new Date().toISOString() : null
        };

        const orderResponse = await fetch(`${supabaseUrl}/rest/v1/service_orders`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(orderData)
        });

        if (!orderResponse.ok) {
            const errorText = await orderResponse.text();
            throw new Error(`创建订单失败: ${errorText}`);
        }

        const orderResult = await orderResponse.json();

        return new Response(JSON.stringify({
            data: {
                appointment: newAppointment,
                order: orderResult[0],
                matched_worker: matchedWorker,
                message: matchedWorker ? '预约成功，已自动匹配陪诊师' : '预约成功，等待陪诊师接单'
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('预约处理错误:', error);

        const errorResponse = {
            error: {
                code: 'APPOINTMENT_BOOKING_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
