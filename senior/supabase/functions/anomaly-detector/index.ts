// 异常检测系统 Edge Function
// 综合异常检测、多维度分析、智能预警

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
        const { user_id, detection_scope, time_window } = await req.json();

        if (!user_id) {
            throw new Error('缺少必需参数：user_id');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
        const aliApiKey = 'sk-71bb10435f134dfdab3a4b684e57b640';

        // 确定检测时间窗口
        const hours = time_window || 24;
        const startDate = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

        // 1. 获取多源数据
        const [healthData, sensorData, physiologicalData, behaviorData] = await Promise.all([
            fetchData(`${supabaseUrl}/rest/v1/health_data?user_id=eq.${user_id}&timestamp=gte.${startDate}&order=timestamp.desc&limit=500`, serviceRoleKey),
            fetchData(`${supabaseUrl}/rest/v1/sensor_data?user_id=eq.${user_id}&timestamp=gte.${startDate}&order=timestamp.desc&limit=500`, serviceRoleKey),
            fetchData(`${supabaseUrl}/rest/v1/physiological_analysis?user_id=eq.${user_id}&analyzed_at=gte.${startDate}&order=analyzed_at.desc&limit=50`, serviceRoleKey),
            fetchData(`${supabaseUrl}/rest/v1/behavior_patterns?user_id=eq.${user_id}&detection_timestamp=gte.${startDate}&order=detection_timestamp.desc&limit=50`, serviceRoleKey)
        ]);

        // 2. 多维度异常检测
        const anomalies: any = {
            vital_signs: detectVitalSignAnomalies(healthData),
            behavioral: detectBehavioralAnomalies(behaviorData),
            physiological: detectPhysiologicalAnomalies(physiologicalData),
            environmental: detectEnvironmentalAnomalies(sensorData),
            temporal: detectTemporalAnomalies(healthData, sensorData)
        };

        // 3. 异常优先级排序
        const prioritizedAnomalies = prioritizeAnomalies(anomalies);

        // 4. 关联分析（查找相关异常模式）
        const correlations = analyzeAnomalyCorrelations(anomalies);

        // 5. 生成异常报告
        const anomalyReport = generateAnomalyReport(prioritizedAnomalies, correlations);

        // 6. AI智能分析
        const aiAnalysis = await generateAnomalyAIAnalysis(
            prioritizedAnomalies,
            correlations,
            aliApiKey
        );

        // 7. 触发必要的预警
        const criticalAnomalies = prioritizedAnomalies.filter((a: any) => a.severity === 'critical');
        if (criticalAnomalies.length > 0) {
            await triggerAnomalyAlerts(user_id, criticalAnomalies, supabaseUrl, serviceRoleKey);
        }

        // 8. 保存检测结果
        await saveDetectionResults(
            user_id,
            anomalies,
            prioritizedAnomalies,
            correlations,
            supabaseUrl,
            serviceRoleKey
        );

        return new Response(JSON.stringify({
            data: {
                detection_summary: {
                    total_anomalies: prioritizedAnomalies.length,
                    critical: prioritizedAnomalies.filter((a: any) => a.severity === 'critical').length,
                    high: prioritizedAnomalies.filter((a: any) => a.severity === 'high').length,
                    medium: prioritizedAnomalies.filter((a: any) => a.severity === 'medium').length,
                    low: prioritizedAnomalies.filter((a: any) => a.severity === 'low').length
                },
                anomalies: prioritizedAnomalies,
                correlations: correlations,
                anomaly_report: anomalyReport,
                ai_analysis: aiAnalysis,
                alerts_triggered: criticalAnomalies.length,
                detection_scope: detection_scope || 'comprehensive',
                time_window_hours: hours,
                data_sources: {
                    health_data_points: healthData.length,
                    sensor_data_points: sensorData.length,
                    physiological_analyses: physiologicalData.length,
                    behavior_patterns: behaviorData.length
                },
                message: '异常检测完成'
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('异常检测错误:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'ANOMALY_DETECTION_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// 获取数据的辅助函数
async function fetchData(url: string, apikey: string): Promise<any[]> {
    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${apikey}`,
                'apikey': apikey
            }
        });
        return response.ok ? await response.json() : [];
    } catch (error) {
        return [];
    }
}

// 生命体征异常检测
function detectVitalSignAnomalies(healthData: any[]): any[] {
    const anomalies = [];

    // 心率异常
    const heartRateData = healthData.filter(d => d.data_type === 'heart_rate');
    heartRateData.forEach(d => {
        const hr = d.value;
        if (hr < 50) {
            anomalies.push({
                type: 'bradycardia',
                category: 'vital_signs',
                parameter: 'heart_rate',
                value: hr,
                threshold: 50,
                severity: hr < 40 ? 'critical' : 'high',
                timestamp: d.timestamp,
                description: '心率过低'
            });
        } else if (hr > 120) {
            anomalies.push({
                type: 'tachycardia',
                category: 'vital_signs',
                parameter: 'heart_rate',
                value: hr,
                threshold: 120,
                severity: hr > 150 ? 'critical' : 'high',
                timestamp: d.timestamp,
                description: '心率过高'
            });
        }
    });

    // 血压异常
    const bpData = healthData.filter(d => d.data_type === 'blood_pressure');
    bpData.forEach(d => {
        const systolic = d.value;
        const diastolic = d.diastolic_value || 0;
        
        if (systolic >= 180 || diastolic >= 120) {
            anomalies.push({
                type: 'hypertensive_crisis',
                category: 'vital_signs',
                parameter: 'blood_pressure',
                value: `${systolic}/${diastolic}`,
                threshold: '180/120',
                severity: 'critical',
                timestamp: d.timestamp,
                description: '高血压危象'
            });
        } else if (systolic < 90 || diastolic < 60) {
            anomalies.push({
                type: 'hypotension',
                category: 'vital_signs',
                parameter: 'blood_pressure',
                value: `${systolic}/${diastolic}`,
                threshold: '90/60',
                severity: 'high',
                timestamp: d.timestamp,
                description: '血压过低'
            });
        }
    });

    // 血糖异常
    const glucoseData = healthData.filter(d => d.data_type === 'blood_glucose');
    glucoseData.forEach(d => {
        const glucose = d.value;
        if (glucose < 3.9) {
            anomalies.push({
                type: 'hypoglycemia',
                category: 'vital_signs',
                parameter: 'blood_glucose',
                value: glucose,
                threshold: 3.9,
                severity: glucose < 2.8 ? 'critical' : 'high',
                timestamp: d.timestamp,
                description: '低血糖'
            });
        } else if (glucose > 13.9) {
            anomalies.push({
                type: 'hyperglycemia',
                category: 'vital_signs',
                parameter: 'blood_glucose',
                value: glucose,
                threshold: 13.9,
                severity: glucose > 16.7 ? 'critical' : 'medium',
                timestamp: d.timestamp,
                description: '高血糖'
            });
        }
    });

    return anomalies;
}

// 行为异常检测
function detectBehavioralAnomalies(behaviorData: any[]): any[] {
    const anomalies = [];

    behaviorData.forEach(pattern => {
        // 认知评分异常
        if (pattern.cognitive_score && pattern.cognitive_score < 0.6) {
            anomalies.push({
                type: 'cognitive_decline',
                category: 'behavioral',
                parameter: 'cognitive_score',
                value: pattern.cognitive_score,
                threshold: 0.6,
                severity: pattern.cognitive_score < 0.4 ? 'high' : 'medium',
                timestamp: pattern.detection_timestamp,
                description: '认知能力下降'
            });
        }

        // 异常行为
        if (pattern.abnormal_behaviors && Array.isArray(pattern.abnormal_behaviors.details)) {
            pattern.abnormal_behaviors.details.forEach((behavior: any) => {
                anomalies.push({
                    type: behavior.type || 'behavior_change',
                    category: 'behavioral',
                    parameter: 'behavior_pattern',
                    value: behavior.description,
                    severity: behavior.severity || 'medium',
                    timestamp: pattern.detection_timestamp,
                    description: behavior.description
                });
            });
        }
    });

    return anomalies;
}

// 生理分析异常检测
function detectPhysiologicalAnomalies(physiologicalData: any[]): any[] {
    const anomalies = [];

    physiologicalData.forEach(analysis => {
        // HRV异常
        if (analysis.heart_rate_variability?.hrv_score && analysis.heart_rate_variability.hrv_score < 40) {
            anomalies.push({
                type: 'low_hrv',
                category: 'physiological',
                parameter: 'hrv_score',
                value: analysis.heart_rate_variability.hrv_score,
                threshold: 40,
                severity: 'medium',
                timestamp: analysis.analyzed_at,
                description: '心率变异性过低'
            });
        }

        // 睡眠质量异常
        if (analysis.sleep_quality_score && analysis.sleep_quality_score < 0.5) {
            anomalies.push({
                type: 'poor_sleep',
                category: 'physiological',
                parameter: 'sleep_quality',
                value: analysis.sleep_quality_score,
                threshold: 0.5,
                severity: 'medium',
                timestamp: analysis.analyzed_at,
                description: '睡眠质量较差'
            });
        }

        // 已检测到的异常
        if (analysis.anomaly_detected && analysis.anomaly_details?.details) {
            analysis.anomaly_details.details.forEach((detail: any) => {
                anomalies.push({
                    type: detail.type,
                    category: 'physiological',
                    parameter: detail.type,
                    value: detail.values || detail.description,
                    severity: detail.severity,
                    timestamp: analysis.analyzed_at,
                    description: detail.description
                });
            });
        }
    });

    return anomalies;
}

// 环境异常检测
function detectEnvironmentalAnomalies(sensorData: any[]): any[] {
    const anomalies = [];

    const envData = sensorData.filter(d => d.device_type === 'environment');

    envData.forEach(d => {
        const value = d.data_value;
        
        // 温度异常
        if (value?.temperature !== undefined) {
            if (value.temperature < 16 || value.temperature > 30) {
                anomalies.push({
                    type: 'temperature_extreme',
                    category: 'environmental',
                    parameter: 'temperature',
                    value: value.temperature,
                    threshold: '16-30',
                    severity: 'low',
                    timestamp: d.timestamp,
                    description: '环境温度异常'
                });
            }
        }

        // 湿度异常
        if (value?.humidity !== undefined) {
            if (value.humidity < 30 || value.humidity > 70) {
                anomalies.push({
                    type: 'humidity_extreme',
                    category: 'environmental',
                    parameter: 'humidity',
                    value: value.humidity,
                    threshold: '30-70',
                    severity: 'low',
                    timestamp: d.timestamp,
                    description: '环境湿度异常'
                });
            }
        }
    });

    return anomalies;
}

// 时间模式异常检测
function detectTemporalAnomalies(healthData: any[], sensorData: any[]): any[] {
    const anomalies = [];

    // 检测夜间异常活动
    const nightData = sensorData.filter(d => {
        const hour = new Date(d.timestamp).getHours();
        return hour >= 0 && hour <= 5;
    });

    if (nightData.length > 10) {
        anomalies.push({
            type: 'night_activity',
            category: 'temporal',
            parameter: 'activity_timing',
            value: nightData.length,
            threshold: 10,
            severity: 'medium',
            timestamp: new Date().toISOString(),
            description: '夜间活动频繁'
        });
    }

    // 检测数据缺失
    const expectedDataPoints = 24; // 假设每小时一个数据点
    if (healthData.length < expectedDataPoints * 0.5) {
        anomalies.push({
            type: 'data_gap',
            category: 'temporal',
            parameter: 'data_continuity',
            value: healthData.length,
            threshold: expectedDataPoints,
            severity: 'low',
            timestamp: new Date().toISOString(),
            description: '数据收集不完整'
        });
    }

    return anomalies;
}

// 异常优先级排序
function prioritizeAnomalies(anomalies: any): any[] {
    const allAnomalies = [
        ...anomalies.vital_signs,
        ...anomalies.behavioral,
        ...anomalies.physiological,
        ...anomalies.environmental,
        ...anomalies.temporal
    ];

    // 按严重程度排序
    const severityOrder: any = { critical: 0, high: 1, medium: 2, low: 3 };
    
    return allAnomalies.sort((a, b) => {
        const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
        if (severityDiff !== 0) return severityDiff;
        
        // 相同严重程度，按时间排序（最新的优先）
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });
}

// 关联分析
function analyzeAnomalyCorrelations(anomalies: any): any[] {
    const correlations = [];

    // 查找同时发生的异常
    const vitalAnomalies = anomalies.vital_signs;
    const behavioralAnomalies = anomalies.behavioral;

    // 例如：心率异常 + 活动异常 = 可能的心脏问题
    if (vitalAnomalies.some((a: any) => a.parameter === 'heart_rate') &&
        behavioralAnomalies.some((a: any) => a.type === 'reduced_activity')) {
        correlations.push({
            pattern: 'cardiac_concern',
            involved_anomalies: ['heart_rate', 'reduced_activity'],
            confidence: 0.75,
            recommendation: '建议进行心脏功能评估'
        });
    }

    // 血压异常 + 睡眠质量差 = 可能的心血管风险
    if (vitalAnomalies.some((a: any) => a.parameter === 'blood_pressure') &&
        anomalies.physiological.some((a: any) => a.type === 'poor_sleep')) {
        correlations.push({
            pattern: 'cardiovascular_risk',
            involved_anomalies: ['blood_pressure', 'poor_sleep'],
            confidence: 0.70,
            recommendation: '建议监测心血管健康'
        });
    }

    return correlations;
}

// 生成异常报告
function generateAnomalyReport(anomalies: any[], correlations: any[]): any {
    return {
        summary: {
            total_anomalies: anomalies.length,
            by_severity: {
                critical: anomalies.filter(a => a.severity === 'critical').length,
                high: anomalies.filter(a => a.severity === 'high').length,
                medium: anomalies.filter(a => a.severity === 'medium').length,
                low: anomalies.filter(a => a.severity === 'low').length
            },
            by_category: {
                vital_signs: anomalies.filter(a => a.category === 'vital_signs').length,
                behavioral: anomalies.filter(a => a.category === 'behavioral').length,
                physiological: anomalies.filter(a => a.category === 'physiological').length,
                environmental: anomalies.filter(a => a.category === 'environmental').length,
                temporal: anomalies.filter(a => a.category === 'temporal').length
            }
        },
        top_concerns: anomalies.slice(0, 5),
        correlations: correlations,
        overall_risk: calculateOverallRisk(anomalies),
        recommendations: generateRecommendations(anomalies, correlations)
    };
}

// AI异常分析
async function generateAnomalyAIAnalysis(
    anomalies: any[],
    correlations: any[],
    apiKey: string
): Promise<string> {
    if (anomalies.length === 0) {
        return '未检测到显著异常，健康状况良好。建议继续保持良好的生活习惯和定期监测。';
    }

    const topAnomalies = anomalies.slice(0, 5);
    const anomalySummary = topAnomalies.map(a => 
        `${a.description}(${a.severity}): ${a.value}`
    ).join('\n');

    const prompt = `作为AI健康异常分析专家，请分析以下检测到的异常情况：

检测到${anomalies.length}项异常，主要包括：
${anomalySummary}

${correlations.length > 0 ? `发现${correlations.length}个异常关联模式：\n${correlations.map(c => c.recommendation).join('\n')}` : ''}

请提供简明分析（80字以内）：
1. 异常严重程度评估
2. 主要健康风险
3. 2条紧急建议`;

    try {
        const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: 'qwen-plus',
                messages: [
                    { role: 'system', content: '你是专业的健康异常分析专家。' },
                    { role: 'user', content: prompt }
                ],
                max_tokens: 300
            })
        });

        if (!response.ok) {
            return '检测到多项异常，建议及时就医检查。';
        }

        const result = await response.json();
        return result.choices?.[0]?.message?.content || '异常检测完成，请关注健康状况。';
    } catch (error) {
        return '异常数据已记录，建议咨询医疗专业人员。';
    }
}

// 触发异常预警
async function triggerAnomalyAlerts(
    userId: string,
    criticalAnomalies: any[],
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    const alerts = criticalAnomalies.map(anomaly => ({
        user_id: userId,
        alert_type: 'anomaly_detection',
        severity: 'critical',
        title: anomaly.description,
        description: `检测到${anomaly.parameter}异常：${anomaly.value}，超过阈值${anomaly.threshold}`,
        risk_score: 0.9,
        recommended_action: '建议立即就医或联系医护人员',
        status: 'active',
        priority: 'urgent'
    }));

    try {
        await fetch(`${supabaseUrl}/rest/v1/health_alerts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alerts)
        });
    } catch (error) {
        console.error('触发异常预警失败:', error);
    }
}

// 保存检测结果
async function saveDetectionResults(
    userId: string,
    anomalies: any,
    prioritized: any[],
    correlations: any[],
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    const record = {
        user_id: userId,
        device_type: 'anomaly_detector',
        device_id: 'comprehensive_v1',
        sensor_type: 'anomaly_detection',
        data_value: {
            anomalies_by_category: anomalies,
            prioritized_anomalies: prioritized,
            correlations: correlations,
            total_count: prioritized.length
        },
        quality_score: 1.0,
        timestamp: new Date().toISOString()
    };

    try {
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
        console.error('保存检测结果失败:', error);
    }
}

// 辅助函数
function calculateOverallRisk(anomalies: any[]): string {
    const criticalCount = anomalies.filter(a => a.severity === 'critical').length;
    const highCount = anomalies.filter(a => a.severity === 'high').length;
    
    if (criticalCount > 0) return 'critical';
    if (highCount >= 3) return 'high';
    if (highCount > 0 || anomalies.length >= 5) return 'medium';
    return 'low';
}

function generateRecommendations(anomalies: any[], correlations: any[]): string[] {
    const recommendations = [];
    
    if (anomalies.some(a => a.severity === 'critical')) {
        recommendations.push('建议立即就医或联系急救服务');
    }
    
    if (anomalies.some(a => a.category === 'vital_signs')) {
        recommendations.push('密切监测生命体征变化');
    }
    
    if (correlations.length > 0) {
        recommendations.push(correlations[0].recommendation);
    }
    
    recommendations.push('保持日常健康监测和规律作息');
    
    return recommendations;
}
