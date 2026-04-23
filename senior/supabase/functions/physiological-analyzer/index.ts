// 生理数据融合分析 Edge Function
// 心率变异分析、血压预测、睡眠质量评估、生理指标异常检测

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
        const { user_id, analysis_type, time_range } = await req.json();

        if (!user_id) {
            throw new Error('缺少必需参数：user_id');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
        const aliApiKey = 'sk-71bb10435f134dfdab3a4b684e57b640'; // 阿里云API Key

        // 1. 获取用户健康数据
        const startDate = time_range?.start || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
        const endDate = time_range?.end || new Date().toISOString();

        const healthDataResponse = await fetch(
            `${supabaseUrl}/rest/v1/health_data?user_id=eq.${user_id}&timestamp=gte.${startDate}&timestamp=lte.${endDate}&order=timestamp.desc&limit=500`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                }
            }
        );

        if (!healthDataResponse.ok) {
            throw new Error('获取健康数据失败');
        }

        const healthData = await healthDataResponse.json();

        // 2. 心率变异性分析（HRV）
        const hrvAnalysis = analyzeHeartRateVariability(healthData);

        // 3. 血压预测（基于历史数据的趋势分析）
        const bloodPressurePrediction = predictBloodPressure(healthData);

        // 4. 睡眠质量评估
        const sleepQualityScore = assessSleepQuality(healthData);

        // 5. 异常检测
        const anomalyDetection = detectAnomalies(healthData, hrvAnalysis, bloodPressurePrediction);

        // 6. 使用AI生成综合健康分析报告
        const aiAnalysis = await generateAIAnalysis(
            user_id,
            hrvAnalysis,
            bloodPressurePrediction,
            sleepQualityScore,
            anomalyDetection,
            aliApiKey
        );

        // 7. 保存分析结果到数据库
        const analysisRecord = {
            user_id,
            analysis_type: analysis_type || 'comprehensive',
            heart_rate_variability: hrvAnalysis,
            blood_pressure_prediction: bloodPressurePrediction,
            sleep_quality_score: sleepQualityScore.score,
            anomaly_detected: anomalyDetection.detected,
            anomaly_details: anomalyDetection.details,
            risk_level: calculateRiskLevel(anomalyDetection, hrvAnalysis, bloodPressurePrediction),
            confidence_score: calculateConfidenceScore(healthData.length),
            data_range_start: startDate,
            data_range_end: endDate,
        };

        const saveResponse = await fetch(
            `${supabaseUrl}/rest/v1/physiological_analysis`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify(analysisRecord)
            }
        );

        if (!saveResponse.ok) {
            const errorText = await saveResponse.text();
            console.error('保存分析结果失败:', errorText);
        }

        const savedData = await saveResponse.json();

        return new Response(JSON.stringify({
            data: {
                analysis_id: savedData[0]?.id,
                heart_rate_variability: hrvAnalysis,
                blood_pressure_prediction: bloodPressurePrediction,
                sleep_quality: sleepQualityScore,
                anomaly_detection: anomalyDetection,
                risk_level: analysisRecord.risk_level,
                confidence_score: analysisRecord.confidence_score,
                ai_insights: aiAnalysis,
                data_points_analyzed: healthData.length,
                analysis_period: {
                    start: startDate,
                    end: endDate
                },
                message: '生理数据分析完成'
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('生理数据分析错误:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'PHYSIOLOGICAL_ANALYSIS_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// 心率变异性分析（HRV）
function analyzeHeartRateVariability(healthData: any[]): any {
    const heartRateData = healthData
        .filter(d => d.data_type === 'heart_rate')
        .map(d => d.value)
        .filter(v => v != null && v > 0);

    if (heartRateData.length < 2) {
        return {
            status: 'insufficient_data',
            message: '心率数据不足，无法进行HRV分析'
        };
    }

    // 计算RR间期（心跳间隔）
    const rrIntervals = [];
    for (let i = 1; i < heartRateData.length; i++) {
        const rr = 60000 / heartRateData[i]; // 转换为毫秒
        rrIntervals.push(rr);
    }

    // SDNN（RR间期标准差）
    const sdnn = calculateStandardDeviation(rrIntervals);

    // RMSSD（相邻RR间期差值的均方根）
    const differences = [];
    for (let i = 1; i < rrIntervals.length; i++) {
        differences.push(Math.pow(rrIntervals[i] - rrIntervals[i - 1], 2));
    }
    const rmssd = Math.sqrt(differences.reduce((a, b) => a + b, 0) / differences.length);

    // HRV评分（0-100）
    const hrvScore = calculateHRVScore(sdnn, rmssd);

    return {
        status: 'analyzed',
        sdnn: Math.round(sdnn * 100) / 100,
        rmssd: Math.round(rmssd * 100) / 100,
        hrv_score: hrvScore,
        interpretation: interpretHRVScore(hrvScore),
        data_points: heartRateData.length,
        avg_heart_rate: Math.round(heartRateData.reduce((a, b) => a + b, 0) / heartRateData.length),
        heart_rate_range: {
            min: Math.min(...heartRateData),
            max: Math.max(...heartRateData)
        }
    };
}

// 血压预测（基于历史趋势）
function predictBloodPressure(healthData: any[]): any {
    const bpData = healthData
        .filter(d => d.data_type === 'blood_pressure')
        .map(d => ({
            systolic: d.value,
            diastolic: d.diastolic_value || 0,
            timestamp: new Date(d.timestamp).getTime()
        }))
        .filter(d => d.systolic > 0 && d.diastolic > 0)
        .sort((a, b) => a.timestamp - b.timestamp);

    if (bpData.length < 3) {
        return {
            status: 'insufficient_data',
            message: '血压数据不足，无法进行预测'
        };
    }

    // 简单线性回归预测
    const systolicTrend = calculateTrend(bpData.map(d => d.systolic));
    const diastolicTrend = calculateTrend(bpData.map(d => d.diastolic));

    // 预测未来7天的血压
    const predictions = [];
    const latestSystolic = bpData[bpData.length - 1].systolic;
    const latestDiastolic = bpData[bpData.length - 1].diastolic;

    for (let i = 1; i <= 7; i++) {
        predictions.push({
            day: i,
            predicted_systolic: Math.round(latestSystolic + systolicTrend * i),
            predicted_diastolic: Math.round(latestDiastolic + diastolicTrend * i),
            confidence: calculatePredictionConfidence(bpData.length, i)
        });
    }

    return {
        status: 'predicted',
        current: {
            systolic: latestSystolic,
            diastolic: latestDiastolic
        },
        trend: {
            systolic: systolicTrend > 0 ? 'increasing' : systolicTrend < 0 ? 'decreasing' : 'stable',
            diastolic: diastolicTrend > 0 ? 'increasing' : diastolicTrend < 0 ? 'decreasing' : 'stable'
        },
        predictions,
        risk_assessment: assessBloodPressureRisk(predictions[6]) // 7天后的预测
    };
}

// 睡眠质量评估
function assessSleepQuality(healthData: any[]): any {
    const sleepData = healthData.filter(d => d.data_type === 'sleep_hours');

    if (sleepData.length === 0) {
        return {
            status: 'no_data',
            score: 0,
            message: '无睡眠数据'
        };
    }

    const avgSleepHours = sleepData.reduce((sum, d) => sum + (d.value || 0), 0) / sleepData.length;
    const sleepConsistency = 1 - calculateStandardDeviation(sleepData.map(d => d.value)) / avgSleepHours;

    // 睡眠质量评分（0-1）
    let score = 0;
    
    // 睡眠时长评分（7-9小时最佳）
    if (avgSleepHours >= 7 && avgSleepHours <= 9) {
        score += 0.5;
    } else if (avgSleepHours >= 6 && avgSleepHours <= 10) {
        score += 0.3;
    } else {
        score += 0.1;
    }

    // 睡眠一致性评分
    score += Math.max(0, sleepConsistency) * 0.5;

    return {
        status: 'assessed',
        score: Math.round(score * 100) / 100,
        avg_sleep_hours: Math.round(avgSleepHours * 10) / 10,
        consistency_score: Math.round(sleepConsistency * 100) / 100,
        interpretation: interpretSleepScore(score),
        recommendations: generateSleepRecommendations(avgSleepHours, sleepConsistency)
    };
}

// 异常检测
function detectAnomalies(healthData: any[], hrvAnalysis: any, bpPrediction: any): any {
    const anomalies = [];

    // 心率异常
    const heartRates = healthData
        .filter(d => d.data_type === 'heart_rate')
        .map(d => d.value);
    
    if (heartRates.some(hr => hr < 50 || hr > 120)) {
        anomalies.push({
            type: 'heart_rate',
            severity: 'high',
            description: '检测到异常心率值',
            values: heartRates.filter(hr => hr < 50 || hr > 120)
        });
    }

    // HRV异常
    if (hrvAnalysis.status === 'analyzed' && hrvAnalysis.hrv_score < 40) {
        anomalies.push({
            type: 'hrv',
            severity: 'medium',
            description: '心率变异性较低，可能提示压力或疲劳',
            hrv_score: hrvAnalysis.hrv_score
        });
    }

    // 血压异常
    if (bpPrediction.status === 'predicted') {
        const lastPrediction = bpPrediction.predictions[bpPrediction.predictions.length - 1];
        if (lastPrediction.predicted_systolic > 140 || lastPrediction.predicted_diastolic > 90) {
            anomalies.push({
                type: 'blood_pressure',
                severity: 'high',
                description: '预测显示血压可能升高',
                predicted_values: lastPrediction
            });
        }
    }

    return {
        detected: anomalies.length > 0,
        count: anomalies.length,
        details: anomalies,
        timestamp: new Date().toISOString()
    };
}

// AI综合分析
async function generateAIAnalysis(
    userId: string,
    hrv: any,
    bp: any,
    sleep: any,
    anomaly: any,
    apiKey: string
): Promise<string> {
    const prompt = `作为专业的健康分析AI，请基于以下老年人健康监测数据提供综合分析和建议：

心率变异性分析：
- HRV评分：${hrv.hrv_score || '无数据'}
- 平均心率：${hrv.avg_heart_rate || '无数据'} bpm
- 解读：${hrv.interpretation || '无数据'}

血压预测：
- 当前血压：${bp.current?.systolic}/${bp.current?.diastolic} mmHg
- 趋势：收缩压${bp.trend?.systolic}，舒张压${bp.trend?.diastolic}
- 风险评估：${bp.risk_assessment || '无'}

睡眠质量：
- 评分：${sleep.score}
- 平均睡眠时长：${sleep.avg_sleep_hours}小时
- 解读：${sleep.interpretation}

异常检测：
${anomaly.detected ? `检测到${anomaly.count}项异常：\n${anomaly.details.map((a: any) => `- ${a.description}`).join('\n')}` : '未检测到异常'}

请提供：
1. 整体健康状况评估（50字以内）
2. 主要风险提示（如有，30字以内）
3. 个性化健康建议（3条，每条20字以内）`;

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
                    { role: 'system', content: '你是专业的老年健康分析专家，擅长解读生理数据并提供实用建议。' },
                    { role: 'user', content: prompt }
                ],
                max_tokens: 500,
                temperature: 0.7
            })
        });

        if (!response.ok) {
            return '健康状况总体平稳，建议继续保持良好的生活习惯，定期监测健康指标。';
        }

        const result = await response.json();
        return result.choices?.[0]?.message?.content || '分析完成，请参考各项指标。';
    } catch (error) {
        console.error('AI分析调用失败:', error);
        return '健康数据已记录，建议定期复查并保持良好生活习惯。';
    }
}

// 辅助函数
function calculateStandardDeviation(values: number[]): number {
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const squareDiffs = values.map(v => Math.pow(v - avg, 2));
    const variance = squareDiffs.reduce((a, b) => a + b, 0) / values.length;
    return Math.sqrt(variance);
}

function calculateHRVScore(sdnn: number, rmssd: number): number {
    // HRV评分算法（0-100）
    const sdnnScore = Math.min(100, (sdnn / 50) * 50);
    const rmssdScore = Math.min(100, (rmssd / 42) * 50);
    return Math.round(sdnnScore + rmssdScore);
}

function interpretHRVScore(score: number): string {
    if (score >= 80) return '优秀：心脏功能良好，自主神经系统平衡';
    if (score >= 60) return '良好：整体状况不错，继续保持';
    if (score >= 40) return '一般：建议改善生活方式，减少压力';
    return '较差：建议就医检查，关注心脏健康';
}

function calculateTrend(values: number[]): number {
    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = values.reduce((sum, y, x) => sum + x * y, 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;
    
    return (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
}

function calculatePredictionConfidence(dataPoints: number, daysAhead: number): number {
    const baseConfidence = Math.min(1, dataPoints / 30); // 数据点越多，基础置信度越高
    const decayFactor = Math.exp(-daysAhead / 7); // 预测时间越远，置信度越低
    return Math.round(baseConfidence * decayFactor * 100) / 100;
}

function assessBloodPressureRisk(prediction: any): string {
    const systolic = prediction.predicted_systolic;
    const diastolic = prediction.predicted_diastolic;
    
    if (systolic >= 180 || diastolic >= 120) return '高危：需要立即就医';
    if (systolic >= 160 || diastolic >= 100) return '2级高血压：建议尽快就诊';
    if (systolic >= 140 || diastolic >= 90) return '1级高血压：建议医学评估';
    if (systolic >= 130 || diastolic >= 85) return '正常高值：需要注意';
    return '正常范围：继续保持';
}

function interpretSleepScore(score: number): string {
    if (score >= 0.8) return '睡眠质量优秀';
    if (score >= 0.6) return '睡眠质量良好';
    if (score >= 0.4) return '睡眠质量一般';
    return '睡眠质量较差';
}

function generateSleepRecommendations(avgHours: number, consistency: number): string[] {
    const recommendations = [];
    
    if (avgHours < 7) {
        recommendations.push('建议增加睡眠时长至7-9小时');
    } else if (avgHours > 9) {
        recommendations.push('睡眠时长略长，建议调整作息');
    }
    
    if (consistency < 0.7) {
        recommendations.push('保持规律作息时间，提高睡眠一致性');
    }
    
    recommendations.push('睡前避免使用电子设备，营造良好睡眠环境');
    
    return recommendations;
}

function calculateRiskLevel(anomaly: any, hrv: any, bp: any): string {
    if (anomaly.count >= 2) return 'high';
    if (anomaly.count === 1 || (hrv.hrv_score && hrv.hrv_score < 40)) return 'medium';
    return 'low';
}

function calculateConfidenceScore(dataPoints: number): number {
    if (dataPoints >= 50) return 0.95;
    if (dataPoints >= 30) return 0.85;
    if (dataPoints >= 10) return 0.70;
    return 0.50;
}
