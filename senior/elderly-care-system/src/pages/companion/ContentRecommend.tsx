import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { Newspaper, Music, Video, BookOpen, Play, Eye, Star, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ContentRecommend({ session }: { session: any }) {
  const navigate = useNavigate();
  const [contents, setContents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [currentEmotion, setCurrentEmotion] = useState<string>('neutral');

  const SUPABASE_URL = 'https://bmaarkhvsuqsnvvbtcsa.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw';

  const contentTypes = [
    { id: 'all', name: '全部', icon: BookOpen, color: 'gray' },
    { id: 'news', name: '新闻', icon: Newspaper, color: 'blue' },
    { id: 'music', name: '音乐', icon: Music, color: 'purple' },
    { id: 'video', name: '视频', icon: Video, color: 'red' },
    { id: 'literature', name: '文学', icon: BookOpen, color: 'green' }
  ];

  useEffect(() => {
    loadRecommendedContent();
  }, [selectedType]);

  const loadRecommendedContent = async () => {
    setLoading(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // 调用推荐API
      const response = await fetch(`${SUPABASE_URL}/functions/v1/content-recommend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userId: user.id,
          contentType: selectedType,
          emotionState: currentEmotion,
          limit: 20
        })
      });

      if (response.ok) {
        const result = await response.json();
        setContents(result.data.contents || []);
      }
    } catch (error) {
      console.error('加载内容失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getContentIcon = (type: string) => {
    const typeConfig = contentTypes.find(t => t.id === type);
    const Icon = typeConfig?.icon || BookOpen;
    return <Icon className="w-6 h-6" />;
  };

  const getContentColor = (type: string) => {
    const colors: Record<string, string> = {
      news: 'blue',
      music: 'purple',
      video: 'red',
      literature: 'green'
    };
    return colors[type] || 'gray';
  };

  const handleViewContent = (content: any) => {
    // 增加浏览次数
    supabase
      .from('content_library')
      .update({ view_count: (content.view_count || 0) + 1 })
      .eq('id', content.id)
      .then(() => {
        if (content.content_url) {
          window.open(content.content_url, '_blank');
        }
      });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/companion')}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-white shadow-md hover:shadow-lg transition-all"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">个性化内容推荐</h1>
              <p className="text-gray-600">为您精选优质内容</p>
            </div>
          </div>
        </div>

        {/* 类型选择 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex flex-wrap gap-3">
            {contentTypes.map((type) => {
              const Icon = type.icon;
              const isSelected = selectedType === type.id;
              return (
                <button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                    isSelected
                      ? `bg-${type.color}-600 text-white shadow-lg scale-105`
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {type.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* 内容列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl shadow-lg p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-4"></div>
                <div className="h-3 bg-gray-200 rounded mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))
          ) : contents.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500">暂无推荐内容</p>
            </div>
          ) : (
            contents.map((content) => {
              const colorClass = getContentColor(content.content_type);
              return (
                <div
                  key={content.id}
                  className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all p-6 cursor-pointer group"
                  onClick={() => handleViewContent(content)}
                >
                  {/* 内容类型标签 */}
                  <div className="flex items-center justify-between mb-4">
                    <div className={`flex items-center gap-2 px-3 py-1 bg-${colorClass}-100 text-${colorClass}-700 rounded-full text-sm font-medium`}>
                      {getContentIcon(content.content_type)}
                      <span>{contentTypes.find(t => t.id === content.content_type)?.name}</span>
                    </div>
                    <div className="flex items-center gap-1 text-yellow-500">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm font-semibold">{content.rating?.toFixed(1) || '0.0'}</span>
                    </div>
                  </div>

                  {/* 标题 */}
                  <h3 className="text-lg font-bold text-gray-800 mb-2 group-hover:text-purple-600 transition-colors line-clamp-2">
                    {content.title}
                  </h3>

                  {/* 描述 */}
                  {content.description && (
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {content.description}
                    </p>
                  )}

                  {/* AI推荐理由 */}
                  {content.recommendReason && (
                    <div className="bg-purple-50 rounded-lg p-3 mb-4">
                      <p className="text-sm text-purple-700 italic">
                        💡 {content.recommendReason}
                      </p>
                    </div>
                  )}

                  {/* 底部信息 */}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        <span>{content.view_count || 0}</span>
                      </div>
                      {content.duration_minutes && (
                        <div className="flex items-center gap-1">
                          <Play className="w-4 h-4" />
                          <span>{content.duration_minutes}分钟</span>
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {content.category}
                    </div>
                  </div>

                  {/* 标签 */}
                  {content.tags && content.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {content.tags.slice(0, 3).map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
