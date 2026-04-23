# 智能异常行为检测系统技术方案

## 1. 系统概述

智能异常行为检测系统基于多设备数据融合，实现实时行为模式分析和异常检测。系统采用自适应基线模型，能够动态调整正常行为范围，识别活动量异常、作息时间异常和认知能力下降信号。

### 1.1 核心特性
- **实时检测**：响应时间≤2分钟
- **多设备融合**：手环活动数据、床垫睡眠数据、环境传感器数据
- **自适应基线**：基于个人历史数据动态调整
- **智能分析**：时间序列分析和模式识别
- **低延迟处理**：边缘计算优化

### 1.2 技术架构
```
数据采集层 → 预处理层 → 特征提取层 → 异常检测层 → 告警层 → API接口层
     ↓           ↓           ↓           ↓           ↓         ↓
   多设备     数据清洗     时序特征     多算法      告警策略   RESTful
   传感器     标准化       模式识别     融合        分级通知   接口
```

## 2. 异常行为检测算法设计

### 2.1 活动量异常检测算法

#### 2.1.1 统计基线算法
```python
class ActivityAnomalyDetector:
    def __init__(self, window_size=7, threshold_sigma=2.5):
        self.window_size = window_size  # 基线数据窗口（天）
        self.threshold_sigma = threshold_sigma  # 异常阈值（标准差倍数）
        self.baseline_stats = {}
        
    def update_baseline(self, user_id, daily_activity_data):
        """更新用户活动基线"""
        if user_id not in self.baseline_stats:
            self.baseline_stats[user_id] = self._initialize_baseline()
            
        # 计算移动平均和标准差
        mean = np.mean(daily_activity_data)
        std = np.std(daily_activity_data)
        
        self.baseline_stats[user_id].update({
            'mean': mean,
            'std': std,
            'percentile_95': np.percentile(daily_activity_data, 95),
            'percentile_5': np.percentile(daily_activity_data, 5)
        })
        
    def detect_anomaly(self, user_id, current_activity):
        """检测活动量异常"""
        if user_id not in self.baseline_stats:
            return {'status': 'insufficient_data', 'anomaly_score': 0}
            
        baseline = self.baseline_stats[user_id]
        
        # 计算异常得分
        z_score = abs(current_activity - baseline['mean']) / baseline['std']
        
        # 异常类型判断
        anomaly_type = None
        if current_activity < baseline['percentile_5']:
            anomaly_type = 'activity_decrease'
        elif current_activity > baseline['percentile_95']:
            anomaly_type = 'activity_increase'
            
        confidence = min(z_score / self.threshold_sigma, 1.0)
        
        return {
            'anomaly_detected': z_score > self.threshold_sigma,
            'anomaly_type': anomaly_type,
            'anomaly_score': confidence,
            'z_score': z_score,
            'current_value': current_activity,
            'baseline_mean': baseline['mean']
        }
```

#### 2.1.2 趋势变化检测
```python
class TrendAnalyzer:
    def __init__(self, min_trend_days=3):
        self.min_trend_days = min_trend_days
        
    def detect_trend_anomaly(self, activity_series):
        """检测活动量趋势异常"""
        if len(activity_series) < self.min_trend_days:
            return {'trend_anomaly': False}
            
        # 计算移动趋势
        recent_trend = np.polyfit(range(len(activity_series[-7:])), 
                                 activity_series[-7:], 1)[0]
        historical_trend = np.polyfit(range(len(activity_series[-30:-7])), 
                                     activity_series[-30:-7], 1)[0]
        
        # 趋势差异分析
        trend_difference = abs(recent_trend - historical_trend)
        trend_ratio = recent_trend / (historical_trend + 1e-8)
        
        # 异常判断
        significant_drop = (recent_trend < -0.1 and 
                          trend_ratio < 0.5 and 
                          recent_trend - historical_trend < -0.05)
        
        return {
            'trend_anomaly': significant_drop,
            'recent_trend': recent_trend,
            'historical_trend': historical_trend,
            'trend_ratio': trend_ratio,
            'trend_difference': trend_difference
        }
```

### 2.2 作息时间异常检测算法

#### 2.2.1 睡眠模式分析
```python
class SleepPatternDetector:
    def __init__(self, time_tolerance=60):  # 容忍度：60分钟
        self.time_tolerance = time_tolerance
        
    def extract_sleep_features(self, sleep_data):
        """提取睡眠特征"""
        features = {}
        
        # 睡眠时长
        features['sleep_duration'] = sleep_data.get('total_sleep_time', 0)
        
        # 入睡时间
        sleep_start = sleep_data.get('sleep_start_time')
        if sleep_start:
            features['sleep_start_hour'] = self._extract_hour(sleep_start)
            
        # 起床时间
        sleep_end = sleep_data.get('wake_up_time')
        if sleep_end:
            features['wake_up_hour'] = self._extract_hour(sleep_end)
            
        # 睡眠质量分数
        features['sleep_quality'] = sleep_data.get('sleep_score', 0)
        
        # 夜间觉醒次数
        features['awakening_count'] = sleep_data.get('awakening_count', 0)
        
        return features
        
    def detect_sleep_anomaly(self, user_id, current_sleep_features, historical_sleep):
        """检测睡眠异常"""
        anomalies = []
        anomaly_score = 0
        
        # 睡眠时长异常
        avg_duration = np.mean([s.get('sleep_duration', 0) for s in historical_sleep])
        current_duration = current_sleep_features.get('sleep_duration', 0)
        
        if abs(current_duration - avg_duration) > 120:  # 超过2小时
            anomalies.append('sleep_duration_anomaly')
            anomaly_score += 0.3
            
        # 入睡时间异常
        current_start_hour = current_sleep_features.get('sleep_start_hour')
        if current_start_hour is not None:
            historical_start_hours = [s.get('sleep_start_hour') for s in historical_sleep 
                                    if s.get('sleep_start_hour') is not None]
            if historical_start_hours:
                avg_start_hour = np.mean(historical_start_hours)
                start_diff = abs(self._time_difference(current_start_hour, avg_start_hour))
                
                if start_diff > self.time_tolerance:
                    anomalies.append('sleep_time_anomaly')
                    anomaly_score += 0.4
                    
        # 睡眠质量异常
        current_quality = current_sleep_features.get('sleep_quality', 0)
        if current_quality < 60:  # 睡眠质量低于60分
            anomalies.append('sleep_quality_anomaly')
            anomaly_score += 0.3
            
        return {
            'anomaly_detected': len(anomalies) > 0,
            'anomaly_types': anomalies,
            'anomaly_score': min(anomaly_score, 1.0),
            'sleep_duration_deviation': abs(current_duration - avg_duration) if avg_duration > 0 else 0
        }
```

#### 2.2.2 日常活动节奏分析
```python
class DailyRhythmDetector:
    def __init__(self, activity_bins=24):
        self.activity_bins = activity_bins  # 24小时活动分布
        
    def build_activity_profile(self, activity_data):
        """构建活动分布图"""
        activity_profile = np.zeros(self.activity_bins)
        
        for timestamp, activity_level in activity_data:
            hour = datetime.fromtimestamp(timestamp).hour
            activity_profile[hour] += activity_level
            
        # 标准化
        total_activity = np.sum(activity_profile)
        if total_activity > 0:
            activity_profile = activity_profile / total_activity
            
        return activity_profile
        
    def detect_rhythm_anomaly(self, current_profile, baseline_profile):
        """检测日常节律异常"""
        # 计算相似度（余弦相似度）
        similarity = np.dot(current_profile, baseline_profile) / (
            np.linalg.norm(current_profile) * np.linalg.norm(baseline_profile) + 1e-8
        )
        
        # 计算活动峰值时间差异
        current_peak = np.argmax(current_profile)
        baseline_peak = np.argmax(baseline_profile)
        peak_time_diff = abs(current_peak - baseline_peak)
        
        # 计算活动分布熵
        current_entropy = -np.sum(current_profile * np.log(current_profile + 1e-8))
        baseline_entropy = -np.sum(baseline_profile * np.log(baseline_profile + 1e-8))
        entropy_diff = abs(current_entropy - baseline_entropy)
        
        # 异常评分
        rhythm_score = 1 - similarity
        irregularity_score = min(peak_time_diff / 12, 1) + min(entropy_diff / 2, 1)
        anomaly_score = (rhythm_score + irregularity_score) / 2
        
        return {
            'rhythm_anomaly': anomaly_score > 0.3,
            'anomaly_score': anomaly_score,
            'similarity_score': similarity,
            'peak_time_shift': peak_time_diff,
            'irregularity_score': irregularity_score
        }
```

