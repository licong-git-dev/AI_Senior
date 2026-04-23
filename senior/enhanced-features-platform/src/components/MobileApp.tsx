import React, { useState } from 'react';
import { Smartphone, Download, QrCode, Star, Users, Heart, Activity, Bell, MessageCircle, MapPin, Calendar } from 'lucide-react';

const MobileApp = () => {
  const [activeTab, setActiveTab] = useState('features');
  const [selectedDevice, setSelectedDevice] = useState('android');

  const appFeatures = [
    {
      icon: Heart,
      title: '健康监护',
      description: '24小时健康监测，实时数据同步，异常预警推送',
      details: ['血压心率监测', '睡眠质量分析', '用药提醒', '健康报告']
    },
    {
      icon: MessageCircle,
      title: '智能对话',
      description: 'AI语音助手，支持语音交互和文字聊天',
      details: ['语音识别', '智能回复', '情感分析', '多轮对话']
    },
    {
      icon: MapPin,
      title: '位置服务',
      description: '实时位置跟踪，紧急情况一键求助',
      details: ['实时定位', '电子围栏', '轨迹记录', '紧急求助']
    },
    {
      icon: Calendar,
      title: '日程管理',
      description: '智能日程规划，医疗预约，生活提醒',
      details: ['智能提醒', '预约管理', '活动规划', '任务跟踪']
    },
    {
      icon: Users,
      title: '家庭互动',
      description: '与家属实时沟通，情感陪伴，视频通话',
      details: ['视频通话', '照片分享', '消息推送', '互动游戏']
    },
    {
      icon: Activity,
      title: '康复指导',
      description: '个性化康复计划，运动指导，健康建议',
      details: ['康复训练', '运动指导', '营养建议', '健康教育']
    }
  ];

  const appScreens = [
    {
      name: '首页仪表盘',
      description: '显示健康状态、紧急联系人和快捷操作',
      image: '/api/placeholder/240/480'
    },
    {
      name: '健康监测',
      description: '实时健康数据展示和历史趋势分析',
      image: '/api/placeholder/240/480'
    },
    {
      name: '语音助手',
      description: '智能对话界面，支持语音和文字交互',
      image: '/api/placeholder/240/480'
    },
    {
      name: '家庭互动',
      description: '与家属沟通、视频通话和照片分享',
      image: '/api/placeholder/240/480'
    }
  ];

  const downloadStats = {
    downloads: '50,000+',
    rating: 4.8,
    reviews: '12,500+',
    updates: '每月更新'
  };

  const systemRequirements = {
    android: {
      version: 'Android 8.0+',
      storage: '100MB',
      ram: '2GB+',
      features: ['蓝牙5.0', '位置服务', '摄像头', '麦克风']
    },
    ios: {
      version: 'iOS 12.0+',
      storage: '80MB',
      ram: '2GB+',
      features: ['蓝牙5.0', '位置服务', 'Face ID/Touch ID', 'Siri集成']
    }
  };

  const TabButton = ({ id, name, active, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`px-4 py-2 mx-1 rounded-lg font-medium transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {name}
    </button>
  );

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Smartphone className="h-8 w-8 mr-3 text-indigo-600" />
            移动端应用
          </h1>
          <p className="text-gray-600 mt-2">
            基于React Native开发的跨平台移动APP，为老年人提供便捷的智能服务
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            可用下载
          </div>
        </div>
      </div>

      {/* 下载统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <Download className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{downloadStats.downloads}</div>
          <div className="text-sm text-gray-600">下载量</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <Star className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{downloadStats.rating}</div>
          <div className="text-sm text-gray-600">应用评分</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <Users className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{downloadStats.reviews}</div>
          <div className="text-sm text-gray-600">用户评价</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <Activity className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <div className="text-lg font-bold text-gray-900">{downloadStats.updates}</div>
          <div className="text-sm text-gray-600">更新频率</div>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="flex justify-center space-x-2 mb-6">
        <TabButton
          id="features"
          name="功能特色"
          active={activeTab === 'features'}
          onClick={setActiveTab}
        />
        <TabButton
          id="screenshots"
          name="界面预览"
          active={activeTab === 'screenshots'}
          onClick={setActiveTab}
        />
        <TabButton
          id="download"
          name="下载安装"
          active={activeTab === 'download'}
          onClick={setActiveTab}
        />
        <TabButton
          id="specs"
          name="系统要求"
          active={activeTab === 'specs'}
          onClick={setActiveTab}
        />
      </div>

      {/* 功能特色 */}
      {activeTab === 'features' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {appFeatures.map((feature, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center mb-4">
                <feature.icon className="h-8 w-8 text-indigo-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
              </div>
              <p className="text-gray-600 mb-4">{feature.description}</p>
              <ul className="space-y-2">
                {feature.details.map((detail, idx) => (
                  <li key={idx} className="flex items-center text-sm text-gray-700">
                    <div className="w-2 h-2 bg-indigo-600 rounded-full mr-3"></div>
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* 界面预览 */}
      {activeTab === 'screenshots' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {appScreens.map((screen, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="bg-gray-100 rounded-lg h-80 mb-4 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <Smartphone className="h-12 w-12 mx-auto mb-2" />
                  <p className="text-sm">{screen.name}</p>
                  <p className="text-xs">{screen.description}</p>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center">{screen.name}</h3>
              <p className="text-sm text-gray-600 text-center mt-1">{screen.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* 下载安装 */}
      {activeTab === 'download' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Android下载 */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mr-4">
                  <Smartphone className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Android版本</h3>
                  <p className="text-sm text-gray-600">适用于Android 8.0及以上系统</p>
                </div>
              </div>
              <div className="space-y-4">
                <button className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center">
                  <Download className="h-5 w-5 mr-2" />
                  下载APK文件
                </button>
                <button className="w-full border border-green-600 text-green-600 py-3 px-4 rounded-lg hover:bg-green-50 transition-colors flex items-center justify-center">
                  <QrCode className="h-5 w-5 mr-2" />
                  扫码下载
                </button>
                <div className="text-xs text-gray-500 space-y-1">
                  <p>• 文件大小: 100MB</p>
                  <p>• 版本: v2.1.0</p>
                  <p>• 更新日期: 2025-01-15</p>
                </div>
              </div>
            </div>

            {/* iOS下载 */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-gray-900 rounded-lg flex items-center justify-center mr-4">
                  <Smartphone className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">iOS版本</h3>
                  <p className="text-sm text-gray-600">适用于iOS 12.0及以上系统</p>
                </div>
              </div>
              <div className="space-y-4">
                <button className="w-full bg-gray-900 text-white py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors flex items-center justify-center">
                  <Download className="h-5 w-5 mr-2" />
                  App Store下载
                </button>
                <button className="w-full border border-gray-900 text-gray-900 py-3 px-4 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center">
                  <QrCode className="h-5 w-5 mr-2" />
                  扫码下载
                </button>
                <div className="text-xs text-gray-500 space-y-1">
                  <p>• 文件大小: 80MB</p>
                  <p>• 版本: v2.1.0</p>
                  <p>• 更新日期: 2025-01-15</p>
                </div>
              </div>
            </div>
          </div>

          {/* 安装指南 */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">安装指南</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Android安装步骤</h4>
                <ol className="text-sm text-gray-700 space-y-1">
                  <li>1. 点击下载APK文件</li>
                  <li>2. 允许"未知来源"应用安装</li>
                  <li>3. 打开APK文件并点击安装</li>
                  <li>4. 完成安装后打开应用</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">iOS安装步骤</h4>
                <ol className="text-sm text-gray-700 space-y-1">
                  <li>1. 点击App Store下载链接</li>
                  <li>2. 使用Apple ID登录</li>
                  <li>3. 点击"获取"按钮下载</li>
                  <li>4. 安装完成后即可使用</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 系统要求 */}
      {activeTab === 'specs' && (
        <div className="space-y-6">
          <div className="flex justify-center space-x-4 mb-6">
            <button
              onClick={() => setSelectedDevice('android')}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                selectedDevice === 'android'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Android
            </button>
            <button
              onClick={() => setSelectedDevice('ios')}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                selectedDevice === 'ios'
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              iOS
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 基本要求 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">基本要求</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">操作系统版本</span>
                  <span className="font-medium">{systemRequirements[selectedDevice].version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">存储空间</span>
                  <span className="font-medium">{systemRequirements[selectedDevice].storage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">运行内存</span>
                  <span className="font-medium">{systemRequirements[selectedDevice].ram}</span>
                </div>
              </div>
            </div>

            {/* 功能要求 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">硬件功能</h3>
              <ul className="space-y-3">
                {systemRequirements[selectedDevice].features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mr-3"></div>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 推荐设备 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">推荐设备</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Android设备</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Samsung Galaxy S10及以上</li>
                  <li>• Huawei P30及以上</li>
                  <li>• Xiaomi Mi 9及以上</li>
                  <li>• OnePlus 7及以上</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">iOS设备</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• iPhone 8及以上</li>
                  <li>• iPad (第5代)及以上</li>
                  <li>• iPad Air (第2代)及以上</li>
                  <li>• iPad Pro (所有型号)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 技术架构 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">技术架构</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div>
            <h4 className="font-medium mb-2">React Native</h4>
            <p>跨平台开发框架，一套代码支持iOS和Android双平台</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">TypeScript</h4>
            <p>类型安全的JavaScript，提升代码质量和开发效率</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">云原生架构</h4>
            <p>基于微服务的云原生架构，支持弹性扩展和高可用</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileApp;