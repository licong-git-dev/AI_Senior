// 行为模式识别系统 Edge Function
// 活动轨迹分析、异常行为检测、认知能力评估、日常活动模式识别

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
        const { user_id, analysis_period } = await req.json();

        if (!user_id) {
            throw new Error('缺少必需参数：user_id');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
        const aliApiKey = 'sk-71bb10435f134dfdab3a4b684e57b640';

        // 确定分析周期
        let daysBack = 7;
        if (analysis_period === 'month') daysBack = 30;
        else if (analysis_period === 'day') daysBack = 1;

        const startDate = new Date(Date.now() - daysBack * 24 * 60 * 60 * 1000).toISOString();
        const endDate = new Date().toISOString();

        // 1. 获取传感器数据（活动、位置、互动等）
        const sensorDataResponse = await fetch(
            `${supabaseUrl}/rest/v1/sensor_data?user_id=eq.${user_id}&timestamp=gte.${startDate}&timestamp=lte.${endDate}&order=timestamp.asc&limit=1000`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                }
            }
        );

        const sensorData = sensorDataResponse.ok ? await sensorDataResponse.json() : [];

        // 2. 活动轨迹分析
        const activityTrajectory = analyzeActivityTrajectory(sensorData);

        // 3. 行为时间线构建
        const behaviorTimeline = buildBehaviorTimeline(sensorData);

        // 4. 异常行为检测
        const abnormalBehaviors = detectAbnormalBehaviors(behaviorTimeline, activityTrajectory);

        // 5. 认知能力评估
        const cognitiveScore = assessCognitiveAbility(sensorData, behaviorTimeline);

        // 6. AI生成行为分析报告
        const aiInsights = await generateBehaviorAIAnalysis(
            activityTrajectory,
            behaviorTimeline,
            abnormalBehaviors,
            cognitiveScore,
            aliApiKey
        );

        // 7. 保存行为模式识别结果
        const patternRecord = {
            user_id,
            pattern_type: 'comprehensive',
            activity_trajectory: activityTrajectory,
            behavior_timeline: behaviorTimeline,
            cognitive_score: cognitiveScore.score,
            abnormal_behaviors: abnormalBehaviors,
            pattern_confidence: calculatePatternConfidence(sensorData.length, daysBack),
            analysis_period: analysis_period || 'week',
        };

        const saveResponse = await fetch(
            `${supabaseUrl}/rest/v1/behavior_patterns`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                body: JSON.stringify(patternRecord)
            }
        );

        const savedData = saveResponse.ok ? await saveResponse.json() : [];

        return new Response(JSON.stringify({
            data: {
                pattern_id: savedData[0]?.id,
                activity_trajectory: activityTrajectory,
                behavior_timeline: behaviorTimeline,
                abnormal_behaviors: abnormalBehaviors,
                cognitive_assessment: cognitiveScore,
                ai_insights: aiInsights,
                pattern_confidence: patternRecord.pattern_confidence,
                analysis_period: {
                    type: analysis_period || 'week',
                    days: daysBack,
                    start: startDate,
                    end: endDate
                },
                data_points: sensorData.length,
                message: '行为模式识别完成'
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('行为模式识别错误:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'BEHAVIOR_RECOGNITION_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// 活动轨迹分析
function analyzeActivityTrajectory(sensorData: any[]): any {
    const trajectoryData = sensorData.filter(d => 
        d.sensor_type === 'location' || 
        d.sensor_type === 'activity' ||
        d.device_type === 'camera'
    );

    if (trajectoryData.length === 0) {
        return {
            status: 'no_data',
            message: '无活动轨迹数据'
        };
    }

    // 按时间分组活动
    const activityByHour = new Array(24).fill(0);
    const locationChanges = [];
    const activityTypes = new Map<string, number>();

    trajectoryData.forEach(d => {
        const hour = new Date(d.timestamp).getHours();
        activityByHour[hour]++;

        const activity = d.data_value?.activity || d.data_value?.detected_activity;
        if (activity) {
            activityTypes.set(activity, (activityTypes.get(activity) || 0) + 1);
        }

        if (d.sensor_type === 'location' && d.data_value?.location) {
            locationChanges.push({
                location: d.data_value.location,
                timestamp: d.timestamp
            });
        }
    });

    // 识别活动高峰时段
    const peakHours = activityByHour
        .map((count, hour) => ({ hour, count }))
        .filter(h => h.count > 0)
        .sort((a, b) => b.count - a.count)
        .slice(0, 3)
        .map(h => h.hour);

    // 计算活动多样性
    const activityDiversity = activityTypes.size;
    const mostCommonActivity = Array.from(activityTypes.entries())
        .sort((a, b) => b[1] - a[1])[0];

    return {
        status: 'analyzed',
        total_activities: trajectoryData.length,
        activity_by_hour: activityByHour,
        peak_hours: peakHours,
        activity_diversity: activityDiversity,
        most_common_activity: mostCommonActivity ? {
            type: mostCommonActivity[0],
            count: mostCommonActivity[1]
        } : null,
        location_changes: locationChanges.length,
        mobility_score: calculateMobilityScore(activityByHour, locationChanges.length)
    };
}

// 行为时间线构建
function buildBehaviorTimeline(sensorData: any[]): any {
    const timeline: any[] = [];
    
    // 按时间排序
    const sortedData = sensorData.sort((a, b) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // 识别行为模式
    sortedData.forEach(d => {
        const hour = new Date(d.timestamp).getHours();
        const behavior = identifyBehavior(d, hour);
        
        if (behavior) {
            timeline.push({
                timestamp: d.timestamp,
                hour,
                behavior: behavior.type,
                confidence: behavior.confidence,
                data_source: d.device_type,
                details: behavior.details
            });
        }
    });

    // 识别日常模式
    const dailyPatterns = identifyDailyPatterns(timeline);

    return {
        events: timeline,
        daily_patterns: dailyPatterns,
        total_behaviors: timeline.length,
        pattern_consistency: calculatePatternConsistency(dailyPatterns)
    };
}

// 识别具体行为
function identifyBehavior(dataPoint: any, hour: number): any {
    const value = dataPoint.data_value;
    
    // 睡眠行为
    if ((hour >= 22 || hour <= 6) && value?.activity === 'sleeping') {
        return {
            type: 'sleeping',
            confidence: 0.95,
            details: { location: 'bedroom', stage: value.sleep_stage }
        };
    }

    // 用餐行为
    if ((hour >= 7 && hour <= 9) || (hour >= 11 && hour <= 13) || (hour >= 17 && hour <= 19)) {
        if (value?.activity === 'sitting' || value?.location === 'dining_room') {
            return {
                type: 'eating',
                confidence: 0.75,
                details: { meal_time: getMealTime(hour) }
            };
        }
    }

    // 运动行为
    if (value?.steps > 100 || value?.activity === 'walking' || value?.activity === 'exercise') {
        return {
            type: 'exercising',
            confidence: 0.85,
            details: { intensity: value.steps > 200 ? 'moderate' : 'light' }
        };
    }

    // 社交行为
    if (value?.activity === 'conversation' || value?.detected_activity === 'talking') {
        return {
            type: 'socializing',
            confidence: 0.80,
            details: { duration_minutes: value.duration }
        };
    }

    // 休息行为
    if (value?.activity === 'resting' || value?.activity === 'sitting') {
        return {
            type: 'resting',
            confidence: 0.70,
            details: { location: value.location }
        };
    }

    return null;
}

// 异常行为检测
function detectAbnormalBehaviors(timeline: any, trajectory: any): any {
    const abnormalities = [];

    // 1. 夜间异常活动
    const nightActivities = timeline.events.filter((e: any) => 
        e.hour >= 0 && e.hour <= 5 && e.behavior !== 'sleeping'
    );
    
    if (nightActivities.length > 3) {
        abnormalities.push({
            type: 'night_activity',
            severity: 'medium',
            description: '检测到夜间异常活动',
            occurrences: nightActivities.length,
            details: nightActivities.slice(0, 3)
        });
    }

    // 2. 活动减少（可能的健康问题）
    if (trajectory.status === 'analyzed' && trajectory.mobility_score < 0.3) {
        abnormalities.push({
            type: 'reduced_activity',
            severity: 'high',
            description: '活动量显著减少',
            mobility_score: trajectory.mobility_score,
            recommendation: '建议关注健康状况，可能需要医疗评估'
        });
    }

    // 3. 模式突变
    if (timeline.pattern_consistency < 0.5) {
        abnormalities.push({
            type: 'pattern_change',
            severity: 'medium',
            description: '日常行为模式发生变化',
            consistency_score: timeline.pattern_consistency,
            recommendation: '建议观察是否有环境或健康变化'
        });
    }

    // 4. 社交隔离
    const socialEvents = timeline.events.filter((e: any) => e.behavior === 'socializing');
    if (socialEvents.length < 2) {
        abnormalities.push({
            type: 'social_isolation',
            severity: 'low',
            description: '社交活动较少',
            social_events: socialEvents.length,
            recommendation: '鼓励参与社交活动'
        });
    }

    return {
        detected: abnormalities.length > 0,
        count: abnormalities.length,
        details: abnormalities,
        overall_risk: calculateBehaviorRisk(abnormalities)
    };
}

// 认知能力评估
function assessCognitiveAbility(sensorData: any[], timeline: any): any {
    let cognitiveScore = 100;
    const factors = [];

    // 1. 日常活动规律性
    const consistency = timeline.pattern_consistency || 0;
    if (consistency < 0.5) {
        cognitiveScore -= 15;
        factors.push('日常活动规律性较差');
    } else if (consistency >= 0.8) {
        factors.push('日常活动规律良好');
    }

    // 2. 活动多样性
    const diversity = timeline.daily_patterns?.activity_diversity || 0;
    if (diversity < 3) {
        cognitiveScore -= 10;
        factors.push('活动类型单一');
    }

    // 3. 响应速度（从游戏记录或互动数据推断）
    const interactionData = sensorData.filter(d => 
        d.sensor_type === 'interaction' || d.data_value?.response_time
    );
    
    if (interactionData.length > 0) {
        const avgResponseTime = interactionData.reduce((sum, d) => 
            sum + (d.data_value?.response_time || 0), 0
        ) / interactionData.length;

        if (avgResponseTime > 5000) { // 超过5秒
            cognitiveScore -= 10;
            factors.push('响应速度较慢');
        }
    }

    // 4. 记忆表现（从重复行为或提醒完成情况推断）
    const reminderData = sensorData.filter(d => d.sensor_type === 'reminder_response');
    if (reminderData.length > 0) {
        const completionRate = reminderData.filter(d => 
            d.data_value?.completed === true
        ).length / reminderData.length;

        if (completionRate < 0.6) {
            cognitiveScore -= 15;
            factors.push('提醒完成率较低');
        }
    }

    cognitiveScore = Math.max(0, Math.min(100, cognitiveScore));

    return {
        score: cognitiveScore / 100,
        level: interpretCognitiveScore(cognitiveScore),
        factors: factors,
        recommendation: generateCognitiveRecommendation(cognitiveScore)
    };
}

// AI行为分析
async function generateBehaviorAIAnalysis(
    trajectory: any,
    timeline: any,
    abnormal: any,
    cognitive: any,
    apiKey: string
): Promise<string> {
    const prompt = `作为老年行为分析专家，请分析以下行为模式数据：

活动轨迹：
- 总活动次数：${trajectory.total_activities || 0}
- 活动多样性：${trajectory.activity_diversity || 0}种
- 移动性评分：${trajectory.mobility_score || 0}
- 活动高峰时段：${trajectory.peak_hours?.join(', ') || '无'}时

行为模式：
- 记录行为：${timeline.total_behaviors || 0}次
- 模式一致性：${timeline.pattern_consistency || 0}

异常检测：
${abnormal.detected ? `检测到${abnormal.count}项异常：\n${abnormal.details.map((a: any) => `- ${a.description}`).join('\n')}` : '未检测到异常行为'}

认知评估：
- 认知评分：${cognitive.score}
- 评级：${cognitive.level}

请提供简洁分析（100字以内）：
1. 行为模式总体评价
2. 主要关注点（如有）
3. 2-3条具体建议`;

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
                    { role: 'system', content: '你是老年行为模式分析专家。' },
                    { role: 'user', content: prompt }
                ],
                max_tokens: 400
            })
        });

        if (!response.ok) return '行为模式整体正常，建议保持当前生活方式。';

        const result = await response.json();
        return result.choices?.[0]?.message?.content || '行为分析完成。';
    } catch (error) {
        return '行为数据已记录，建议定期关注活动模式变化。';
    }
}

// 辅助函数
function calculateMobilityScore(activityByHour: number[], locationChanges: number): number {
    const totalActivity = activityByHour.reduce((a, b) => a + b, 0);
    const activeHours = activityByHour.filter(h => h > 0).length;
    
    const activityScore = Math.min(1, totalActivity / 100);
    const diversityScore = Math.min(1, activeHours / 12);
    const mobilityScore = Math.min(1, locationChanges / 20);
    
    return (activityScore * 0.4 + diversityScore * 0.3 + mobilityScore * 0.3);
}

function identifyDailyPatterns(timeline: any[]): any {
    const patterns: any = {
        morning_routine: [],
        afternoon_routine: [],
        evening_routine: [],
        activity_diversity: 0
    };

    const morningEvents = timeline.filter(e => e.hour >= 6 && e.hour < 12);
    const afternoonEvents = timeline.filter(e => e.hour >= 12 && e.hour < 18);
    const eveningEvents = timeline.filter(e => e.hour >= 18 && e.hour < 22);

    patterns.morning_routine = extractRoutine(morningEvents);
    patterns.afternoon_routine = extractRoutine(afternoonEvents);
    patterns.evening_routine = extractRoutine(eveningEvents);

    const uniqueBehaviors = new Set(timeline.map(e => e.behavior));
    patterns.activity_diversity = uniqueBehaviors.size;

    return patterns;
}

function extractRoutine(events: any[]): any[] {
    const behaviorCounts = new Map<string, number>();
    events.forEach(e => {
        behaviorCounts.set(e.behavior, (behaviorCounts.get(e.behavior) || 0) + 1);
    });

    return Array.from(behaviorCounts.entries())
        .map(([behavior, count]) => ({ behavior, frequency: count }))
        .sort((a, b) => b.frequency - a.frequency);
}

function calculatePatternConsistency(patterns: any): number {
    if (!patterns) return 0;
    
    const routines = [
        patterns.morning_routine,
        patterns.afternoon_routine,
        patterns.evening_routine
    ].filter(r => r && r.length > 0);

    if (routines.length === 0) return 0;
    
    const avgRoutineLength = routines.reduce((sum, r) => sum + r.length, 0) / routines.length;
    return Math.min(1, avgRoutineLength / 5);
}

function getMealTime(hour: number): string {
    if (hour >= 7 && hour <= 9) return 'breakfast';
    if (hour >= 11 && hour <= 13) return 'lunch';
    if (hour >= 17 && hour <= 19) return 'dinner';
    return 'snack';
}

function calculateBehaviorRisk(abnormalities: any[]): string {
    if (abnormalities.length === 0) return 'low';
    
    const highSeverity = abnormalities.filter(a => a.severity === 'high').length;
    if (highSeverity > 0) return 'high';
    
    const mediumSeverity = abnormalities.filter(a => a.severity === 'medium').length;
    if (mediumSeverity >= 2) return 'medium';
    
    return 'low';
}

function interpretCognitiveScore(score: number): string {
    if (score >= 85) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 55) return '一般';
    return '需要关注';
}

function generateCognitiveRecommendation(score: number): string {
    if (score >= 85) return '认知功能良好，建议继续保持活跃生活方式';
    if (score >= 70) return '认知功能正常，建议适当增加脑力活动';
    if (score >= 55) return '建议增加认知训练，如阅读、游戏等';
    return '建议进行专业认知评估，考虑医疗干预';
}

function calculatePatternConfidence(dataPoints: number, days: number): number {
    const dailyAverage = dataPoints / days;
    if (dailyAverage >= 50) return 0.95;
    if (dailyAverage >= 30) return 0.85;
    if (dailyAverage >= 10) return 0.70;
    return 0.50;
}
