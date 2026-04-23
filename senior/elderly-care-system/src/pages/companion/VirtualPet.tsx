import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { Heart, Smile, Star, ArrowLeft, Gift, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function VirtualPet({ session }: { session: any }) {
  const navigate = useNavigate();
  const [pets, setPets] = useState<any[]>([]);
  const [selectedPet, setSelectedPet] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMyPets();
  }, []);

  const loadMyPets = async () => {
    setLoading(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from('virtual_pets')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setPets(data || []);
      if (data && data.length > 0) {
        setSelectedPet(data[0]);
      }
    } catch (error) {
      console.error('加载宠物失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPetEmoji = (petType: string) => {
    const emojis: Record<string, string> = {
      cat: '🐱',
      dog: '🐶',
      bird: '🐦',
      fish: '🐟',
      hamster: '🐹',
      rabbit: '🐰',
      parrot: '🦜',
      turtle: '🐢'
    };
    return emojis[petType] || '🐾';
  };

  const getMoodEmoji = (mood: string) => {
    const emojis: Record<string, string> = {
      happy: '😊',
      excited: '🤩',
      content: '😌',
      joyful: '😄',
      peaceful: '😇',
      relaxed: '😴',
      curious: '🤔',
      playful: '😜',
      chatty: '😺',
      cheerful: '🥰'
    };
    return emojis[mood] || '😊';
  };

  const getMoodText = (mood: string) => {
    const texts: Record<string, string> = {
      happy: '开心',
      excited: '兴奋',
      content: '满足',
      joyful: '快乐',
      peaceful: '平静',
      relaxed: '放松',
      curious: '好奇',
      playful: '调皮',
      chatty: '话多',
      cheerful: '愉快'
    };
    return texts[mood] || mood;
  };

  const handleInteract = async (action: string) => {
    if (!selectedPet) return;

    let message = '';
    let bonusExp = 0;

    switch (action) {
      case 'feed':
        message = `给${selectedPet.pet_name}喂食了，它吃得很开心！`;
        bonusExp = 10;
        break;
      case 'play':
        message = `和${selectedPet.pet_name}玩耍了一会，它很高兴！`;
        bonusExp = 15;
        break;
      case 'talk':
        message = `和${selectedPet.pet_name}聊天了，它很愿意倾听你说话！`;
        bonusExp = 12;
        break;
      case 'clean':
        message = `给${selectedPet.pet_name}洗澡了，它现在干干净净的！`;
        bonusExp = 8;
        break;
    }

    // 更新宠物状态
    const newExp = (selectedPet.experience_points || 0) + bonusExp;
    const newLevel = Math.floor(newExp / 100) + 1;
    const newBond = Math.min(100, (selectedPet.bond_strength || 0) + Math.floor(bonusExp / 2));

    await supabase
      .from('virtual_pets')
      .update({
        experience_points: newExp,
        growth_level: newLevel,
        bond_strength: newBond,
        last_interaction: new Date().toISOString()
      })
      .eq('id', selectedPet.id);

    alert(message + `\n\n获得经验：+${bonusExp}\n情感纽带：${newBond}/100`);
    loadMyPets();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (pets.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-8">
            <button
              onClick={() => navigate('/companion')}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-white shadow-md hover:shadow-lg transition-all"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <h1 className="text-3xl font-bold text-gray-800">我的虚拟宠物</h1>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl p-12 text-center max-w-2xl mx-auto">
            <div className="text-8xl mb-6">🐾</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">您还没有宠物</h2>
            <p className="text-gray-600 mb-8">领养一只虚拟宠物，它将成为您忠实的数字朋友！</p>
            <button
              onClick={() => alert('宠物领养功能即将开放！')}
              className="px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-bold text-lg hover:shadow-lg transition-all"
            >
              去领养宠物
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
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
              <h1 className="text-3xl font-bold text-gray-800">我的虚拟宠物</h1>
              <p className="text-gray-600">您有 {pets.length} 只数字朋友</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：宠物列表 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-bold text-gray-800 mb-4">宠物列表</h3>
              <div className="space-y-3">
                {pets.map((pet) => (
                  <button
                    key={pet.id}
                    onClick={() => setSelectedPet(pet)}
                    className={`w-full p-4 rounded-xl transition-all ${
                      selectedPet?.id === pet.id
                        ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{getPetEmoji(pet.pet_type)}</div>
                      <div className="flex-1 text-left">
                        <div className="font-semibold">{pet.pet_name}</div>
                        <div className={`text-sm ${selectedPet?.id === pet.id ? 'text-green-100' : 'text-gray-500'}`}>
                          等级 {pet.growth_level}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 右侧：宠物详情 */}
          {selectedPet && (
            <div className="lg:col-span-2">
              <div className="bg-white rounded-3xl shadow-2xl p-8">
                {/* 宠物展示 */}
                <div className="text-center mb-8">
                  <div className="text-9xl mb-4 animate-bounce">
                    {getPetEmoji(selectedPet.pet_type)}
                  </div>
                  <h2 className="text-3xl font-bold text-gray-800 mb-2">{selectedPet.pet_name}</h2>
                  <div className="flex items-center justify-center gap-2 text-xl">
                    <span>{getMoodEmoji(selectedPet.mood_state)}</span>
                    <span className="text-gray-600">心情：{getMoodText(selectedPet.mood_state)}</span>
                  </div>
                </div>

                {/* 宠物状态 */}
                <div className="grid grid-cols-2 gap-4 mb-8">
                  <div className="bg-blue-50 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-blue-600 mb-2">
                      <Star className="w-5 h-5" />
                      <span className="font-semibold">成长等级</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-800">{selectedPet.growth_level} 级</div>
                    <div className="mt-2">
                      <div className="h-2 bg-blue-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-600 transition-all"
                          style={{ width: `${((selectedPet.experience_points || 0) % 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {(selectedPet.experience_points || 0) % 100}/100 经验
                      </div>
                    </div>
                  </div>

                  <div className="bg-pink-50 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-pink-600 mb-2">
                      <Heart className="w-5 h-5" />
                      <span className="font-semibold">情感纽带</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-800">{selectedPet.bond_strength}/100</div>
                    <div className="mt-2">
                      <div className="h-2 bg-pink-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-pink-600 transition-all"
                          style={{ width: `${selectedPet.bond_strength}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {selectedPet.bond_strength >= 80 ? '深厚' : selectedPet.bond_strength >= 50 ? '友好' : '培养中'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 互动按钮 */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <button
                    onClick={() => handleInteract('feed')}
                    className="py-4 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                  >
                    🍖 喂食
                  </button>
                  <button
                    onClick={() => handleInteract('play')}
                    className="py-4 bg-gradient-to-r from-blue-500 to-cyan-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                  >
                    🎾 玩耍
                  </button>
                  <button
                    onClick={() => handleInteract('talk')}
                    className="py-4 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                  >
                    💬 聊天
                  </button>
                  <button
                    onClick={() => handleInteract('clean')}
                    className="py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                  >
                    🛁 清洁
                  </button>
                </div>

                {/* 最近互动时间 */}
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <Calendar className="w-5 h-5" />
                    <span className="text-sm">
                      最近互动：{new Date(selectedPet.last_interaction).toLocaleString('zh-CN')}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
