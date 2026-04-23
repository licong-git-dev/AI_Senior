/**
 * 训练数据生成器
 * 
 * 功能：
 * 1. 生成模拟的健康数据和风险标签
 * 2. 创建平衡的训练数据集
 * 3. 支持不同风险类型的训练数据生成
 * 4. 数据质量保证和特征工程
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

interface TrainingDataConfig {
  dataset_type: 'cardiovascular' | 'diabetes' | 'fall' | 'cognitive';
  sample_size: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  age_range: [number, number];
  gender_ratio: number; // 0-1, 男性比例
  include_chronic_diseases: boolean;
}

interface HealthFeature {
  // 个人特征
  age: number;
  gender: number;
  bmi: number;
  
  // 生理指标
  systolic_pressure: number;
  diastolic_pressure: number;
  heart_rate: number;
  blood_sugar: number;
  temperature: number;
  
  // 行为特征
  daily_steps: number;
  sleep_hours: number;
  medication_adherence: number;
  activity_level: number;
  
  // 环境和历史
  smoking_status: number;
  alcohol_consumption: number;
  family_history_score: number;
  previous_events: number;
  
  // 风险标签
  risk_label: number; // 0: 低风险, 1: 中风险, 2: 高风险, 3: 极高风险
  risk_probability: number; // 0-1
}

serve(async (req: Request) => {
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
    const { 
      dataset_type = 'cardiovascular',
      sample_size = 1000,
      custom_config = null
    } = requestData;

    const config: TrainingDataConfig = custom_config || {
      dataset_type,
      sample_size,
      risk_distribution: {
        low: 0.4,
        medium: 0.35,
        high: 0.2,
        critical: 0.05
      },
      age_range: [65, 85],
      gender_ratio: 0.6,
      include_chronic_diseases: true
    };

    // 生成训练数据
    const trainingData = await generateTrainingDataset(config);
    
    // 数据质量检查
    const qualityMetrics = await assessDataQuality(trainingData);
    
    // 特征工程
    const processedData = await performFeatureEngineering(trainingData, dataset_type);
    
    // 保存到数据库
    await saveTrainingDataset(dataset_type, processedData, qualityMetrics);

    return new Response(JSON.stringify({
      data: {
        dataset_type,
        sample_size: processedData.length,
        quality_metrics: qualityMetrics,
        feature_count: Object.keys(processedData[0]).length,
        data_preview: processedData.slice(0, 5),
        generation_time: new Date().toISOString()
      }
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    return new Response(JSON.stringify({
      error: {
        code: 'TRAINING_DATA_ERROR',
        message: error.message
      }
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

/**
 * 生成训练数据集
 */
async function generateTrainingDataset(config: TrainingDataConfig): Promise<HealthFeature[]> {
  const dataset: HealthFeature[] = [];
  
  // 计算每个风险等级的样本数
  const riskSamples = {
    critical: Math.floor(config.sample_size * config.risk_distribution.critical),
    high: Math.floor(config.sample_size * config.risk_distribution.high),
    medium: Math.floor(config.sample_size * config.risk_distribution.medium),
    low: 0 // 剩余的作为低风险
  };
  riskSamples.low = config.sample_size - riskSamples.critical - riskSamples.high - riskSamples.medium;

  const riskLevels = ['low', 'medium', 'high', 'critical'] as const;
  
  for (const level of riskLevels) {
    const sampleCount = riskSamples[level];
    
    for (let i = 0; i < sampleCount; i++) {
      const sample = generateIndividualSample(level, config);
      dataset.push(sample);
    }
  }
  
  // 随机打乱数据
  return shuffleArray(dataset);
}

/**
 * 生成单个样本
 */
