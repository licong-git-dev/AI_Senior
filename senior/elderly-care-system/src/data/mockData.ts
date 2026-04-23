// 演示模式Mock数据
// 包含50+老人档案、100+健康记录、20+设备等完整演示数据

export interface MockElderly {
  id: string;
  name: string;
  age: number;
  gender: string;
  community: string;
  address: string;
  phone: string;
  emergencyContact: string;
  emergencyPhone: string;
  chronicDiseases: string[];
  riskLevel: number; // 1-低 2-中 3-高
}

export interface MockHealthData {
  id: string;
  userId: string;
  dataType: string;
  systolicPressure?: number;
  diastolicPressure?: number;
  heartRate?: number;
  bloodSugar?: number;
  temperature?: number;
  measurementTime: string;
  abnormalFlag: number;
}

export interface MockDevice {
  id: string;
  userId: string;
  deviceType: string;
  deviceName: string;
  batteryLevel: number;
  status: number; // 0-离线 1-在线
  lastSyncTime: string;
}

export interface MockEmergencyCall {
  id: string;
  userId: string;
  userName: string;
  callType: string;
  callTime: string;
  location: string;
  priorityLevel: number;
  status: number; // 0-待处理 1-处理中 2-已完成
  responseTime?: string;
  notes: string;
}

// 生成50个老人档案
const communities = ['仁义社区', '百步亭社区', '永清社区', '四唯社区', '台北社区', '新村社区', '西马社区', '劳动社区'];
const names = [
  '张大爷', '李奶奶', '王大爷', '刘奶奶', '陈大爷', '杨奶奶', '赵大爷', '孙奶奶', '周大爷', '吴奶奶',
  '郑大爷', '王奶奶', '冯大爷', '陈奶奶', '褚大爷', '卫奶奶', '蒋大爷', '沈奶奶', '韩大爷', '杨奶奶',
  '朱大爷', '秦奶奶', '尤大爷', '许奶奶', '何大爷', '吕奶奶', '施大爷', '张奶奶', '孔大爷', '曹奶奶',
  '严大爷', '华奶奶', '金大爷', '魏奶奶', '陶大爷', '姜奶奶', '戚大爷', '谢奶奶', '邹大爷', '喻奶奶',
  '柏大爷', '水奶奶', '窦大爷', '章奶奶', '云大爷', '苏奶奶', '潘大爷', '葛奶奶', '奚大爷', '范奶奶'
];

const chronicDiseasesList = [
  ['高血压'],
  ['糖尿病'],
  ['冠心病'],
  ['高血压', '糖尿病'],
  ['高血压', '冠心病'],
  ['糖尿病', '高血脂'],
  ['骨质疏松'],
  ['关节炎'],
  ['慢性支气管炎'],
  ['高血压', '糖尿病', '高血脂']
];

export const mockElderly: MockElderly[] = Array.from({ length: 50 }, (_, i) => ({
  id: `elder-${i + 1}`,
  name: names[i],
  age: 65 + (i % 25),
  gender: i % 2 === 0 ? '男' : '女',
  community: communities[i % 8],
  address: `武汉市江岸区${communities[i % 8]}${(i % 20) + 1}栋${(i % 6) + 1}单元${(i % 8) + 1}01`,
  phone: `138${String(13800000 + i).padStart(8, '0')}`,
  emergencyContact: i % 2 === 0 ? `${names[i]}的儿子` : `${names[i]}的女儿`,
  emergencyPhone: `139${String(13900000 + i).padStart(8, '0')}`,
  chronicDiseases: chronicDiseasesList[i % 10],
  riskLevel: i % 7 === 0 ? 3 : i % 5 === 0 ? 2 : 1
}));

// 生成设备数据（每个老人1-3个设备）
export const mockDevices: MockDevice[] = mockElderly.flatMap((elder, i) => {
  const deviceCount = 1 + (i % 3);
  return Array.from({ length: deviceCount }, (_, j) => ({
    id: `device-${i}-${j}`,
    userId: elder.id,
    deviceType: ['smartwatch', 'bed_sensor', 'camera'][j] || 'smartwatch',
    deviceName: ['智能手环', '床垫监测器', '智能摄像头'][j] || '智能手环',
    batteryLevel: 50 + (i % 50),
    status: (i + j) % 10 === 0 ? 0 : 1,
    lastSyncTime: new Date(Date.now() - (i % 24) * 3600000).toISOString()
  }));
});

