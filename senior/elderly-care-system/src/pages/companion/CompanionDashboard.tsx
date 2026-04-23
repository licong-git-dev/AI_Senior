import { useNavigate } from 'react-router-dom';
import { MessageCircle, Heart, Brain, Smile, ArrowLeft, Sparkles } from 'lucide-react';

export default function CompanionDashboard({ session }: { session: any }) {
  const navigate = useNavigate();

  const modules = [
    {
      id: 'chat',
      title: 'AI智能陪伴',
      description: '温暖的对话陪伴',
      features: ['语音/文字对话', '情感识别', '心理疏导'],
      icon: MessageCircle,
      color: 'from-blue-500 to-cyan-600',
      bgColor: 'bg-blue-50',
      path: '/companion/chat'
    },
    {
      id: 'content',
      title: '个性化内容',
      description: '精选推荐内容',
      features: ['新闻资讯', '音乐视频', '文学作品'],
      icon: Heart,
      color: 'from-rose-500 to-pink-600',
      bgColor: 'bg-rose-50',
      path: '/companion/content'
    },
    {
      id: 'games',
      title: '认知训练',
      description: '趣味脑力游戏',
      features: ['记忆力训练', '注意力训练', '计算力训练'],
      icon: Brain,
      color: 'from-purple-500 to-violet-600',
      bgColor: 'bg-purple-50',
      path: '/companion/games'
    },
    {
      id: 'pet',
      title: '虚拟宠物',
      description: '数字朋友陪伴',
      features: ['宠物养成', '情感互动', '任务提醒'],
      icon: Smile,
      color: 'from-green-500 to-emerald-600',
      bgColor: 'bg-green-50',
      path: '/companion/pet'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <div className="container mx-auto px-4 py-12">
        {/* 头部 */}
        <div className="text-center mb-12">
          <button
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            返回首页
          </button>
          
          <div className="inline-flex items-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-purple-600" />
            <h1 className="text-4xl font-bold text-gray-800">情感陪伴系统</h1>
          </div>
          <p className="text-xl text-gray-600">AI驱动 · 温暖陪伴 · 快乐生活</p>
          <div className="mt-4 inline-block px-4 py-2 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
            7×24小时智能陪伴 · 情感识别与支持
          </div>
        </div>

        {/* 功能模块卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {modules.map((module) => {
            const Icon = module.icon;
            return (
              <div
                key={module.id}
                className={`${module.bgColor} rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 cursor-pointer overflow-hidden group`}
                onClick={() => navigate(module.path)}
              >
                <div className={`h-2 bg-gradient-to-r ${module.color}`}></div>
                <div className="p-8">
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`p-4 bg-gradient-to-r ${module.color} rounded-xl shadow-lg group-hover:scale-110 transition-transform`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-2xl font-bold text-gray-800 mb-2">{module.title}</h2>
                      <p className="text-gray-600">{module.description}</p>
                    </div>
                  </div>

                  <div className="space-y-3 mb-6">
                    {module.features.map((feature, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${module.color}`}></div>
                        <span className="text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <button 
                    className={`w-full py-3 bg-gradient-to-r ${module.color} text-white rounded-lg font-semibold hover:shadow-lg transition-all`}
                  >
                    进入{module.title}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* 系统亮点 */}
        <div className="mt-16 max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-center text-gray-800 mb-8">系统亮点</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">智能对话</h4>
              <p className="text-sm text-gray-600">AI理解情感，提供温暖陪伴</p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-rose-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">情感支持</h4>
              <p className="text-sm text-gray-600">心理疏导，减少孤独感</p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-violet-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">认知训练</h4>
              <p className="text-sm text-gray-600">科学游戏，保持大脑活力</p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Smile className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">虚拟宠物</h4>
              <p className="text-sm text-gray-600">数字朋友，建立情感纽带</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