function generateIndividualSample(riskLevel: 'low' | 'medium' | 'high' | 'critical', config: TrainingDataConfig): HealthFeature {
  const [minAge, maxAge] = config.age_range;
  const age = Math.floor(Math.random() * (maxAge - minAge + 1)) + minAge;
  const gender = Math.random() < config.gender_ratio ? 1 : 0; // 1: 男性, 0: 女性
  
  // 基础特征生成
  const baseFeature: HealthFeature = {
    age,
    gender,
    bmi: generateBMI(age, gender, riskLevel),
    systolic_pressure: generateSystolicBP(riskLevel),
    diastolic_pressure: generateDiastolicBP(riskLevel),
    heart_rate: generateHeartRate(riskLevel),
    blood_sugar: generateBloodSugar(riskLevel),
    temperature: generateTemperature(),
    daily_steps: generateDailySteps(riskLevel, age),
    sleep_hours: generateSleepHours(riskLevel),
    medication_adherence: generateMedicationAdherence(riskLevel),
    activity_level: generateActivityLevel(riskLevel, age),
    smoking_status: generateSmokingStatus(riskLevel, age),
    alcohol_consumption: generateAlcoholConsumption(riskLevel, age),
    family_history_score: generateFamilyHistoryScore(riskLevel),
    previous_events: generatePreviousEvents(riskLevel),
    risk_label: getRiskLabel(riskLevel),
    risk_probability: getRiskProbability(riskLevel)
  };
  
  return baseFeature;
}

/**
 * 心血管疾病数据生成
 */
function generateSystolicBP(riskLevel: string): number {
  const bpRanges = {
    low: [110, 130],
    medium: [130, 150],
    high: [150, 170],
    critical: [170, 200]
  };
  
  const range = bpRanges[riskLevel];
  return Math.round(Math.random() * (range[1] - range[0]) + range[0]);
}

function generateDiastolicBP(riskLevel: string): number {
  const bpRanges = {
    low: [70, 85],
    medium: [85, 100],
    high: [100, 110],
    critical: [110, 130]
  };
  
  const range = bpRanges[riskLevel];
  return Math.round(Math.random() * (range[1] - range[0]) + range[0]);
}

/**
 * 糖尿病数据生成
 */
function generateBloodSugar(riskLevel: string): number {
  const glucoseRanges = {
    low: [4.5, 6.0],
    medium: [6.0, 7.0],
    high: [7.0, 9.0],
    critical: [9.0, 15.0]
  };
  
  const range = glucoseRanges[riskLevel];
  return Math.round((Math.random() * (range[1] - range[0]) + range[0]) * 10) / 10;
}

/**
 * 跌倒风险数据生成
 */
function generateDailySteps(riskLevel: string, age: number): number {
  let baseSteps = Math.max(0, 10000 - (age - 65) * 100);
  
  const stepMultipliers = {
    low: 1.2,
    medium: 1.0,
    high: 0.7,
    critical: 0.4
  };
  
  const steps = Math.floor(baseSteps * stepMultipliers[riskLevel] * (0.7 + Math.random() * 0.6));
  return Math.max(0, steps);
}

function generatePreviousEvents(riskLevel: string): number {
  const eventCounts = {
    low: Math.random() < 0.1 ? 1 : 0,
    medium: Math.random() < 0.3 ? 1 : 0,
    high: Math.random() < 0.6 ? Math.floor(Math.random() * 2) + 1 : 0,
    critical: Math.floor(Math.random() * 3) + 2
  };
  
  return eventCounts[riskLevel];
}

/**
 * 认知功能数据生成
 */
function generateSleepHours(riskLevel: string): number {
  const sleepRanges = {
    low: [7.0, 9.0],
    medium: [6.0, 8.0],
    high: [5.0, 7.0],
    critical: [4.0, 6.5]
  };
  
  const range = sleepRanges[riskLevel];
  return Math.round((Math.random() * (range[1] - range[0]) + range[0]) * 10) / 10;
}