### 2.3 认知能力下降信号检测

#### 2.3.1 反应时间分析
```python
class CognitiveDeclineDetector:
    def __init__(self, reaction_time_threshold=2000):  # 2秒阈值
        self.reaction_time_threshold = reaction_time_threshold
        
    def analyze_reaction_patterns(self, reaction_time_data):
        """分析反应时间模式"""
        if len(reaction_time_data) < 10:
            return {'sufficient_data': False}
            
        # 基础统计
        mean_reaction = np.mean(reaction_time_data)
        median_reaction = np.median(reaction_time_data)
        std_reaction = np.std(reaction_time_data)
        
        # 趋势分析
        recent_times = reaction_time_data[-20:]  # 最近20次
        early_times = reaction_time_data[:20]    # 早期20次
        recent_mean = np.mean(recent_times)
        early_mean = np.mean(early_times)
        
        # 反应时间增长
        reaction_increase = (recent_mean - early_mean) / early_mean
        
        # 变异性增加
        recent_std = np.std(recent_times)
        early_std = np.std(early_times)
        variability_increase = recent_std / (early_std + 1e-8)
        
        # 异常长反应时间比例
        slow_reactions = sum(1 for rt in recent_times if rt > self.reaction_time_threshold)
        slow_reaction_ratio = slow_reactions / len(recent_times)
        
        return {
            'sufficient_data': True,
            'mean_reaction_time': mean_reaction,
            'reaction_trend_increase': reaction_increase,
            'variability_increase': variability_increase,
            'slow_reaction_ratio': slow_reaction_ratio,
            'cognitive_concern_score': self._calculate_concern_score(
                reaction_increase, variability_increase, slow_reaction_ratio
            )
        }
        
    def _calculate_concern_score(self, trend_increase, variability_increase, slow_ratio):
        """计算认知能力下降担忧分数"""
        # 趋势权重：40%
        trend_score = min(max(trend_increase * 2, 0), 1)
        
        # 变异性权重：35%
        variability_score = min(max(variability_increase - 1, 0), 1)
        
        # 慢反应比例权重：25%
        slow_score = min(slow_ratio * 5, 1)
        
        return trend_score * 0.4 + variability_score * 0.35 + slow_score * 0.25
```

#### 2.3.2 行为模式复杂度分析
```python
class BehaviorComplexityAnalyzer:
    def __init__(self, min_activities=50):
        self.min_activities = min_activities
        
    def calculate_behavioral_diversity(self, activity_sequence):
        """计算行为多样性"""
        if len(activity_sequence) < self.min_activities:
            return {'diversity_score': 0, 'sufficient_data': False}
            
        # 活动类型熵
        activity_types = [activity['type'] for activity in activity_sequence]
        type_counts = Counter(activity_types)
        type_entropy = -sum((count/len(activity_types)) * np.log(count/len(activity_types)) 
                          for count in type_counts.values())
        
        # 活动规律性（重复模式）
        patterns = self._extract_patterns(activity_sequence)
        pattern_diversity = len(patterns) / len(activity_sequence)
        
        # 时间分布均匀性
        hourly_activity = np.zeros(24)
        for activity in activity_sequence:
            hour = datetime.fromtimestamp(activity['timestamp']).hour
            hourly_activity[hour] += 1
            
        # 计算均匀性（反熵）
        hourly_probs = hourly_activity / (np.sum(hourly_activity) + 1e-8)
        uniformity = 1 + np.sum(hourly_probs * np.log(hourly_probs + 1e-8)) / np.log(24)
        
        # 综合多样性分数
        diversity_score = (type_entropy / np.log(len(type_counts)) + 
                          pattern_diversity + 
                          uniformity) / 3
        
        return {
            'sufficient_data': True,
            'diversity_score': diversity_score,
            'type_entropy': type_entropy,
            'pattern_diversity': pattern_diversity,
            'temporal_uniformity': uniformity
        }
        
    def _extract_patterns(self, activity_sequence, pattern_length=3):
        """提取行为模式"""
        patterns = set()
        for i in range(len(activity_sequence) - pattern_length + 1):
            pattern = tuple(activity['type'] for activity in activity_sequence[i:i+pattern_length])
            patterns.add(pattern)
        return patterns
```

## 3. 时间序列分析算法

### 3.1 动态时间规整算法
```python
class DTWAnomalyDetector:
    def __init__(self, window_size=30, threshold_percentile=90):
        self.window_size = window_size
        self.threshold_percentile = threshold_percentile
        
    def calculate_dtw_distance(self, series1, series2):
        """计算动态时间规整距离"""
        n, m = len(series1), len(series2)
        
        # 构建距离矩阵
        distance_matrix = np.zeros((n + 1, m + 1))
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                distance_matrix[i][j] = abs(series1[i-1] - series2[j-1])
                
        # DTW距离计算
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                distance_matrix[i][j] += min(
                    distance_matrix[i-1][j],      # 插入
                    distance_matrix[i][j-1],      # 删除
                    distance_matrix[i-1][j-1]     # 匹配
                )
                
        return distance_matrix[n][m]
        
    def detect_sequence_anomaly(self, current_sequence, reference_sequences):
        """检测序列模式异常"""
        distances = []
        
        for ref_seq in reference_sequences:
            if len(ref_seq) == len(current_sequence):
                dist = self.calculate_dtw_distance(current_sequence, ref_seq)
                distances.append(dist)
                
        if not distances:
            return {'anomaly_detected': False, 'confidence': 0}
            
        # 计算异常阈值
        threshold = np.percentile(distances, self.threshold_percentile)
        
        # 当前序列与最近模式的距离
        min_distance = min(distances)
        anomaly_detected = min_distance > threshold
        
        # 计算异常置信度
        confidence = min((min_distance - np.median(distances)) / 
                        (threshold - np.median(distances) + 1e-8), 1.0)
        
        return {
            'anomaly_detected': anomaly_detected,
            'anomaly_score': confidence,
            'min_distance': min_distance,
            'distance_threshold': threshold,
            'relative_position': np.percentile(distances, 
                100 * sum(1 for d in distances if d <= min_distance) / len(distances))
        }
```

### 3.2 季节性分解分析
```python
class SeasonalDecomposer:
    def __init__(self, seasonal_period=7):  # 7天周期
        self.seasonal_period = seasonal_period
        
    def decompose_time_series(self, time_series):
        """时间序列季节性分解"""
        # 移动平均趋势提取
        trend = self._extract_trend(time_series)
        
        # 季节性成分提取
        seasonal = self._extract_seasonal(time_series, trend)
        
        # 残差成分
        residual = time_series - trend - seasonal
        
        return {
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual,
            'reconstructed': trend + seasonal
        }
        
    def _extract_trend(self, time_series):
        """提取趋势成分"""
        # 使用移动平均
        window = min(self.seasonal_period * 2, len(time_series) // 4)
        if window < 2:
            return np.zeros_like(time_series)
            
        trend = np.convolve(time_series, np.ones(window)/window, mode='same')
        return trend
        
    def _extract_seasonal(self, time_series, trend):
        """提取季节性成分"""
        detrended = time_series - trend
        
        # 按周期位置分组
        seasonal_components = {}
        period_positions = []
        
        for i, value in enumerate(detrended):
            position = i % self.seasonal_period
            if position not in seasonal_components:
                seasonal_components[position] = []
            seasonal_components[position].append(value)
            period_positions.append(position)
            
        # 计算每个位置的季节性因子
        seasonal_factors = {}
        for position, values in seasonal_components.items():
            seasonal_factors[position] = np.mean(values)
            
        # 重构季节性序列
        seasonal = np.array([seasonal_factors[pos] for pos in period_positions])
        return seasonal
        
    def detect_seasonal_anomaly(self, current_decomposition, historical_decompositions):
        """检测季节性模式异常"""
        if not historical_decompositions:
            return {'seasonal_anomaly': False}
            
        # 分析当前残差
        current_residual = current_decomposition['residual']
        residual_energy = np.sum(current_residual ** 2)
        
        # 与历史残差比较
        historical_energies = [np.sum(dec['residual'] ** 2) 
                             for dec in historical_decompositions]
        
        # 异常判断
        threshold = np.percentile(historical_energies, 95)
        residual_anomaly = residual_energy > threshold
        
        # 季节性模式变化分析
        seasonal_change = self._analyze_seasonal_change(
            current_decomposition['seasonal'], 
            historical_decompositions
        )
        
        return {
            'seasonal_anomaly': residual_anomaly or seasonal_change['change_detected'],
            'residual_anomaly': residual_anomaly,
            'seasonal_change': seasonal_change,
            'residual_energy': residual_energy,
            'residual_threshold': threshold
        }
        
    def _analyze_seasonal_change(self, current_seasonal, historical_decompositions):
        """分析季节性变化"""
        historical_seasonals = [dec['seasonal'] for dec in historical_decompositions]
        
        if not historical_seasonals:
            return {'change_detected': False}
            
        # 计算季节性相似度
        similarities = []
        for hist_seasonal in historical_seasonals:
            similarity = np.corrcoef(current_seasonal, hist_seasonal)[0, 1]
            similarities.append(similarity)
            
        # 平均相似度
        avg_similarity = np.mean(similarities)
        change_detected = avg_similarity < 0.7  # 相似度低于70%
        
        return {
            'change_detected': change_detected,
            'average_similarity': avg_similarity,
            'min_similarity': min(similarities),
            'seasonal_coherence': 1 - np.std(similarities)
        }
```

## 4. 自适应基线模型

### 4.1 在线学习基线更新
```python
class AdaptiveBaselineModel:
    def __init__(self, user_id, learning_rate=0.1, forgetting_factor=0.95, 
                 confidence_threshold=0.8):
        self.user_id = user_id
        self.learning_rate = learning_rate
        self.forgetting_factor = forgetting_factor
        self.confidence_threshold = confidence_threshold
        
        # 基线参数
        self.baseline_means = {}
        self.baseline_variances = {}
        self.confidence_scores = {}
        self.data_quality_scores = {}
        
        # 异常历史
        self.anomaly_history = []
        self.normal_samples = []
        
    def update_baseline(self, feature_name, new_value, timestamp, data_quality=1.0):
        """在线更新基线模型"""
        # 初始化基线
        if feature_name not in self.baseline_means:
            self.baseline_means[feature_name] = new_value
            self.baseline_variances[feature_name] = 1.0
            self.confidence_scores[feature_name] = data_quality
            return
            
        # 计算当前值的异常得分
        anomaly_score = self._calculate_anomaly_score(feature_name, new_value)
        
        # 判断是否为正常样本
        is_normal_sample = anomaly_score < (1 - self.confidence_threshold)
        
        # 更新基线（仅使用正常样本）
        if is_normal_sample:
            # 更新均值（指数移动平均）
            old_mean = self.baseline_means[feature_name]
            new_mean = (1 - self.learning_rate) * old_mean + self.learning_rate * new_value
            self.baseline_means[feature_name] = new_mean
            
            # 更新方差
            old_variance = self.baseline_variances[feature_name]
            prediction_error = new_value - old_mean
            new_variance = ((1 - self.learning_rate) * old_variance + 
                          self.learning_rate * prediction_error ** 2)
            self.baseline_variances[feature_name] = max(new_variance, 0.01)
            
            # 保存正常样本
            self.normal_samples.append((timestamp, new_value, data_quality))
            
            # 限制样本数量（遗忘机制）
            max_samples = 1000
            if len(self.normal_samples) > max_samples:
                self.normal_samples = self.normal_samples[-max_samples:]
                
        # 更新置信度
        self.confidence_scores[feature_name] *= self.forgetting_factor
        self.confidence_scores[feature_name] += (1 - self.forgetting_factor) * data_quality
        
        # 更新数据质量得分
        self.data_quality_scores[feature_name] = data_quality
        
    def _calculate_anomaly_score(self, feature_name, value):
        """计算异常得分"""
        if feature_name not in self.baseline_means:
            return 0.0
            
        mean = self.baseline_means[feature_name]
        variance = self.baseline_variances[feature_name]
        
        # Z-score异常得分
        z_score = abs(value - mean) / (np.sqrt(variance) + 1e-8)
        
        # 转换为概率得分（0-1）
        anomaly_score = 1 - np.exp(-z_score / 2)
        
        return min(anomaly_score, 1.0)
        
    def get_baseline_stats(self, feature_name):
        """获取基线统计信息"""
        if feature_name not in self.baseline_means:
            return None
            
        return {
            'mean': self.baseline_means[feature_name],
            'std': np.sqrt(self.baseline_variances[feature_name]),
            'confidence': self.confidence_scores[feature_name],
            'data_quality': self.data_quality_scores.get(feature_name, 0),
            'sample_count': len(self.normal_samples)
        }
        
    def detect_adaptive_anomaly(self, feature_name, new_value):
        """自适应异常检测"""
        if feature_name not in self.baseline_means:
            return {'anomaly_detected': False, 'confidence': 0}
            
        baseline_stats = self.get_baseline_stats(feature_name)
        
        # 计算自适应阈值
        std = baseline_stats['std']
        confidence = baseline_stats['confidence']
        
        # 动态调整阈值
        adaptive_threshold = 2.0 + (1 - confidence) * 2.0  # 置信度低时放宽阈值
        
        # 异常检测
        z_score = abs(new_value - baseline_stats['mean']) / (std + 1e-8)
        anomaly_detected = z_score > adaptive_threshold
        
        # 计算异常置信度
        if anomaly_detected:
            confidence_score = min((z_score - adaptive_threshold + 1) / 2, 1.0)
        else:
            confidence_score = 1 - min(z_score / adaptive_threshold, 1.0)
            
        return {
            'anomaly_detected': anomaly_detected,
            'confidence': confidence_score,
            'z_score': z_score,
            'adaptive_threshold': adaptive_threshold,
            'baseline_mean': baseline_stats['mean'],
            'baseline_std': std,
            'model_confidence': confidence
        }
```

### 4.2 多维基线模型
```python
class MultidimensionalBaseline:
    def __init__(self, feature_dimensions, learning_rate=0.1):
        self.feature_dimensions = feature_dimensions
        self.learning_rate = learning_rate
        
        # 多维协方差矩阵
        self.covariance_matrix = np.eye(len(feature_dimensions))
        self.mean_vector = np.zeros(len(feature_dimensions))
        self.sample_count = 0
        
        # 特征权重
        self.feature_weights = np.ones(len(feature_dimensions))
        
    def update_multidimensional_baseline(self, feature_values, timestamps, qualities):
        """更新多维基线"""
        # 特征有效性检查
        valid_indices = [i for i, (val, qual) in enumerate(zip(feature_values, qualities)) 
                        if qual > 0.5]  # 数据质量阈值
        
        if len(valid_indices) < 2:  # 需要至少2个有效特征
            return False
            
        # 提取有效特征
        valid_features = np.array([feature_values[i] for i in valid_indices])
        valid_weights = np.array([self.feature_weights[i] * qualities[i] for i in valid_indices])
        
        # 更新加权均值
        old_mean = self.mean_vector.copy()
        for i, idx in enumerate(valid_indices):
            self.mean_vector[idx] = ((1 - self.learning_rate) * self.mean_vector[idx] + 
                                   self.learning_rate * valid_features[i])
        
        # 更新协方差矩阵
        if self.sample_count > 0:
            mean_diff_old = old_mean - self.mean_vector
            mean_diff_new = np.zeros(len(self.feature_dimensions))
            
            for i, idx in enumerate(valid_indices):
                mean_diff_new[idx] = valid_features[i] - self.mean_vector[idx]
                
            # 更新协方差
            for i in range(len(self.feature_dimensions)):
                for j in range(len(self.feature_dimensions)):
                    if i == j:
                        self.covariance_matrix[i][j] *= (1 - self.learning_rate)
                    else:
                        self.covariance_matrix[i][j] *= (1 - self.learning_rate * 0.5)
                        
            # 添加新的方差贡献
            for i, idx in enumerate(valid_indices):
                self.covariance_matrix[idx][idx] += self.learning_rate * valid_features[i] ** 2
                
        self.sample_count += 1
        
        # 更新特征权重
        for i, idx in enumerate(valid_indices):
            # 基于方差更新权重（方差越小，权重越大）
            feature_var = self.covariance_matrix[idx][idx]
            weight_update = 1 / (feature_var + 1e-8)
            self.feature_weights[idx] = ((1 - self.learning_rate) * self.feature_weights[idx] + 
                                       self.learning_rate * weight_update)
        
        return True
        
    def detect_multidimensional_anomaly(self, feature_values, qualities):
        """多维异常检测"""
        if self.sample_count < 10:  # 需要足够样本
            return {'anomaly_detected': False, 'confidence': 0}
            
        # 构建检测向量
        detection_vector = np.array(feature_values)
        
        # 马氏距离计算
        try:
            # 使用伪逆以处理奇异矩阵
            cov_inv = np.linalg.pinv(self.covariance_matrix)
            mean_diff = detection_vector - self.mean_vector
            
            # 加权马氏距离
            mahalanobis_dist = np.sqrt(mean_diff.T @ cov_inv @ mean_diff)
            
            # 基于特征权重的距离修正
            weighted_distance = 0
            for i, value in enumerate(feature_values):
                if qualities[i] > 0.5:  # 有效特征
                    weighted_distance += self.feature_weights[i] * abs(value - self.mean_vector[i])
                    
            # 异常阈值
            threshold = 3.0  # 卡方分布阈值
            
            anomaly_detected = mahalanobis_dist > threshold
            
            # 置信度计算
            if anomaly_detected:
                confidence = min((mahalanobis_dist - threshold + 1) / 3, 1.0)
            else:
                confidence = 1 - min(mahalanobis_dist / threshold, 1.0)
                
            return {
                'anomaly_detected': anomaly_detected,
                'confidence': confidence,
                'mahalanobis_distance': mahalanobis_dist,
                'weighted_distance': weighted_distance,
                'threshold': threshold,
                'effective_features': sum(1 for q in qualities if q > 0.5)
            }
            
        except np.linalg.LinAlgError:
            # 矩阵计算失败时的降级检测
            return self._fallback_detection(feature_values, qualities)
            
    def _fallback_detection(self, feature_values, qualities):
        """降级检测（当协方差矩阵奇异时）"""
        anomaly_scores = []
        
        for i, (value, quality) in enumerate(zip(feature_values, qualities)):
            if quality > 0.5:
                mean = self.mean_vector[i]
                std = np.sqrt(self.covariance_matrix[i][i])
                
                z_score = abs(value - mean) / (std + 1e-8)
                anomaly_scores.append(z_score)
                
        if not anomaly_scores:
            return {'anomaly_detected': False, 'confidence': 0}
            
        max_score = max(anomaly_scores)
        anomaly_detected = max_score > 3.0
        
        confidence = min(max_score / 3.0, 1.0) if anomaly_detected else 1 - min(max_score / 3.0, 1.0)
        
        return {
            'anomaly_detected': anomaly_detected,
            'confidence': confidence,
            'max_z_score': max_score,
            'detection_method': 'fallback'
        }
```

