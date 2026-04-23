// 多模态数据融合处理 Edge Function
// 整合手环、床垫、摄像头、环境传感器数据

Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Max-Age': '86400',
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const { user_id, data_sources, time_range } = await req.json();

        if (!user_id || !data_sources) {
            throw new Error('缺少必需参数：user_id 和 data_sources');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

        // 1. 从各个设备获取原始数据
        const deviceDataPromises = data_sources.map(async (source: any) => {
            const params = new URLSearchParams({
                user_id: `eq.${user_id}`,
                device_type: `eq.${source.type}`,
                timestamp: `gte.${time_range.start}`,
                timestamp2: `lte.${time_range.end}`,
                order: 'timestamp.desc',
                limit: '1000'
            });

            const response = await fetch(
                `${supabaseUrl}/rest/v1/sensor_data?${params}`,
                {
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                    }
                }
            );

            if (!response.ok) {
                console.error(`获取${source.type}数据失败`);
                return { type: source.type, data: [], error: true };
            }

            const data = await response.json();
            return { type: source.type, data, error: false };
        });

        const deviceDataResults = await Promise.all(deviceDataPromises);

        // 2. 数据质量评估和清洗
        const cleanedData = deviceDataResults.map(result => {
            if (result.error || !result.data.length) {
                return { ...result, quality: 0, cleaned: [] };
            }

            const cleaned = result.data.filter((item: any) => {
                // 数据质量过滤：quality_score > 0.7
                return item.quality_score && item.quality_score > 0.7;
            });

            const quality = cleaned.length / result.data.length;
            return { ...result, quality, cleaned };
        });

        // 3. 时间对齐和数据融合
        const fusedData = performDataFusion(cleanedData);

        // 4. 特征提取
        const features = extractMultimodalFeatures(fusedData);

        // 5. 保存融合结果到传感器数据表
        const fusionRecord = {
            user_id,
            device_type: 'fusion',
            device_id: 'multimodal_fusion_engine',
            sensor_type: 'multimodal_fusion',
            data_value: {
                fused_data: fusedData,
                features: features,
                data_sources: data_sources.map((s: any) => s.type),
                quality_scores: cleanedData.map(d => ({ type: d.type, quality: d.quality }))
            },
            quality_score: calculateOverallQuality(cleanedData),
            timestamp: new Date().toISOString(),
        };

        const saveResponse = await fetch(
            `${supabaseUrl}/rest/v1/sensor_data`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify(fusionRecord)
            }
        );

        if (!saveResponse.ok) {
            const errorText = await saveResponse.text();
            throw new Error(`保存融合数据失败: ${errorText}`);
        }

        const savedData = await saveResponse.json();

        return new Response(JSON.stringify({
            data: {
                fusion_id: savedData[0].id,
                fused_data: fusedData,
                features: features,
                quality_report: {
                    overall_quality: fusionRecord.quality_score,
                    device_qualities: cleanedData.map(d => ({
                        device: d.type,
                        quality: d.quality,
                        records_count: d.cleaned.length
                    }))
                },
                processing_time: Date.now(),
                message: '多模态数据融合成功'
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('多模态数据融合错误:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'MULTIMODAL_FUSION_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// 数据融合算法
function performDataFusion(cleanedData: any[]): any {
    const fusion: any = {
        vital_signs: {},
        activity: {},
        sleep: {},
        environment: {},
        timestamp: new Date().toISOString()
    };

    cleanedData.forEach(device => {
        if (!device.cleaned.length) return;

        switch (device.type) {
            case 'wristband':
                // 手环数据：心率、步数、卡路里
                fusion.vital_signs.heart_rate = calculateAverage(device.cleaned, 'heart_rate');
                fusion.activity.steps = sumValues(device.cleaned, 'steps');
                fusion.activity.calories = sumValues(device.cleaned, 'calories');
                break;

            case 'mattress':
                // 床垫数据：呼吸频率、翻身次数、睡眠阶段
                fusion.vital_signs.respiratory_rate = calculateAverage(device.cleaned, 'respiratory_rate');
                fusion.sleep.turn_count = sumValues(device.cleaned, 'turn_count');
                fusion.sleep.sleep_stage = getMostRecent(device.cleaned, 'sleep_stage');
                break;

            case 'camera':
                // 摄像头数据：活动检测、姿态分析
                fusion.activity.detected_activities = aggregateActivities(device.cleaned);
                fusion.activity.posture_analysis = getMostRecent(device.cleaned, 'posture');
                break;

            case 'environment':
                // 环境传感器：温度、湿度、光照
                fusion.environment.temperature = calculateAverage(device.cleaned, 'temperature');
                fusion.environment.humidity = calculateAverage(device.cleaned, 'humidity');
                fusion.environment.light_level = calculateAverage(device.cleaned, 'light');
                break;
        }
    });

    return fusion;
}

// 多模态特征提取
function extractMultimodalFeatures(fusedData: any): any {
    return {
        // 生理特征
        physiological: {
            heart_rate_avg: fusedData.vital_signs.heart_rate || 0,
            respiratory_rate_avg: fusedData.vital_signs.respiratory_rate || 0,
            vital_signs_stability: calculateStability(fusedData.vital_signs)
        },
        // 活动特征
        activity: {
            total_steps: fusedData.activity.steps || 0,
            activity_diversity: calculateActivityDiversity(fusedData.activity.detected_activities),
            mobility_score: calculateMobilityScore(fusedData.activity)
        },
        // 睡眠特征
        sleep: {
            sleep_quality_indicator: calculateSleepQuality(fusedData.sleep),
            sleep_disturbance: fusedData.sleep.turn_count || 0,
            sleep_stage: fusedData.sleep.sleep_stage || 'unknown'
        },
        // 环境特征
        environment: {
            comfort_index: calculateComfortIndex(fusedData.environment),
            temperature: fusedData.environment.temperature || 0,
            humidity: fusedData.environment.humidity || 0
        }
    };
}

// 辅助函数
function calculateAverage(data: any[], field: string): number {
    const values = data
        .map(d => d.data_value?.[field])
        .filter(v => v != null && !isNaN(v));
    
    if (!values.length) return 0;
    return values.reduce((a, b) => a + b, 0) / values.length;
}

function sumValues(data: any[], field: string): number {
    return data
        .map(d => d.data_value?.[field])
        .filter(v => v != null && !isNaN(v))
        .reduce((a, b) => a + b, 0);
}

function getMostRecent(data: any[], field: string): any {
    if (!data.length) return null;
    const sorted = data.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    return sorted[0]?.data_value?.[field] || null;
}

function aggregateActivities(data: any[]): string[] {
    const activities = new Set<string>();
    data.forEach(d => {
        const activity = d.data_value?.activity;
        if (activity) activities.add(activity);
    });
    return Array.from(activities);
}

function calculateStability(vitalSigns: any): number {
    // 简化的稳定性计算：0-1分数
    let score = 1.0;
    if (vitalSigns.heart_rate && (vitalSigns.heart_rate < 50 || vitalSigns.heart_rate > 100)) {
        score -= 0.3;
    }
    if (vitalSigns.respiratory_rate && (vitalSigns.respiratory_rate < 12 || vitalSigns.respiratory_rate > 20)) {
        score -= 0.3;
    }
    return Math.max(0, score);
}

function calculateActivityDiversity(activities: string[]): number {
    return activities ? activities.length / 10 : 0; // 归一化到0-1
}

function calculateMobilityScore(activity: any): number {
    const steps = activity.steps || 0;
    // 基于步数的移动性评分：0-1
    return Math.min(1.0, steps / 10000);
}

function calculateSleepQuality(sleep: any): number {
    // 基于翻身次数的睡眠质量指标
    const turnCount = sleep.turn_count || 0;
    if (turnCount < 5) return 1.0; // 优秀
    if (turnCount < 15) return 0.8; // 良好
    if (turnCount < 25) return 0.6; // 一般
    return 0.4; // 较差
}

function calculateComfortIndex(environment: any): number {
    let comfort = 1.0;
    const temp = environment.temperature || 22;
    const humidity = environment.humidity || 50;
    
    // 温度舒适度
    if (temp < 18 || temp > 26) comfort -= 0.3;
    // 湿度舒适度
    if (humidity < 30 || humidity > 70) comfort -= 0.3;
    
    return Math.max(0, comfort);
}

function calculateOverallQuality(cleanedData: any[]): number {
    if (!cleanedData.length) return 0;
    const sum = cleanedData.reduce((acc, d) => acc + (d.quality || 0), 0);
    return sum / cleanedData.length;
}