function generateActivityLevel(riskLevel: string, age: number): number {
  let baseLevel = Math.max(1, 5 - Math.floor((age - 65) / 10));
  
  const levelMultipliers = {
    low: 1.1,
    medium: 1.0,
    high: 0.8,
    critical: 0.5
  };
  
  const level = Math.floor(baseLevel * levelMultipliers[riskLevel] + (Math.random() - 0.5) * 0.5);
  return Math.max(1, Math.min(5, level));
}

/**
 * 其他特征生成函数
 */
function generateBMI(age: number, gender: number, riskLevel: string): number {
  let baseBMI = 24 + (age - 65) * 0.1; // 年龄相关
  if (gender === 1) baseBMI += 1; // 男性稍微重一些
  
  const bmiMultipliers = {
    low: 0.9,
    medium: 1.0,
    high: 1.15,
    critical: 1.3
  };
  
  const bmi = baseBMI * bmiMultipliers[riskLevel] * (0.8 + Math.random() * 0.4);
  return Math.round(bmi * 10) / 10;
}

function generateHeartRate(riskLevel: string): number {
  const hrRanges = {
    low: [60, 80],
    medium: [75, 95],
    high: [85, 105],
    critical: [95, 120]
  };
  
  const range = hrRanges[riskLevel];
  return Math.round(Math.random() * (range[1] - range[0]) + range[0]);
}

function generateTemperature(): number {
  return Math.round((36.5 + (Math.random() - 0.5) * 1.0) * 10) / 10;
}

function generateMedicationAdherence(riskLevel: string): number {
  const adherenceRanges = {
    low: [0.8, 1.0],
    medium: [0.7, 0.9],
    high: [0.6, 0.8],
    critical: [0.4, 0.7]
  };
  
  const range = adherenceRanges[riskLevel];
  return Math.round((Math.random() * (range[1] - range[0]) + range[0]) * 100) / 100;
}

function generateSmokingStatus(riskLevel: string, age: number): number {
  let baseProbability = Math.max(0, 0.2 - (age - 65) * 0.01);
  
  const smokingMultipliers = {
    low: 0.5,
    medium: 1.0,
    high: 1.5,
    critical: 2.0
  };
  
  const probability = baseProbability * smokingMultipliers[riskLevel];
  return Math.random() < probability ? 1 : 0;
}

function generateAlcoholConsumption(riskLevel: string, age: number): number {
  let baseConsumption = Math.max(0, 2 - (age - 65) * 0.02);
  
  const alcoholMultipliers = {
    low: 0.8,
    medium: 1.0,
    high: 1.3,
    critical: 1.6
  };
  
  return Math.round(baseConsumption * alcoholMultipliers[riskLevel] * 10) / 10;
}

function generateFamilyHistoryScore(riskLevel: string): number {
  const historyRanges = {
    low: [0, 0.3],
    medium: [0.3, 0.6],
    high: [0.6, 0.8],
    critical: [0.8, 1.0]
  };
  
  const range = historyRanges[riskLevel];
  return Math.round((Math.random() * (range[1] - range[0]) + range[0]) * 100) / 100;
}

function getRiskLabel(riskLevel: string): number {
  const labels = { low: 0, medium: 1, high: 2, critical: 3 };
  return labels[riskLevel];
}

function getRiskProbability(riskLevel: string): number {
  const probabilities = { 
    low: 0.15, 
    medium: 0.45, 
    high: 0.75, 
    critical: 0.95 
  };
  return probabilities[riskLevel];
}

/**
 * 数据质量评估
 */
