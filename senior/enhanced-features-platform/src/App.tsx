import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Brain, Mic, AlertTriangle, BarChart3, Smartphone, Home } from 'lucide-react';
import SmartRecommendationEngine from './components/SmartRecommendationEngine';
import VoiceAssistantSystem from './components/VoiceAssistantSystem';
import IntelligentAlertSystem from './components/IntelligentAlertSystem';
import DataAnalyticsDashboard from './components/DataAnalyticsDashboard';
import MobileApp from './components/MobileApp';
import HomePage from './components/HomePage';

function App() {
  const [activeModule, setActiveModule] = useState('home');

  const modules = [
    { id: 'home', name: '首页', icon: Home, component: HomePage },
    { id: 'recommendation', name: '智能推荐引擎', icon: Brain, component: SmartRecommendationEngine },
    { id: 'voice', name: '语音助手系统', icon: Mic, component: VoiceAssistantSystem },
    { id: 'alert', name: '智能预警系统', icon: AlertTriangle, component: IntelligentAlertSystem },
    { id: 'dashboard', name: '数据分析仪表盘', icon: BarChart3, component: DataAnalyticsDashboard },
    { id: 'mobile', name: '移动端应用', icon: Smartphone, component: MobileApp },
  ];

  const ActiveComponent = modules.find(m => m.id === activeModule)?.component || HomePage;

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        {/* 导航栏 */}
        <nav className="bg-white shadow-lg border-b">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center">
                  <Brain className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">智能化新功能平台</span>
                </div>
              </div>
              <div className="flex space-x-4 items-center">
                {modules.map((module) => (
                  <button
                    key={module.id}
                    onClick={() => setActiveModule(module.id)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeModule === module.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <module.icon className="inline-block h-4 w-4 mr-1" />
                    {module.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </nav>

        {/* 主要内容区域 */}
        <main className="max-w-7xl mx-auto py-6 px-4">
          <ActiveComponent />
        </main>
      </div>
    </Router>
  );
}

export default App;
