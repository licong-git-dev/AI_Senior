import React, { useState, useEffect } from 'react';

// 设备类型定义
interface Device {
  id: string;
  name: string;
  type: 'router' | 'switch' | 'server' | 'sensor' | 'camera' | 'gateway';
  status: 'online' | 'offline' | 'warning' | 'error';
  location: string;
  ipAddress: string;
  firmwareVersion: string;
  lastSeen: string;
}

// 模拟数据
const mockDevices: Device[] = [
  {
    id: 'dev-001',
    name: '核心路由器-01',
    type: 'router',
    status: 'online',
    location: '数据中心A-01机柜',
    ipAddress: '192.168.1.1',
    firmwareVersion: 'v2.3.1',
    lastSeen: new Date().toISOString()
  },
  {
    id: 'dev-002',
    name: '楼层交换机-02',
    type: 'switch',
    status: 'warning',
    location: '办公楼2楼-02机柜',
    ipAddress: '192.168.2.10',
    firmwareVersion: 'v1.8.2',
    lastSeen: '2024-11-18T13:45:00Z'
  },
  {
    id: 'dev-003',
    name: '边缘服务器-03',
    type: 'server',
    status: 'online',
    location: '边缘节点B-03机柜',
    ipAddress: '192.168.3.50',
    firmwareVersion: 'v3.1.0',
    lastSeen: new Date().toISOString()
  },
  {
    id: 'dev-004',
    name: '温湿度传感器-04',
    type: 'sensor',
    status: 'online',
    location: '仓库区-04位置',
    ipAddress: '192.168.4.20',
    firmwareVersion: 'v1.2.1',
    lastSeen: new Date().toISOString()
  },
  {
    id: 'dev-005',
    name: '网络摄像头-05',
    type: 'camera',
    status: 'offline',
    location: '停车场-05位置',
    ipAddress: '192.168.5.30',
    firmwareVersion: 'v2.0.5',
    lastSeen: '2024-11-17T22:30:00Z'
  }
];