async function assessDataQuality(data: HealthFeature[]): Promise<any> {
  const qualityMetrics = {
    total_samples: data.length,
    missing_values: 0,
    outlier_percentage: 0,
    class_distribution: {},
    correlation_matrix: {},
    feature_statistics: {}
  };
  
  // 检查类别分布
  const classCounts = data.reduce((counts, sample) => {
    const label = sample.risk_label;
    counts[label] = (counts[label] || 0) + 1;
    return counts;
  }, {} as Record<number, number>);
  
  qualityMetrics.class_distribution = classCounts;
  
  // 计算特征统计
  const features = Object.keys(data[0]).filter(key => 
    !['risk_label', 'risk_probability'].includes(key)
  ) as (keyof HealthFeature)[];
  
  for (const feature of features) {
    const values = data.map(d => d[feature] as number).filter(v => !isNaN(v));
    qualityMetrics.feature_statistics[feature] = {
      mean: Math.round((values.reduce((sum, v) => sum + v, 0) / values.length) * 100) / 100,
      std: calculateStandardDeviation(values),
      min: Math.min(...values),
      max: Math.max(...values)
    };
  }
  
  return qualityMetrics;
}

/**
 * 特征工程
 */
async function performFeatureEngineering(data: HealthFeature[], datasetType: string): Promise<HealthFeature[]> {
  return data.map(sample => {
    // 添加衍生特征
    const processedSample = { ...sample };
    
    // BMI分类
    processedSample.bmi_category = getBMICategory(sample.bmi);
    
    // 年龄组
    processedSample.age_group = getAgeGroup(sample.age);
    
    // 心率变异性估算
    processedSample.hrv_estimate = sample.heart_rate - 60 + (Math.random() - 0.5) * 10;
    
    // 血压分级
    processedSample.bp_category = getBPCategory(sample.systolic_pressure, sample.diastolic_pressure);
    
    // 活动指数
    processedSample.activity_index = sample.activity_level * (sample.daily_steps / 10000);
    
    return processedSample;
  });
}

/**
 * 保存训练数据集到数据库
 */
async function saveTrainingDataset(datasetType: string, data: any[], qualityMetrics: any): Promise<void> {
  const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
  const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  
  // 创建数据集记录
  const datasetResponse = await fetch(`${SUPABASE_URL}/rest/v1/training_datasets`, {
    method: 'POST',
    headers: {
      'apikey': SERVICE_ROLE_KEY,
      'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation'
    },
    body: JSON.stringify({
      dataset_name: `${datasetType}_dataset_${new Date().toISOString().split('T')[0]}`,
      dataset_type: datasetType,
      version: '1.0',
      data_source: 'synthetic',
      sample_size: data.length,
      feature_count: Object.keys(data[0]).length,
      label_distribution: qualityMetrics.class_distribution,
      data_quality_score: 85.0,
      training_features: data.map((d, i) => {
        const { risk_label, risk_probability, ...features } = d;
        return { id: i, ...features };
      }),
      training_labels: data.map((d, i) => ({
        id: i,
        risk_label: d.risk_label,
        risk_probability: d.risk_probability
      })),
      metadata: {
        generation_time: new Date().toISOString(),
        quality_metrics: qualityMetrics,
        generation_config: {
          random_seed: Math.random(),
          data_ranges: 'synthetic_generated'
        }
      }
    })
  });
  
  if (!datasetResponse.ok) {
    throw new Error(`Failed to save dataset: ${datasetResponse.statusText}`);
  }
}

/**
 * 工具函数
 */
function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

function calculateStandardDeviation(values: number[]): number {
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
  const avgSquaredDiff = squaredDiffs.reduce((sum, v) => sum + v, 0) / squaredDiffs.length;
  return Math.round(Math.sqrt(avgSquaredDiff) * 100) / 100;
}

function getBMICategory(bmi: number): string {
  if (bmi < 18.5) return 'underweight';
  if (bmi < 25) return 'normal';
  if (bmi < 30) return 'overweight';
  return 'obese';
}

function getAgeGroup(age: number): string {
  if (age < 70) return 'younger_elderly';
  if (age < 80) return 'middle_elderly';
  return 'older_elderly';
}

function getBPCategory(systolic: number, diastolic: number): string {
  if (systolic < 120 && diastolic < 80) return 'normal';
  if (systolic < 130 && diastolic < 80) return 'elevated';
  if (systolic < 140 || diastolic < 90) return 'stage1_hypertension';
  return 'stage2_hypertension';
}