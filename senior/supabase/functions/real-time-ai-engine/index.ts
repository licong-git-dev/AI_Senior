// 实时AI分析引擎 Edge Function
// 边缘计算优化、实时推理、快速响应（延迟<100ms目标）

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

    const startTime = Date.now();

    try {
        const { user_id, real_time_data, analysis_type } = await req.json();

        if (!user_id || !real_time_data) {
            throw new Error('缺少必需参数：user_id 和 real_time_data');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

        // 1. 实时数据预处理（边缘计算优化）
        const preprocessedData = preprocessRealTimeData(real_time_data);

        // 2. 快速特征提取
        const features = extractFeaturesRealTime(preprocessedData);

        // 3. 实时推理（使用轻量级模型）
        const inference = performRealTimeInference(features, analysis_type);

        // 4. 快速风险评估
        const riskAssessment = assessRiskRealTime(inference, preprocessedData);

        // 5. 如果检测到异常，立即触发预警
        if (riskAssessment.alert_required) {
            await triggerImmediateAlert(user_id, riskAssessment, supabaseUrl, serviceRoleKey);
        }

        // 6. 异步保存分析结果（不阻塞响应）
        saveAnalysisAsync(user_id, preprocessedData, inference, riskAssessment, supabaseUrl, serviceRoleKey);

        const processingTime = Date.now() - startTime;

        return new Response(JSON.stringify({
            data: {
                real_time_inference: inference,
                risk_assessment: riskAssessment,
                features: features,
                alert_triggered: riskAssessment.alert_required,
                processing_time_ms: processingTime,
                performance: {
                    target_met: processingTime < 100,
                    latency_ms: processingTime,
                    optimization_level: 'edge_computing'
                },
                timestamp: new Date().toISOString(),
                message: '实时分析完成'
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        const processingTime = Date.now() - startTime;
        console.error('实时AI分析错误:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'REALTIME_ANALYSIS_FAILED',
                message: error.message,
                processing_time_ms: processingTime
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// 实时数据预处理（边缘计算优化）
function preprocessRealTimeData(rawData: any): any {
    const processed: any = {
        vital_signs: {},
        activity: {},
        environment: {},
        timestamp: new Date().toISOString(),
        data_quality: 1.0
    };

    // 提取生命体征
    if (rawData.heart_rate !== undefined) {
        processed.vital_signs.heart_rate = rawData.heart_rate;
        processed.vital_signs.heart_rate_valid = rawData.heart_rate >= 40 && rawData.heart_rate <= 180;
    }

    if (rawData.blood_pressure) {
        processed.vital_signs.systolic = rawData.blood_pressure.systolic;
        processed.vital_signs.diastolic = rawData.blood_pressure.diastolic;
        processed.vital_signs.bp_valid = 
            rawData.blood_pressure.systolic >= 80 && 
            rawData.blood_pressure.systolic <= 200 &&
            rawData.blood_pressure.diastolic >= 50 &&
            rawData.blood_pressure.diastolic <= 130;
    }

    if (rawData.spo2 !== undefined) {
        processed.vital_signs.spo2 = rawData.spo2;
        processed.vital_signs.spo2_valid = rawData.spo2 >= 80 && rawData.spo2 <= 100;
    }

    if (rawData.temperature !== undefined) {
        processed.vital_signs.temperature = rawData.temperature;
        processed.vital_signs.temp_valid = rawData.temperature >= 35 && rawData.temperature <= 42;
    }

    // 提取活动数据
    if (rawData.activity) {
        processed.activity = {
            type: rawData.activity.type || 'unknown',
            intensity: rawData.activity.intensity || 0,
            duration: rawData.activity.duration || 0,
            steps: rawData.activity.steps || 0
        };
    }

    // 提取环境数据
    if (rawData.environment) {
        processed.environment = {
            temperature: rawData.environment.temperature,
            humidity: rawData.environment.humidity,
            light: rawData.environment.light
        };
    }

    // 计算数据质量分数
    const validFields = Object.values(processed.vital_signs)
        .filter(v => typeof v === 'boolean' && v === true).length;
    const totalFields = Object.keys(processed.vital_signs).filter(k => k.includes('_valid')).length;
    processed.data_quality = totalFields > 0 ? validFields / totalFields : 1.0;

    return processed;
}

// 快速特征提取
function extractFeaturesRealTime(data: any): any {
    const features: any = {
        vital_features: [],
        activity_features: [],
        risk_indicators: []
    };

    // 生命体征特征
    if (data.vital_signs.heart_rate !== undefined) {
        features.vital_features.push({
            name: 'heart_rate',
            value: data.vital_signs.heart_rate,
            normalized: normalizeHeartRate(data.vital_signs.heart_rate),
            risk_score: assessHeartRateRisk(data.vital_signs.heart_rate)
        });
    }

    if (data.vital_signs.systolic !== undefined) {
        features.vital_features.push({
            name: 'blood_pressure',
            value: `${data.vital_signs.systolic}/${data.vital_signs.diastolic}`,
            normalized: normalizeBloodPressure(data.vital_signs.systolic),
            risk_score: assessBloodPressureRisk(data.vital_signs.systolic, data.vital_signs.diastolic)
        });
    }

    if (data.vital_signs.spo2 !== undefined) {
        features.vital_features.push({
            name: 'spo2',
            value: data.vital_signs.spo2,
            normalized: data.vital_signs.spo2 / 100,
            risk_score: assessSpO2Risk(data.vital_signs.spo2)
        });
    }

    // 活动特征
    if (data.activity.intensity !== undefined) {
        features.activity_features.push({
            name: 'activity_intensity',
            value: data.activity.intensity,
            level: classifyActivityLevel(data.activity.intensity)
        });
    }

    // 综合风险指标
    const avgRiskScore = features.vital_features.reduce((sum: number, f: any) => 
        sum + f.risk_score, 0
    ) / (features.vital_features.length || 1);

    features.risk_indicators.push({
        overall_risk: avgRiskScore,
        risk_level: avgRiskScore > 0.7 ? 'high' : avgRiskScore > 0.4 ? 'medium' : 'low',
        data_quality: data.data_quality
    });

    return features;
}

// 实时推理（轻量级模型）
function performRealTimeInference(features: any, analysisType: string): any {
    const inference: any = {
        model_version: 'lightweight_v1',
        inference_time_ms: 0,
        results: {}
    };

    const inferenceStart = Date.now();

    // 健康状态推理
    if (analysisType === 'health_status' || analysisType === 'all') {
        const vitalScores = features.vital_features.map((f: any) => 1 - f.risk_score);
        const avgScore = vitalScores.reduce((a: number, b: number) => a + b, 0) / (vitalScores.length || 1);
        
        inference.results.health_status = {
            score: Math.round(avgScore * 100) / 100,
            status: avgScore > 0.8 ? 'excellent' : avgScore > 0.6 ? 'good' : avgScore > 0.4 ? 'fair' : 'poor',
            confidence: features.risk_indicators[0]?.data_quality || 0.9
        };
    }

    // 异常检测推理
    if (analysisType === 'anomaly_detection' || analysisType === 'all') {
        const anomalies = [];
        
        for (const feature of features.vital_features) {
            if (feature.risk_score > 0.7) {
                anomalies.push({
                    parameter: feature.name,
                    value: feature.value,
                    severity: feature.risk_score > 0.9 ? 'critical' : 'high',
                    action_required: true
                });
            }
        }

        inference.results.anomaly_detection = {
            anomalies_detected: anomalies.length,
            anomalies: anomalies,
            requires_attention: anomalies.length > 0
        };
    }

    // 活动评估推理
    if (analysisType === 'activity_assessment' || analysisType === 'all') {
        const activityFeature = features.activity_features[0];
        
        inference.results.activity_assessment = {
            level: activityFeature?.level || 'unknown',
            recommendation: generateActivityRecommendation(activityFeature?.level),
            suitable_for_age_group: 'elderly'
        };
    }

    inference.inference_time_ms = Date.now() - inferenceStart;

    return inference;
}

// 快速风险评估
function assessRiskRealTime(inference: any, data: any): any {
    const assessment: any = {
        overall_risk_level: 'low',
        risk_score: 0,
        alert_required: false,
        immediate_actions: [],
        monitoring_recommendations: []
    };

    // 检查健康状态
    if (inference.results.health_status) {
        const status = inference.results.health_status.status;
        if (status === 'poor') {
            assessment.risk_score += 0.4;
            assessment.immediate_actions.push('建议立即联系医护人员');
        } else if (status === 'fair') {
            assessment.risk_score += 0.2;
            assessment.monitoring_recommendations.push('密切监测健康状况');
        }
    }

    // 检查异常
    if (inference.results.anomaly_detection?.anomalies_detected > 0) {
        const anomalies = inference.results.anomaly_detection.anomalies;
        const criticalAnomalies = anomalies.filter((a: any) => a.severity === 'critical');
        
        if (criticalAnomalies.length > 0) {
            assessment.risk_score += 0.5;
            assessment.alert_required = true;
            assessment.immediate_actions.push('检测到严重异常，需要紧急处理');
            
            criticalAnomalies.forEach((a: any) => {
                assessment.immediate_actions.push(`${a.parameter}: ${a.value}`);
            });
        } else {
            assessment.risk_score += 0.2;
            assessment.monitoring_recommendations.push('发现异常指标，建议复查');
        }
    }

    // 确定风险等级
    assessment.overall_risk_level = 
        assessment.risk_score >= 0.7 ? 'critical' :
        assessment.risk_score >= 0.4 ? 'high' :
        assessment.risk_score >= 0.2 ? 'medium' : 'low';

    // 如果是高风险或危急，触发警报
    if (assessment.overall_risk_level === 'high' || assessment.overall_risk_level === 'critical') {
        assessment.alert_required = true;
    }

    return assessment;
}

// 立即触发预警
async function triggerImmediateAlert(
    userId: string,
    riskAssessment: any,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    const alertRecord = {
        user_id: userId,
        alert_type: 'real_time_anomaly',
        severity: riskAssessment.overall_risk_level,
        title: '实时健康异常检测',
        description: riskAssessment.immediate_actions.join('; '),
        risk_score: riskAssessment.risk_score,
        recommended_action: riskAssessment.immediate_actions[0] || '请联系医护人员',
        status: 'active',
        priority: riskAssessment.overall_risk_level === 'critical' ? 'urgent' : 'high'
    };

    try {
        await fetch(`${supabaseUrl}/rest/v1/health_alerts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertRecord)
        });
    } catch (error) {
        console.error('触发预警失败:', error);
    }
}

// 异步保存分析结果
function saveAnalysisAsync(
    userId: string,
    data: any,
    inference: any,
    risk: any,
    supabaseUrl: string,
    serviceRoleKey: string
): void {
    // 使用setTimeout确保不阻塞主响应
    setTimeout(async () => {
        try {
            const record = {
                user_id: userId,
                device_type: 'real_time_analyzer',
                device_id: 'ai_engine_v1',
                sensor_type: 'ai_analysis',
                data_value: {
                    preprocessed_data: data,
                    inference_results: inference,
                    risk_assessment: risk
                },
                quality_score: data.data_quality,
                timestamp: new Date().toISOString()
            };

            await fetch(`${supabaseUrl}/rest/v1/sensor_data`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(record)
            });
        } catch (error) {
            console.error('异步保存失败:', error);
        }
    }, 0);
}

// 辅助函数
function normalizeHeartRate(hr: number): number {
    // 正常范围：60-100 bpm
    if (hr < 60) return (hr - 40) / 20; // 40-60映射到0-1
    if (hr > 100) return 1 - ((hr - 100) / 80); // 100-180映射到1-0
    return 1.0; // 正常范围
}

function normalizeBloodPressure(systolic: number): number {
    // 正常范围：90-120 mmHg
    if (systolic < 90) return systolic / 90;
    if (systolic > 120) return 1 - ((systolic - 120) / 80);
    return 1.0;
}

function assessHeartRateRisk(hr: number): number {
    if (hr < 50 || hr > 120) return 0.9;
    if (hr < 55 || hr > 110) return 0.7;
    if (hr < 60 || hr > 100) return 0.3;
    return 0.1;
}

function assessBloodPressureRisk(systolic: number, diastolic: number): number {
    if (systolic >= 180 || diastolic >= 120) return 1.0;
    if (systolic >= 160 || diastolic >= 100) return 0.8;
    if (systolic >= 140 || diastolic >= 90) return 0.6;
    if (systolic < 90 || diastolic < 60) return 0.7;
    return 0.1;
}

function assessSpO2Risk(spo2: number): number {
    if (spo2 < 90) return 1.0;
    if (spo2 < 94) return 0.7;
    if (spo2 < 96) return 0.3;
    return 0.1;
}

function classifyActivityLevel(intensity: number): string {
    if (intensity >= 0.7) return 'high';
    if (intensity >= 0.4) return 'moderate';
    if (intensity >= 0.1) return 'light';
    return 'sedentary';
}

function generateActivityRecommendation(level: string): string {
    switch (level) {
        case 'high':
            return '活动强度较高，注意适度休息';
        case 'moderate':
            return '活动强度适中，继续保持';
        case 'light':
            return '建议适当增加活动量';
        case 'sedentary':
            return '活动量偏低，建议增加日常活动';
        default:
            return '保持规律的身体活动';
    }
}