// 工具函数
const getStatusColor = (status: Device['status']) => {
  switch (status) {
    case 'online': return 'text-green-600 bg-green-100';
    case 'offline': return 'text-red-600 bg-red-100';
    case 'warning': return 'text-yellow-600 bg-yellow-100';
    case 'error': return 'text-red-600 bg-red-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

const getStatusText = (status: Device['status']) => {
  switch (status) {
    case 'online': return '在线';
    case 'offline': return '离线';
    case 'warning': return '警告';
    case 'error': return '错误';
    default: return '未知';
  }
};

const getTypeText = (type: Device['type']) => {
  switch (type) {
    case 'router': return '路由器';
    case 'switch': return '交换机';
    case 'server': return '服务器';
    case 'sensor': return '传感器';
    case 'camera': return '摄像头';
    case 'gateway': return '网关';
    default: return '未知';
  }
};

// 简单图标组件
const MonitorIcon = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const ActivityIcon = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const AlertIcon = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const SettingsIcon = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

// 设备列表组件
const DeviceList: React.FC<{ onSelectDevice: (device: Device) => void }> = ({ onSelectDevice }) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    setDevices(mockDevices);
  }, []);

  const filteredDevices = devices.filter(device =>
    device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <MonitorIcon />
          设备管理
        </h2>
      </div>
      <div className="p-6">
        <div className="mb-4">
          <input
            type="text"
            placeholder="搜索设备..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="space-y-3">
          {filteredDevices.map((device) => (
            <div
              key={device.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50"
              onClick={() => onSelectDevice(device)}
            >
              <div>
                <h3 className="font-medium text-gray-900">{device.name}</h3>
                <p className="text-sm text-gray-500">{device.location}</p>
                <p className="text-xs text-gray-400">{device.ipAddress}</p>
              </div>
              <div className="text-right">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
                  {getStatusText(device.status)}
                </span>
                <p className="text-xs text-gray-500 mt-1">{getTypeText(device.type)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// 设备详情组件
const DeviceDetails: React.FC<{ device: Device }> = ({ device }) => {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">设备详情</h2>
      </div>
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">基本信息</h3>
            <dl className="space-y-2 text-sm">
              <div>
                <dt className="text-gray-500">设备名称</dt>
                <dd className="font-medium">{device.name}</dd>
              </div>
              <div>
                <dt className="text-gray-500">设备类型</dt>
                <dd className="font-medium">{getTypeText(device.type)}</dd>
              </div>
              <div>
                <dt className="text-gray-500">IP地址</dt>
                <dd className="font-medium">{device.ipAddress}</dd>
              </div>
              <div>
                <dt className="text-gray-500">固件版本</dt>
                <dd className="font-medium">{device.firmwareVersion}</dd>
              </div>
            </dl>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">状态信息</h3>
            <dl className="space-y-2 text-sm">
              <div>
                <dt className="text-gray-500">当前状态</dt>
                <dd>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
                    {getStatusText(device.status)}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">设备位置</dt>
                <dd className="font-medium">{device.location}</dd>
              </div>
              <div>
                <dt className="text-gray-500">最后在线</dt>
                <dd className="font-medium">{new Date(device.lastSeen).toLocaleString('zh-CN')}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

// 系统概览组件
const SystemOverview: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    online: 0,
    offline: 0,
    warning: 0,
    error: 0
  });

  useEffect(() => {
    setDevices(mockDevices);
    const online = mockDevices.filter(d => d.status === 'online').length;
    const offline = mockDevices.filter(d => d.status === 'offline').length;
    const warning = mockDevices.filter(d => d.status === 'warning').length;
    const error = mockDevices.filter(d => d.status === 'error').length;
    
    setStats({
      total: mockDevices.length,
      online,
      offline,
      warning,
      error
    });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">系统概览</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">总设备数</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <MonitorIcon />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">在线设备</p>
              <p className="text-2xl font-bold text-green-600">{stats.online}</p>
            </div>
            <ActivityIcon />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">离线设备</p>
              <p className="text-2xl font-bold text-red-600">{stats.offline}</p>
            </div>
            <MonitorIcon />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">警告设备</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.warning}</p>
            </div>
            <AlertIcon />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">错误设备</p>
              <p className="text-2xl font-bold text-red-600">{stats.error}</p>
            </div>
            <SettingsIcon />
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">设备类型分布</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {['router', 'switch', 'server', 'sensor', 'camera'].map(type => {
              const count = mockDevices.filter(d => d.type === type).length;
              const percentage = (count / mockDevices.length * 100).toFixed(1);
              return (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">{getTypeText(type as Device['type'])}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">{count} 台</span>
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-500 w-12 text-right">{percentage}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// 主应用组件
const HardwareManagementSystem: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  const tabs = [
    { id: 'overview', label: '系统概览', icon: MonitorIcon },
    { id: 'devices', label: '设备管理', icon: MonitorIcon },
    { id: 'monitoring', label: '监控中心', icon: ActivityIcon },
    { id: 'alerts', label: '告警管理', icon: AlertIcon },
    { id: 'config', label: '设备配置', icon: SettingsIcon }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <SystemOverview />;
      case 'devices':
        return <DeviceList onSelectDevice={setSelectedDevice} />;
      case 'monitoring':
        return selectedDevice ? (
          <DeviceDetails device={selectedDevice} />
        ) : (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center">
            <p className="text-gray-500">请先选择一个设备</p>
          </div>
        );
      case 'alerts':
        return (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center">
            <p className="text-gray-500">告警管理功能开发中...</p>
          </div>
        );
      case 'config':
        return (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center">
            <p className="text-gray-500">设备配置功能开发中...</p>
          </div>
        );
      default:
        return <SystemOverview />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <MonitorIcon />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">硬件设备管理系统</h1>
                <p className="text-sm text-gray-500">统一的设备监控与管理平台</p>
              </div>
            </div>
            
            {/* 导航选项卡 */}
            <nav className="flex space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon />
                    {tab.label}
                  </button>
                );
              })}
            </nav>

            {/* 当前选中设备信息 */}
            {selectedDevice && (
              <div className="flex items-center gap-3 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm">
                  <div className="font-medium text-blue-900">{selectedDevice.name}</div>
                  <div className="text-blue-600">{selectedDevice.ipAddress}</div>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  selectedDevice.status === 'online' ? 'bg-green-400' :
                  selectedDevice.status === 'offline' ? 'bg-red-400' :
                  selectedDevice.status === 'warning' ? 'bg-yellow-400' :
                  'bg-red-600'
                }`}></div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 主要内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>

      {/* 底部 */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              © 2024 硬件设备管理系统. 保留所有权利.
            </div>
            <div>
              版本 1.0.0
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HardwareManagementSystem;