## 5. 多设备数据融合分析

### 5.1 数据同步与对齐
```python
class MultiDeviceDataFusion:
    def __init__(self, sync_tolerance=300):  # 5分钟同步容差
        self.sync_tolerance = sync_tolerance
        
        # 设备配置
        self.device_configs = {
            'wearable': {
                'data_types': ['activity', 'heart_rate', 'steps'],
                'sampling_rate': 60,  # 秒
                'reliability': 0.9
            },
            'mattress': {
                'data_types': ['sleep', 'breathing', 'movement'],
                'sampling_rate': 300,  # 5分钟
                'reliability': 0.8
            },
            'environmental': {
                'data_types': ['temperature', 'humidity', 'air_quality'],
                'sampling_rate': 1800,  # 30分钟
                'reliability': 0.7
            }
        }
        
    def synchronize_data(self, device_data):
        """多设备数据同步"""
        synchronized_data = {}
        
        # 找到时间交集
        all_timestamps = set()
        for device, data in device_data.items():
            if 'timestamp' in data:
                all_timestamps.add(data['timestamp'])
                
        if not all_timestamps:
            return {}
            
        # 为每个时间点构建同步数据
        for timestamp in sorted(all_timestamps):
            sync_point = {'timestamp': timestamp, 'devices': {}}
            
            # 收集该时间点附近的设备数据
            for device, data in device_data.items():
                if 'timestamp' in data:
                    time_diff = abs(data['timestamp'] - timestamp)
                    if time_diff <= self.sync_tolerance:
                        sync_point['devices'][device] = data
                        
            if len(sync_point['devices']) > 1:  # 至少2个设备有数据
                synchronized_data[timestamp] = sync_point
                
        return synchronized_data
        
    def extract_fused_features(self, synchronized_data):
        """提取融合特征"""
        fused_features = []
        
        for timestamp, data_point in synchronized_data.items():
            features = {'timestamp': timestamp}
            
            # 活动相关融合
            activity_features = self._fuse_activity_features(data_point['devices'])
            features.update(activity_features)
            
            # 睡眠相关融合
            sleep_features = self._fuse_sleep_features(data_point['devices'])
            features.update(sleep_features)
            
            # 环境相关融合
            environmental_features = self._fuse_environmental_features(data_point['devices'])
            features.update(environmental_features)
            
            # 计算数据可靠性
            reliability = self._calculate_data_reliability(data_point['devices'])
            features['data_reliability'] = reliability
            
            fused_features.append(features)
            
        return fused_features
        
    def _fuse_activity_features(self, device_data):
        """融合活动特征"""
        activity_features = {}
        
        # 手环活动数据
        if 'wearable' in device_data:
            wearable = device_data['wearable']
            activity_features.update({
                'steps': wearable.get('steps', 0),
                'activity_level': wearable.get('activity_level', 0),
                'heart_rate': wearable.get('heart_rate', 0)
            })
            
        # 床垫活动数据
        if 'mattress' in device_data:
            mattress = device_data['mattress']
            activity_features.update({
                'night_movement': mattress.get('movement_intensity', 0),
                'restlessness': mattress.get('restlessness_score', 0)
            })
            
        # 计算综合活动指数
        activity_components = [
            activity_features.get('steps', 0) / 10000,  # 步数标准化
            activity_features.get('activity_level', 0) / 100,  # 活动强度标准化
            activity_features.get('heart_rate', 60) / 200 * 100,  # 心率标准化
            (100 - activity_features.get('night_movement', 0)) / 100  # 夜间安眠度
        ]
        
        activity_features['composite_activity_index'] = np.mean(activity_components) * 100
        
        return activity_features
        
    def _fuse_sleep_features(self, device_data):
        """融合睡眠特征"""
        sleep_features = {}
        
        if 'mattress' in device_data:
            mattress = device_data['mattress']
            sleep_features.update({
                'sleep_quality_score': mattress.get('sleep_score', 0),
                'deep_sleep_percentage': mattress.get('deep_sleep_ratio', 0) * 100,
                'rem_sleep_percentage': mattress.get('rem_sleep_ratio', 0) * 100,
                'sleep_efficiency': mattress.get('sleep_efficiency', 0) * 100
            })
            
        # 如果有可穿戴设备的睡眠数据
        if 'wearable' in device_data and 'sleep_data' in device_data['wearable']:
            wearable_sleep = device_data['wearable']['sleep_data']
            sleep_features.update({
                'wearable_sleep_score': wearable_sleep.get('sleep_score', 0),
                'sleep_duration_wearable': wearable_sleep.get('duration', 0)
            })
            
        return sleep_features
        
    def _fuse_environmental_features(self, device_data):
        """融合环境特征"""
        environmental_features = {}
        
        if 'environmental' in device_data:
            env = device_data['environmental']
            environmental_features.update({
                'room_temperature': env.get('temperature', 22),
                'humidity_level': env.get('humidity', 50),
                'air_quality_index': env.get('air_quality', 50)
            })
            
        # 环境舒适度评分
        temp_score = 1 - abs(environmental_features.get('room_temperature', 22) - 22) / 10
        humidity_score = 1 - abs(environmental_features.get('humidity_level', 50) - 50) / 30
        air_score = 1 - environmental_features.get('air_quality_index', 50) / 100
        
        environmental_features['environmental_comfort_score'] = (
            (temp_score + humidity_score + air_score) / 3 * 100
        )
        
        return environmental_features
        
    def _calculate_data_reliability(self, device_data):
        """计算数据可靠性"""
        reliabilities = []
        
        for device_name, device_config in self.device_configs.items():
            if device_name in device_data:
                reliability = device_config['reliability']
                
                # 根据数据完整性调整可靠性
                expected_data_types = set(device_config['data_types'])
                available_data_types = set(device_data[device_name].keys()) & expected_data_types
                
                completeness = len(available_data_types) / len(expected_data_types)
                adjusted_reliability = reliability * completeness
                
                reliabilities.append(adjusted_reliability)
                
        return np.mean(reliabilities) if reliabilities else 0
```

### 5.2 冲突检测与协调
```python
class DataConflictResolver:
    def __init__(self, conflict_threshold=0.3):
        self.conflict_threshold = conflict_threshold
        
    def detect_data_conflicts(self, fused_features):
        """检测数据冲突"""
        conflicts = []
        
        # 检测睡眠时长冲突
        mattress_duration = fused_features.get('sleep_duration', 0)
        wearable_duration = fused_features.get('sleep_duration_wearable', 0)
        
        if mattress_duration > 0 and wearable_duration > 0:
            duration_diff = abs(mattress_duration - wearable_duration)
            duration_ratio = duration_diff / max(mattress_duration, wearable_duration)
            
            if duration_ratio > self.conflict_threshold:
                conflicts.append({
                    'type': 'sleep_duration_conflict',
                    'mattress_value': mattress_duration,
                    'wearable_value': wearable_duration,
                    'difference_ratio': duration_ratio
                })
                
        # 检测睡眠质量评分冲突
        mattress_score = fused_features.get('sleep_quality_score', 0)
        wearable_score = fused_features.get('wearable_sleep_score', 0)
        
        if mattress_score > 0 and wearable_score > 0:
            score_diff = abs(mattress_score - wearable_score)
            score_ratio = score_diff / max(mattress_score, wearable_score)
            
            if score_ratio > self.conflict_threshold:
                conflicts.append({
                    'type': 'sleep_quality_conflict',
                    'mattress_value': mattress_score,
                    'wearable_value': wearable_score,
                    'difference_ratio': score_ratio
                })
                
        return conflicts
        
    def resolve_conflicts(self, fused_features, conflicts):
        """解决数据冲突"""
        resolved_features = fused_features.copy()
        
        for conflict in conflicts:
            if conflict['type'] == 'sleep_duration_conflict':
                # 基于可靠性加权平均
                mattress_reliability = 0.8  # 床垫通常更准确
                wearable_reliability = 0.7
                
                total_weight = mattress_reliability + wearable_reliability
                weighted_duration = (
                    conflict['mattress_value'] * mattress_reliability +
                    conflict['wearable_value'] * wearable_reliability
                ) / total_weight
                
                resolved_features['sleep_duration_resolved'] = weighted_duration
                
            elif conflict['type'] == 'sleep_quality_conflict':
                # 使用床垫评分作为主要依据
                resolved_features['sleep_quality_resolved'] = conflict['mattress_value']
                
        return resolved_features
```

## 6. 平台架构集成

### 6.1 数据模型设计
```sql
-- 用户基线模型表
CREATE TABLE user_baseline_models (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    baseline_mean DECIMAL(10,4),
    baseline_variance DECIMAL(10,6),
    confidence_score DECIMAL(3,2),
    data_quality_score DECIMAL(3,2),
    sample_count INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_feature (user_id, feature_name)
);

-- 异常检测记录表
CREATE TABLE anomaly_detection_records (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    detection_timestamp TIMESTAMP NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    anomaly_score DECIMAL(4,3),
    z_score DECIMAL(6,3),
    current_value DECIMAL(10,4),
    baseline_mean DECIMAL(10,4),
    confidence DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_timestamp (user_id, detection_timestamp),
    INDEX idx_anomaly_type (anomaly_type)
);

-- 设备融合数据表
CREATE TABLE fused_sensor_data (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    composite_activity_index DECIMAL(5,2),
    sleep_quality_score DECIMAL(5,2),
    environmental_comfort_score DECIMAL(5,2),
    data_reliability DECIMAL(3,2),
    raw_wearable_data JSONB,
    raw_mattress_data JSONB,
    raw_environmental_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_timestamp (user_id, timestamp)
);

-- 告警记录表
CREATE TABLE anomaly_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity_level INTEGER CHECK (severity_level BETWEEN 1 AND 5),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    detection_data JSONB,
    response_time_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_status (user_id, status),
    INDEX idx_severity (severity_level)
);
```

### 6.2 API接口设计
```typescript
// 异常检测API接口
interface AnomalyDetectionAPI {
  // 实时异常检测
  detectAnomaly(request: {
    userId: string;
    featureData: {
      timestamp: number;
      features: Record<string, number>;
      qualities: Record<string, number>;
    };
    detectionTypes: AnomalyType[];
  }): Promise<AnomalyDetectionResponse>;
  
  // 更新基线模型
  updateBaseline(request: {
    userId: string;
    featureName: string;
    value: number;
    timestamp: number;
    quality: number;
  }): Promise<BaselineUpdateResponse>;
  
  // 获取基线统计
  getBaselineStats(request: {
    userId: string;
    featureNames: string[];
  }): Promise<BaselineStatsResponse>;
  
  // 获取异常历史
  getAnomalyHistory(request: {
    userId: string;
    startTime: number;
    endTime: number;
    anomalyTypes?: AnomalyType[];
  }): Promise<AnomalyHistoryResponse>;
  
  // 批量数据融合
  fuseMultiDeviceData(request: {
    userId: string;
    deviceData: Record<string, DeviceData>;
    timeRange: {
      start: number;
      end: number;
    };
  }): Promise<FusionResultResponse>;
}

type AnomalyType = 
  | 'activity_decrease'
  | 'activity_increase' 
  | 'sleep_time_anomaly'
  | 'sleep_quality_anomaly'
  | 'cognitive_decline'
  | 'behavioral_rhythm_anomaly'
  | 'seasonal_pattern_change';

interface AnomalyDetectionResponse {
  anomalyDetected: boolean;
  anomalyTypes: AnomalyType[];
  confidence: number;
  detectionDetails: {
    featureName: string;
    currentValue: number;
    baselineMean: number;
    zScore: number;
    anomalyScore: number;
  }[];
  processingTimeMs: number;
}
```

### 6.3 配置管理
```yaml
# 异常检测配置文件
anomaly_detection:
  global_settings:
    response_time_target: 120  # 秒
    data_fusion_enabled: true
    adaptive_baseline_enabled: true
    
  activity_detection:
    window_size_days: 7
    threshold_sigma: 2.5
    min_data_points: 50
    trend_analysis_days: 3
    
  sleep_detection:
    time_tolerance_minutes: 60
    quality_threshold: 60
    duration_variance_threshold: 120  # 分钟
    
  cognitive_detection:
    reaction_time_threshold_ms: 2000
    min_reaction_samples: 20
    diversity_threshold: 0.3
    
  data_fusion:
    sync_tolerance_seconds: 300
    conflict_threshold: 0.3
    reliability_weights:
      wearable: 0.9
      mattress: 0.8
      environmental: 0.7
      
  alerting:
    min_confidence_threshold: 0.7
    severity_mapping:
      high_confidence: 4
      medium_confidence: 3
      low_confidence: 2
      
  performance:
    max_processing_time_ms: 3000
    batch_size: 1000
    cache_ttl_seconds: 300
```

## 7. 实时监控Edge Function

### 7.1 数据流处理Edge Function
```typescript
// edge-function/anomaly-detection.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

interface SensorData {
  user_id: string;
  device_type: 'wearable' | 'mattress' | 'environmental';
  timestamp: number;
  data: Record<string, any>;
  quality_score: number;
}

interface AnomalyAlert {
  user_id: string;
  alert_type: string;
  severity: number;
  timestamp: number;
  confidence: number;
  data: Record<string, any>;
}

interface BaselineModel {
  [key: string]: {
    mean: number;
    variance: number;
    confidence: number;
    last_update: number;
  };
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
  'Access-Control-Max-Age': '86400',
  'Access-Control-Allow-Credentials': 'false'
};

// 全局缓存（实际部署中应使用Redis）
const baselineCache = new Map<string, BaselineModel>();
const anomalyHistory = new Map<string, any[]>();

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const { action, data } = await req.json();

    switch (action) {
      case 'detect_anomaly':
        return await handleAnomalyDetection(data);
      case 'update_baseline':
        return await handleBaselineUpdate(data);
      case 'fuse_multi_device':
        return await handleMultiDeviceFusion(data);
      case 'get_anomaly_status':
        return await handleGetAnomalyStatus(data);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  } catch (error) {
    console.error('Edge function error:', error);
    return new Response(
      JSON.stringify({ error: { code: 'FUNCTION_ERROR', message: error.message } }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

async function handleAnomalyDetection(data: any) {
  const startTime = Date.now();
  const { user_id, sensor_data, detection_types } = data;

  // 数据预处理
  const processedData = preprocessSensorData(sensor_data);
  
  // 加载基线模型
  const baselineModel = await loadBaselineModel(user_id);
  
  // 执行异常检测
  const detectionResults = await performAnomalyDetection(
    processedData, 
    baselineModel, 
    detection_types
  );
  
  // 生成告警
  const alerts = generateAlerts(detectionResults, user_id);
  
  // 异步保存结果
  saveDetectionResults(user_id, detectionResults, alerts);
  
  const processingTime = Date.now() - startTime;
  
  return new Response(
    JSON.stringify({
      success: true,
      data: {
        alerts,
        detection_results: detectionResults,
        processing_time_ms: processingTime,
        response_time_met: processingTime <= 120000
      }
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

function preprocessSensorData(sensorData: SensorData[]): any {
  const processed: any = {
    timestamp: Date.now(),
    features: {},
    qualities: {}
  };

  for (const data of sensorData) {
    switch (data.device_type) {
      case 'wearable':
        processed.features = {
          ...processed.features,
          steps: data.data.steps || 0,
          activity_level: data.data.activity_level || 0,
          heart_rate: data.data.heart_rate || 60
        };
        break;
      case 'mattress':
        processed.features = {
          ...processed.features,
          sleep_score: data.data.sleep_score || 0,
          movement_intensity: data.data.movement_intensity || 0
        };
        break;
      case 'environmental':
        processed.features = {
          ...processed.features,
          temperature: data.data.temperature || 22,
          humidity: data.data.humidity || 50,
          air_quality: data.data.air_quality || 50
        };
        break;
    }
    
    // 设置质量分数
    processed.qualities = {
      ...processed.qualities,
      ...Object.fromEntries(
        Object.keys(data.data).map(key => [key, data.quality_score])
      )
    };
  }

  return processed;
}

async function loadBaselineModel(userId: string): Promise<BaselineModel> {
  if (baselineCache.has(userId)) {
    return baselineCache.get(userId)!;
  }

  // 从数据库加载基线模型
  // const result = await supabase
  //   .from('user_baseline_models')
  //   .select('*')
  //   .eq('user_id', userId);
  
  // 模拟基线模型
  const mockBaseline: BaselineModel = {
    steps: { mean: 8000, variance: 1600000, confidence: 0.9, last_update: Date.now() },
    activity_level: { mean: 45, variance: 225, confidence: 0.85, last_update: Date.now() },
    heart_rate: { mean: 72, variance: 64, confidence: 0.9, last_update: Date.now() }
  };
  
  baselineCache.set(userId, mockBaseline);
  return mockBaseline;
}

async function performAnomalyDetection(
  processedData: any, 
  baselineModel: BaselineModel, 
  detectionTypes: string[]
): Promise<any[]> {
  const results: any[] = [];
  
  for (const [featureName, value] of Object.entries(processedData.features)) {
    if (!baselineModel[featureName]) continue;
    
    const baseline = baselineModel[featureName];
    
    // 计算Z-score
    const zScore = Math.abs(value - baseline.mean) / Math.sqrt(baseline.variance);
    
    // 异常检测
    const isAnomaly = zScore > 2.5; // 2.5σ阈值
    
    if (isAnomaly || detectionTypes.includes('continuous_monitoring')) {
      results.push({
        feature_name: featureName,
        current_value: value,
        baseline_mean: baseline.mean,
        z_score: zScore,
        anomaly_detected: isAnomaly,
        confidence: Math.min(zScore / 2.5, 1.0) * baseline.confidence,
        timestamp: processedData.timestamp
      });
    }
  }
  
  return results;
}

function generateAlerts(detectionResults: any[], userId: string): AnomalyAlert[] {
  const alerts: AnomalyAlert[] = [];
  
  for (const result of detectionResults) {
    if (!result.anomaly_detected) continue;
    
    const severity = calculateSeverity(result.confidence, result.z_score);
    
    if (severity >= 3) { // 中等及以上严重性才生成告警
      alerts.push({
        user_id: userId,
        alert_type: `${result.feature_name}_anomaly`,
        severity,
        timestamp: Date.now(),
        confidence: result.confidence,
        data: {
          feature_name: result.feature_name,
          current_value: result.current_value,
          baseline_mean: result.baseline_mean,
          z_score: result.z_score
        }
      });
    }
  }
  
  return alerts;
}

function calculateSeverity(confidence: number, zScore: number): number {
  if (confidence >= 0.9 && zScore >= 4) return 5; // 严重
  if (confidence >= 0.8 && zScore >= 3) return 4; // 高
  if (confidence >= 0.7 && zScore >= 2.5) return 3; // 中等
  if (confidence >= 0.6) return 2; // 低
  return 1; // 轻微
}

async function saveDetectionResults(
  userId: string, 
  detectionResults: any[], 
  alerts: AnomalyAlert[]
): Promise<void> {
  // 保存检测结果到数据库
  // 保存告警信息
  
  // 更新缓存
  if (alerts.length > 0) {
    const existingHistory = anomalyHistory.get(userId) || [];
    anomalyHistory.set(userId, [...existingHistory, ...alerts]);
  }
}
```

### 7.2 流式数据处理
```typescript
// edge-function/stream-processor.ts
interface StreamProcessor {
  processStream(userId: string, dataStream: AsyncIterable<any>): Promise<void>;
  aggregateData(dataPoints: any[], windowSize: number): any;
  detectAnomaliesInStream(aggregatedData: any): any[];
}

class RealTimeStreamProcessor implements StreamProcessor {
  private aggregationWindow = 300000; // 5分钟窗口
  private anomalyBuffer: any[] = [];
  
  async processStream(userId: string, dataStream: AsyncIterable<any>): Promise<void> {
    const windowBuffer: any[] = [];
    const windowStart = Date.now();
    
    for await (const dataPoint of dataStream) {
      windowBuffer.push(dataPoint);
      
      // 检查窗口是否需要聚合
      if (this.shouldAggregate(windowBuffer, windowStart)) {
        const aggregatedData = this.aggregateData(windowBuffer, this.aggregationWindow);
        const anomalies = this.detectAnomaliesInStream(aggregatedData);
        
        if (anomalies.length > 0) {
          await this.handleStreamAnomalies(userId, anomalies, aggregatedData);
        }
        
        windowBuffer.length = 0; // 清空缓冲区
      }
    }
    
    // 处理剩余数据
    if (windowBuffer.length > 0) {
      const finalAggregated = this.aggregateData(windowBuffer, this.aggregationWindow);
      const finalAnomalies = this.detectAnomaliesInStream(finalAggregated);
      
      if (finalAnomalies.length > 0) {
        await this.handleStreamAnomalies(userId, finalAnomalies, finalAggregated);
      }
    }
  }
  
  aggregateData(dataPoints: any[], windowSize: number): any {
    if (dataPoints.length === 0) return {};
    
    const features: Record<string, number[]> = {};
    let totalQuality = 0;
    
    // 收集所有特征值
    for (const point of dataPoints) {
      for (const [feature, value] of Object.entries(point.features || {})) {
        if (!features[feature]) features[feature] = [];
        features[feature].push(value);
      }
      totalQuality += point.quality || 1;
    }
    
    // 计算聚合特征
    const aggregated: any = {
      timestamp: Date.now(),
      window_size: dataPoints.length,
      avg_quality: totalQuality / dataPoints.length
    };
    
    for (const [feature, values] of Object.entries(features)) {
      aggregated[feature] = {
        mean: values.reduce((sum, val) => sum + val, 0) / values.length,
        median: values.sort((a, b) => a - b)[Math.floor(values.length / 2)],
        std: Math.sqrt(
          values.reduce((sum, val) => sum + Math.pow(val - aggregated[feature]?.mean || 0, 2), 0) / values.length
        ),
        trend: this.calculateTrend(values)
      };
    }
    
    return aggregated;
  }
  
  calculateTrend(values: number[]): number {
    if (values.length < 2) return 0;
    
    const n = values.length;
    const x = Array.from({length: n}, (_, i) => i);
    const y = values;
    
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX + 1e-8);
    return slope;
  }
  
  detectAnomaliesInStream(aggregatedData: any): any[] {
    const anomalies: any[] = [];
    
    for (const [feature, stats] of Object.entries(aggregatedData)) {
      if (typeof stats === 'object' && 'mean' in stats) {
        const { mean, std, trend } = stats as any;
        
        // 检测统计异常
        if (std > mean * 0.5) { // 高变异性
          anomalies.push({
            type: 'high_variability',
            feature,
            severity: 3,
            details: { mean, std, threshold: mean * 0.5 }
          });
        }
        
        // 检测趋势异常
        if (Math.abs(trend) > 0.1) { // 显著趋势变化
          anomalies.push({
            type: 'trend_anomaly',
            feature,
            severity: Math.abs(trend) > 0.3 ? 4 : 2,
            details: { trend, mean }
          });
        }
      }
    }
    
    return anomalies;
  }
  
  shouldAggregate(buffer: any[], windowStart: number): boolean {
    return buffer.length >= 10 || (Date.now() - windowStart) >= this.aggregationWindow;
  }
  
  async handleStreamAnomalies(userId: string, anomalies: any[], aggregatedData: any): Promise<void> {
    // 发送到告警系统
    const alertPromises = anomalies.map(async (anomaly) => {
      return fetch('/api/alerts/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          anomaly_type: anomaly.type,
          severity: anomaly.severity,
          feature: anomaly.feature,
          aggregated_data: aggregatedData,
          detection_time: Date.now(),
          stream_source: true
        })
      });
    });
    
    await Promise.all(alertPromises);
  }
}
```

## 8. 性能优化与部署

### 8.1 性能优化策略

#### 8.1.1 缓存机制
```typescript
// cache/lru-cache.ts
class LRUCache<T> {
  private cache = new Map<string, { value: T; timestamp: number }>();
  private maxSize: number;
  private ttl: number;
  
  constructor(maxSize: number = 1000, ttlMinutes: number = 30) {
    this.maxSize = maxSize;
    this.ttl = ttlMinutes * 60 * 1000;
  }
  
  get(key: string): T | null {
    const item = this.cache.get(key);
    
    if (!item) return null;
    
    // 检查TTL
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    // 移动到末尾（最近使用）
    this.cache.delete(key);
    this.cache.set(key, { value: item.value, timestamp: Date.now() });
    
    return item.value;
  }
  
  set(key: string, value: T): void {
    // 如果已存在，更新值和时间戳
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }
    
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, { value, timestamp: Date.now() });
  }
  
  clear(): void {
    this.cache.clear();
  }
}

// 全局缓存实例
export const baselineCache = new LRUCache<BaselineModel>(500, 60); // 1小时TTL
export const detectionCache = new LRUCache<any>(1000, 30); // 30分钟TTL
export const fusionCache = new LRUCache<any>(800, 45); // 45分钟TTL
```

#### 8.1.2 并行处理优化
```typescript
// parallel/processor.ts
class ParallelAnomalyProcessor {
  private workerPool: Worker[];
  private maxWorkers: number;
  
  constructor(maxWorkers: number = 4) {
    this.maxWorkers = maxWorkers;
    this.workerPool = [];
    
    // 初始化工作线程
    for (let i = 0; i < maxWorkers; i++) {
      this.workerPool.push(new Worker('./anomaly-worker.js'));
    }
  }
  
  async processBatch(userData: any[]): Promise<any[]> {
    const batchSize = Math.ceil(userData.length / this.maxWorkers);
    const batches = this.chunkArray(userData, batchSize);
    
    // 并行处理批次
    const promises = batches.map((batch, index) => 
      this.processBatchOnWorker(batch, index)
    );
    
    const results = await Promise.all(promises);
    return this.mergeResults(results);
  }
  
  private chunkArray<T>(array: T[], chunkSize: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
  }
  
  private async processBatchOnWorker(batch: any[], workerIndex: number): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const worker = this.workerPool[workerIndex];
      
      const timeout = setTimeout(() => {
        worker.terminate();
        reject(new Error('Worker timeout'));
      }, 30000); // 30秒超时
      
      worker.onmessage = (e) => {
        clearTimeout(timeout);
        resolve(e.data);
      };
      
      worker.onerror = (error) => {
        clearTimeout(timeout);
        reject(error);
      };
      
      worker.postMessage({
        action: 'process_batch',
        data: batch
      });
    });
  }
  
  private mergeResults(results: any[][]): any[] {
    return results.flat();
  }
  
  terminate(): void {
    this.workerPool.forEach(worker => worker.terminate());
  }
}
```

### 8.2 监控与告警

#### 8.2.1 系统监控
```typescript
// monitoring/system-monitor.ts
interface SystemMetrics {
  responseTime: number;
  throughput: number;
  errorRate: number;
  cacheHitRate: number;
  activeConnections: number;
}

class SystemMonitor {
  private metrics: SystemMetrics = {
    responseTime: 0,
    throughput: 0,
    errorRate: 0,
    cacheHitRate: 0,
    activeConnections: 0
  };
  
  private requestCount = 0;
  private errorCount = 0;
  private responseTimes: number[] = [];
  private cacheHits = 0;
  private cacheMisses = 0;
  
  recordRequest(responseTime: number): void {
    this.requestCount++;
    this.responseTimes.push(responseTime);
    
    // 保持最近的1000个响应时间
    if (this.responseTimes.length > 1000) {
      this.responseTimes = this.responseTimes.slice(-1000);
    }
    
    this.updateMetrics();
  }
  
  recordError(): void {
    this.errorCount++;
    this.updateMetrics();
  }
  
  recordCacheHit(): void {
    this.cacheHits++;
    this.updateCacheMetrics();
  }
  
  recordCacheMiss(): void {
    this.cacheMisses++;
    this.updateCacheMetrics();
  }
  
  private updateMetrics(): void {
    this.metrics.responseTime = this.calculateAverageResponseTime();
    this.metrics.throughput = this.calculateThroughput();
    this.metrics.errorRate = this.errorCount / this.requestCount;
    this.metrics.activeConnections = this.getActiveConnections();
  }
  
  private updateCacheMetrics(): void {
    const totalCacheRequests = this.cacheHits + this.cacheMisses;
    this.metrics.cacheHitRate = totalCacheRequests > 0 ? 
      this.cacheHits / totalCacheRequests : 0;
  }
  
  private calculateAverageResponseTime(): number {
    if (this.responseTimes.length === 0) return 0;
    
    const sum = this.responseTimes.reduce((a, b) => a + b, 0);
    return sum / this.responseTimes.length;
  }
  
  private calculateThroughput(): number {
    // 计算每分钟的请求数
    const oneMinuteAgo = Date.now() - 60000;
    const recentRequests = this.responseTimes.filter(time => time > oneMinuteAgo);
    return recentRequests.length;
  }
  
  private getActiveConnections(): number {
    // 实际实现中应该从连接池获取
    return Math.floor(this.requestCount * 0.1);
  }
  
  getMetrics(): SystemMetrics {
    return { ...this.metrics };
  }
  
  shouldAlert(): boolean {
    return (
      this.metrics.responseTime > 2000 || // 响应时间超过2秒
      this.metrics.errorRate > 0.05 ||     // 错误率超过5%
      this.metrics.cacheHitRate < 0.7 ||   // 缓存命中率低于70%
      this.metrics.throughput < 10         // 吞吐量过低
    );
  }
  
  generateAlert(): any {
    return {
      type: 'system_performance_alert',
      timestamp: Date.now(),
      metrics: this.getMetrics(),
      alerts: this.getAlertReasons()
    };
  }
  
  private getAlertReasons(): string[] {
    const reasons: string[] = [];
    
    if (this.metrics.responseTime > 2000) {
      reasons.push('High response time');
    }
    
    if (this.metrics.errorRate > 0.05) {
      reasons.push('High error rate');
    }
    
    if (this.metrics.cacheHitRate < 0.7) {
      reasons.push('Low cache hit rate');
    }
    
    if (this.metrics.throughput < 10) {
      reasons.push('Low throughput');
    }
    
    return reasons;
  }
}

// 全局监控实例
export const systemMonitor = new SystemMonitor();
```

### 8.3 部署配置

#### 8.3.1 Docker配置
```dockerfile
# Dockerfile
FROM denoland/deno:1.30.0

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY deps.ts ./
COPY import_map.json ./

# 下载依赖
RUN deno cache --import-map=import_map.json deps.ts

# 复制源代码
COPY src/ ./src/

# 设置环境变量
ENV DENO_ENV=production
ENV RUST_LOG=info

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["deno", "run", "--allow-net", "--allow-env", "--import-map=import_map.json", "src/main.ts"]
```

#### 8.3.2 部署脚本
```yaml
# deploy.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-detection-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anomaly-detection
  template:
    metadata:
      labels:
        app: anomaly-detection
    spec:
      containers:
      - name: anomaly-detection
        image: anomaly-detection:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: anomaly-detection-service
spec:
  selector:
    app: anomaly-detection
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 9. 测试与验证

### 9.1 单元测试
```typescript
// tests/anomaly-detector.test.ts
import { assertEquals } from "https://deno.land/std@0.168.0/testing/asserts.ts";
import { ActivityAnomalyDetector } from "../src/detectors/activity-detector.ts";

Deno.test("ActivityAnomalyDetector - detect increase anomaly", () => {
  const detector = new ActivityAnomalyDetector();
  
  // 设置基线
  const baselineData = [8000, 7500, 8200, 7800, 7900, 8100, 7700];
  detector.updateBaseline("test_user", baselineData);
  
  // 测试活动量激增
  const result = detector.detectAnomaly("test_user", 15000);
  
  assertEquals(result.anomaly_detected, true);
  assertEquals(result.anomaly_type, "activity_increase");
  assertEquals(result.anomaly_score > 0.5, true);
});

Deno.test("ActivityAnomalyDetector - detect decrease anomaly", () => {
  const detector = new ActivityAnomalyDetector();
  
  // 设置基线
  const baselineData = [8000, 7500, 8200, 7800, 7900, 8100, 7700];
  detector.updateBaseline("test_user", baselineData);
  
  // 测试活动量骤减
  const result = detector.detectAnomaly("test_user", 2000);
  
  assertEquals(result.anomaly_detected, true);
  assertEquals(result.anomaly_type, "activity_decrease");
  assertEquals(result.anomaly_score > 0.7, true);
});

Deno.test("MultiDeviceDataFusion - synchronize data", () => {
  const fusion = new MultiDeviceDataFusion();
  
  const deviceData = {
    wearable: {
      timestamp: 1640995200,
      steps: 5000,
      heart_rate: 75
    },
    mattress: {
      timestamp: 1640995205,  // 5秒差异
      sleep_score: 85
    }
  };
  
  const synchronized = fusion.synchronize_data(deviceData);
  
  assertEquals(Object.keys(synchronized).length > 0, true);
  
  const syncPoint = Object.values(synchronized)[0] as any;
  assertEquals(Object.keys(syncPoint.devices).length, 2);
});
```

### 9.2 性能测试
```typescript
// tests/performance.test.ts
import { bench } from "https://deno.land/std@0.168.0/testing/bench.ts";
import { AdaptiveBaselineModel } from "../src/models/adaptive-baseline.ts";

bench({
  name: "baseline_update_performance",
  runs: 1000,
  func(): void {
    const model = new AdaptiveBaselineModel("perf_test_user");
    
    for (let i = 0; i < 100; i++) {
      model.update_baseline("steps", Math.random() * 10000, Date.now(), 0.9);
    }
  }
});

bench({
  name: "anomaly_detection_performance",
  runs: 500,
  func(): void {
    const model = new AdaptiveBaselineModel("perf_test_user");
    
    // 模拟数据
    for (let i = 0; i < 50; i++) {
      model.update_baseline("steps", 8000 + Math.random() * 2000, Date.now(), 0.9);
    }
    
    model.detect_adaptive_anomaly("steps", 5000);
  }
});
```

### 9.3 集成测试
```typescript
// tests/integration.test.ts
import { assertEquals } from "https://deno.land/std@0.168.0/testing/asserts.ts";

Deno.test("End-to-end anomaly detection flow", async () => {
  // 1. 数据收集
  const sensorData = {
    userId: "e2e_test_user",
    data: [
      {
        device_type: "wearable",
        timestamp: Date.now(),
        data: { steps: 15000, activity_level: 80, heart_rate: 90 },
        quality_score: 0.95
      },
      {
        device_type: "mattress", 
        timestamp: Date.now(),
        data: { sleep_score: 60, movement_intensity: 40 },
        quality_score: 0.85
      }
    ]
  };
  
  // 2. 数据融合
  const fusionResult = await processSensorData(sensorData);
  assertEquals(fusionResult.fused_features.length > 0, true);
  
  // 3. 异常检测
  const detectionResult = await detectAnomalies(fusionResult);
  assertEquals(typeof detectionResult.anomaly_detected, "boolean");
  
  // 4. 响应时间检查
  assertEquals(detectionResult.processing_time_ms <= 120000, true);
  
  console.log("E2E test completed successfully");
});
```

## 10. 运维与监控

### 10.1 日志系统
```typescript
// logging/logger.ts
enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

class StructuredLogger {
  private logLevel: LogLevel;
  
  constructor(logLevel: LogLevel = LogLevel.INFO) {
    this.logLevel = logLevel;
  }
  
  info(message: string, metadata?: any): void {
    if (this.logLevel <= LogLevel.INFO) {
      this.log('INFO', message, metadata);
    }
  }
  
  warn(message: string, metadata?: any): void {
    if (this.logLevel <= LogLevel.WARN) {
      this.log('WARN', message, metadata);
    }
  }
  
  error(message: string, error?: Error, metadata?: any): void {
    if (this.logLevel <= LogLevel.ERROR) {
      this.log('ERROR', message, {
        ...metadata,
        error_message: error?.message,
        error_stack: error?.stack
      });
    }
  }
  
  debug(message: string, metadata?: any): void {
    if (this.logLevel <= LogLevel.DEBUG) {
      this.log('DEBUG', message, metadata);
    }
  }
  
  private log(level: string, message: string, metadata?: any): void {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      metadata,
      service: 'anomaly-detection',
      version: '1.0.0'
    };
    
    console.log(JSON.stringify(logEntry));
  }
}

// 性能日志装饰器
export function performanceLogger(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;
  
  descriptor.value = async function (...args: any[]) {
    const logger = new StructuredLogger();
    const startTime = Date.now();
    
    try {
      const result = await originalMethod.apply(this, args);
      const duration = Date.now() - startTime;
      
      logger.info(`Method ${propertyKey} completed`, {
        duration_ms: duration,
        args_count: args.length,
        success: true
      });
      
      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      
      logger.error(`Method ${propertyKey} failed`, error, {
        duration_ms: duration,
        args_count: args.length,
        success: false
      });
      
      throw error;
    }
  };
  
  return descriptor;
}
```

### 10.2 健康检查
```typescript
// health/health-check.ts
interface HealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'degraded';
  checks: {
    database: boolean;
    cache: boolean;
    external_apis: boolean;
  };
  metrics: {
    uptime: number;
    memory_usage: number;
    active_connections: number;
  };
  timestamp: number;
}

class HealthChecker {
  private startTime = Date.now();
  
  async performHealthCheck(): Promise<HealthCheckResult> {
    const checks = {
      database: await this.checkDatabase(),
      cache: await this.checkCache(),
      external_apis: await this.checkExternalAPIs()
    };
    
    const metrics = {
      uptime: Date.now() - this.startTime,
      memory_usage: this.getMemoryUsage(),
      active_connections: this.getActiveConnections()
    };
    
    const allHealthy = Object.values(checks).every(check => check);
    const status = allHealthy ? 'healthy' : 
                  Object.values(checks).some(check => check) ? 'degraded' : 'unhealthy';
    
    return {
      status,
      checks,
      metrics,
      timestamp: Date.now()
    };
  }
  
  private async checkDatabase(): Promise<boolean> {
    try {
      // 简单的数据库查询测试
      // const result = await database.query('SELECT 1');
      return true; // 模拟成功
    } catch {
      return false;
    }
  }
  
  private async checkCache(): Promise<boolean> {
    try {
      // 测试缓存读写
      // await cache.set('health_check', 'ok', 60);
      // const value = await cache.get('health_check');
      return true; // 模拟成功
    } catch {
      return false;
    }
  }
  
  private async checkExternalAPIs(): Promise<boolean> {
    try {
      // 检查外部API可用性
      return true; // 模拟成功
    } catch {
      return false;
    }
  }
  
  private getMemoryUsage(): number {
    // 实际实现中从系统获取内存使用情况
    return Math.random() * 100; // 模拟
  }
  
  private getActiveConnections(): number {
    // 实际实现中从连接池获取
    return Math.floor(Math.random() * 50); // 模拟
  }
}
```

## 11. 总结

本智能异常行为检测系统实现了以下核心功能：

### 11.1 技术特点
1. **实时性能**：响应时间≤2分钟，满足技术要求
2. **自适应学习**：基线模型能够动态更新和调整
3. **多设备融合**：支持手环、床垫、环境传感器数据融合
4. **智能算法**：结合统计分析和机器学习方法
5. **可扩展架构**：支持横向扩展和负载均衡

### 11.2 算法优势
1. **多维度检测**：活动量、睡眠、认知能力三维异常检测
2. **时间序列分析**：季节性分解和趋势分析
3. **冲突解决**：智能处理多设备数据冲突
4. **置信度评估**：提供可靠性的量化指标

### 11.3 系统可靠性
1. **容错机制**：降级处理和故障恢复
2. **监控体系**：全面的性能和健康监控
3. **测试覆盖**：单元测试、集成测试、性能测试
4. **运维友好**：结构化日志和健康检查

### 11.4 部署就绪
1. **容器化**：Docker容器化部署
2. **云原生**：Kubernetes编排支持
3. **微服务**：Edge Function架构
4. **缓存优化**：LRU缓存和并行处理

该系统为智能健康管理提供了强大的异常行为检测能力，能够及时发现用户的健康异常并提供可靠的预警服务。