// 生成健康数据（每个老人过去30天的数据，共100+条）
export const mockHealthData: MockHealthData[] = mockElderly.flatMap((elder, elderIndex) => {
  const healthRecords: MockHealthData[] = [];
  
  // 生成过去30天的数据
  for (let day = 0; day < 30; day++) {
    const baseDate = new Date(Date.now() - day * 24 * 3600000);
    
    // 血压数据（每天早上8点）
    const systolic = 120 + (elderIndex % 30) + ((day % 5) - 2) * 5;
    const diastolic = 75 + (elderIndex % 20) + ((day % 4) - 1) * 3;
    healthRecords.push({
      id: `health-${elderIndex}-${day}-bp`,
      userId: elder.id,
      dataType: 'blood_pressure',
      systolicPressure: systolic,
      diastolicPressure: diastolic,
      heartRate: 65 + (elderIndex % 20) + ((day % 5) - 2) * 3,
      measurementTime: new Date(baseDate.setHours(8 + (elderIndex % 2), 0, 0)).toISOString(),
      abnormalFlag: (systolic > 140 || diastolic > 90) ? 1 : 0
    });
    
    // 血糖数据（每天早上7点）
    const bloodSugar = 5.0 + (elderIndex % 20) * 0.1 + ((day % 5) - 2) * 0.3;
    healthRecords.push({
      id: `health-${elderIndex}-${day}-bs`,
      userId: elder.id,
      dataType: 'blood_sugar',
      bloodSugar: Number(bloodSugar.toFixed(1)),
      measurementTime: new Date(baseDate.setHours(7, 0, 0)).toISOString(),
      abnormalFlag: bloodSugar > 6.1 ? 1 : 0
    });
    
    // 心率数据（每隔一天下午2点）
    if (day % 2 === 0) {
      const heartRate = 68 + (elderIndex % 25) + ((day % 6) - 2) * 2;
      healthRecords.push({
        id: `health-${elderIndex}-${day}-hr`,
        userId: elder.id,
        dataType: 'heart_rate',
        heartRate: heartRate,
        measurementTime: new Date(baseDate.setHours(14, 0, 0)).toISOString(),
        abnormalFlag: heartRate > 90 ? 1 : 0
      });
    }
  }
  
  return healthRecords;
});

// 生成紧急呼叫记录（30%的老人有1-3次呼叫）
export const mockEmergencyCalls: MockEmergencyCall[] = mockElderly
  .filter((_, i) => i % 3 === 0)
  .flatMap((elder, i) => {
    const callCount = 1 + (i % 3);
    return Array.from({ length: callCount }, (_, j) => ({
      id: `call-${i}-${j}`,
      userId: elder.id,
      userName: elder.name,
      callType: ['manual', 'auto_fall', 'health_alert'][j % 3],
      callTime: new Date(Date.now() - (j * 7 + i % 10) * 24 * 3600000).toISOString(),
      location: `武汉市江岸区${elder.community}`,
      priorityLevel: [1, 3, 2][j % 3],
      status: 2,
      responseTime: new Date(Date.now() - (j * 7 + i % 10) * 24 * 3600000 + 15 * 60000).toISOString(),
      notes: [
        '老人主动呼叫，要求护理人员协助',
        '系统检测到跌倒事件，已及时响应',
        '健康指标异常，已通知家属和医护人员'
      ][j % 3]
    }));
  });

// 统计数据
export const mockStats = {
  totalElderly: mockElderly.length,
  totalDevices: mockDevices.length,
  onlineDevices: mockDevices.filter(d => d.status === 1).length,
  totalHealthRecords: mockHealthData.length,
  abnormalRecords: mockHealthData.filter(h => h.abnormalFlag === 1).length,
  totalEmergencyCalls: mockEmergencyCalls.length,
  highRiskElderly: mockElderly.filter(e => e.riskLevel === 3).length,
  mediumRiskElderly: mockElderly.filter(e => e.riskLevel === 2).length,
  lowRiskElderly: mockElderly.filter(e => e.riskLevel === 1).length
};

console.log('Mock数据加载完成:', mockStats);
