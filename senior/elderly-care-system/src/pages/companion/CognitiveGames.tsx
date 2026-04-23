import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { Brain, Trophy, Clock, Target, Play, ArrowLeft, Award } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function CognitiveGames({ session }: { session: any }) {
  const navigate = useNavigate();
  const [games, setGames] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedGame, setSelectedGame] = useState<any>(null);

  const gameTypes = [
    { id: 'all', name: '全部', color: 'gray' },
    { id: 'memory', name: '记忆力', color: 'blue' },
    { id: 'attention', name: '注意力', color: 'green' },
    { id: 'calculation', name: '计算力', color: 'purple' }
  ];

  const difficulties = [
    { id: 'all', name: '全部难度' },
    { id: 'easy', name: '简单' },
    { id: 'medium', name: '中等' },
    { id: 'hard', name: '困难' }
  ];

  useEffect(() => {
    loadGames();
  }, [selectedType, selectedDifficulty]);

  const loadGames = async () => {
    setLoading(true);
    try {
      let query = supabase
        .from('cognitive_games')
        .select('*')
        .order('play_count', { ascending: false });

      if (selectedType !== 'all') {
        query = query.eq('game_type', selectedType);
      }

      if (selectedDifficulty !== 'all') {
        query = query.eq('difficulty_level', selectedDifficulty);
      }

      const { data, error } = await query;

      if (error) throw error;
      setGames(data || []);
    } catch (error) {
      console.error('加载游戏失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (level: string) => {
    const colors: Record<string, string> = {
      easy: 'text-green-600 bg-green-100',
      medium: 'text-yellow-600 bg-yellow-100',
      hard: 'text-red-600 bg-red-100'
    };
    return colors[level] || 'text-gray-600 bg-gray-100';
  };

  const getDifficultyText = (level: string) => {
    const texts: Record<string, string> = {
      easy: '简单',
      medium: '中等',
      hard: '困难'
    };
    return texts[level] || level;
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      memory: 'blue',
      attention: 'green',
      calculation: 'purple'
    };
    return colors[type] || 'gray';
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'memory':
        return '🧠';
      case 'attention':
        return '👁️';
      case 'calculation':
        return '🔢';
      default:
        return '🎮';
    }
  };

  const handleStartGame = async (game: any) => {
    // 增加游戏次数
    await supabase
      .from('cognitive_games')
      .update({ play_count: (game.play_count || 0) + 1 })
      .eq('id', game.id);

    setSelectedGame(game);
  };

  if (selectedGame) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-2xl w-full">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">{getTypeIcon(selectedGame.game_type)}</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-2">{selectedGame.game_name}</h2>
            <p className="text-gray-600 mb-4">{selectedGame.description}</p>
            <div className={`inline-block px-4 py-2 rounded-full text-sm font-medium ${getDifficultyColor(selectedGame.difficulty_level)}`}>
              {getDifficultyText(selectedGame.difficulty_level)}
            </div>
          </div>

          <div className="bg-gray-50 rounded-2xl p-6 mb-6">
            <h3 className="font-bold text-gray-800 mb-3">游戏说明：</h3>
            <p className="text-gray-700 leading-relaxed">{selectedGame.instructions}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <Target className="w-5 h-5" />
                <span className="font-semibold">训练领域</span>
              </div>
              <p className="text-gray-700">{selectedGame.cognitive_area}</p>
            </div>
            <div className="bg-green-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-green-600 mb-1">
                <Clock className="w-5 h-5" />
                <span className="font-semibold">推荐时长</span>
              </div>
              <p className="text-gray-700">{selectedGame.recommended_duration}分钟</p>
            </div>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => alert('游戏即将开始！（实际游戏逻辑需要进一步开发）')}
              className="w-full py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-bold text-lg hover:shadow-lg transition-all"
            >
              开始游戏
            </button>
            <button
              onClick={() => setSelectedGame(null)}
              className="w-full py-4 bg-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-300 transition-all"
            >
              返回游戏列表
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50">
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
              <h1 className="text-3xl font-bold text-gray-800">认知训练游戏</h1>
              <p className="text-gray-600">科学锻炼大脑，保持思维敏捷</p>
            </div>
          </div>
        </div>

        {/* 筛选器 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-3">游戏类型</h3>
            <div className="flex flex-wrap gap-3">
              {gameTypes.map((type) => {
                const isSelected = selectedType === type.id;
                return (
                  <button
                    key={type.id}
                    onClick={() => setSelectedType(type.id)}
                    className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                      isSelected
                        ? `bg-${type.color}-600 text-white shadow-lg scale-105`
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {getTypeIcon(type.id)} {type.name}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-600 mb-3">难度等级</h3>
            <div className="flex flex-wrap gap-3">
              {difficulties.map((diff) => {
                const isSelected = selectedDifficulty === diff.id;
                return (
                  <button
                    key={diff.id}
                    onClick={() => setSelectedDifficulty(diff.id)}
                    className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                      isSelected
                        ? 'bg-purple-600 text-white shadow-lg scale-105'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {diff.name}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 游戏列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl shadow-lg p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-4"></div>
                <div className="h-3 bg-gray-200 rounded mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))
          ) : games.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500">暂无游戏</p>
            </div>
          ) : (
            games.map((game) => {
              const colorClass = getTypeColor(game.game_type);
              return (
                <div
                  key={game.id}
                  className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all p-6 group cursor-pointer"
                  onClick={() => handleStartGame(game)}
                >
                  {/* 游戏图标和难度 */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-4xl">{getTypeIcon(game.game_type)}</div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${getDifficultyColor(game.difficulty_level)}`}>
                      {getDifficultyText(game.difficulty_level)}
                    </div>
                  </div>

                  {/* 游戏名称 */}
                  <h3 className="text-lg font-bold text-gray-800 mb-2 group-hover:text-purple-600 transition-colors">
                    {game.game_name}
                  </h3>

                  {/* 描述 */}
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {game.description}
                  </p>

                  {/* 训练领域 */}
                  <div className="bg-purple-50 rounded-lg p-3 mb-4">
                    <div className="flex items-center gap-2 text-purple-700">
                      <Target className="w-4 h-4" />
                      <span className="text-sm font-medium">{game.cognitive_area}</span>
                    </div>
                  </div>

                  {/* 底部信息 */}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>{game.recommended_duration}分钟</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Trophy className="w-4 h-4" />
                      <span>{game.play_count || 0}次</span>
                    </div>
                  </div>

                  {/* 开始按钮 */}
                  <button
                    className={`w-full mt-4 py-3 bg-gradient-to-r from-${colorClass}-500 to-${colorClass}-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all flex items-center justify-center gap-2`}
                  >
                    <Play className="w-5 h-5" />
                    开始训练
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
