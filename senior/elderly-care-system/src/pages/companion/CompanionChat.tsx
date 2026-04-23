import { useState, useEffect, useRef } from 'react';
import { supabase } from '../../lib/supabase';
import { MessageCircle, Send, Mic, MicOff, Volume2, Heart, Smile, Meh, Frown } from 'lucide-react';

export default function CompanionChat({ session }: { session: any }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState('neutral');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const SUPABASE_URL = 'https://bmaarkhvsuqsnvvbtcsa.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw';

  useEffect(() => {
    loadRecentMessages();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadRecentMessages = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data } = await supabase
        .from('voice_interactions')
        .select('*')
        .eq('user_id', user.id)
        .order('interaction_time', { ascending: false })
        .limit(10);

      if (data) {
        const formattedMessages = data.reverse().flatMap((msg: any) => [
          { role: 'user', content: msg.user_input, timestamp: msg.interaction_time },
          { role: 'assistant', content: msg.ai_response, timestamp: msg.interaction_time, emotion: msg.emotion_detected }
        ]);
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('加载历史消息失败:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() || loading) return;

    const userMessage = inputText;
    setInputText('');
    setLoading(true);

    // 立即显示用户消息
    setMessages(prev => [...prev, { role: 'user', content: userMessage, timestamp: new Date() }]);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('未登录');
      }

      // 调用Edge Function
      const response = await fetch(`${SUPABASE_URL}/functions/v1/companion-chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userInput: userMessage,
          userId: user.id,
          emotionState: currentEmotion,
          conversationContext: messages.slice(-10).map(m => ({
            [m.role === 'user' ? 'user' : 'assistant']: m.content
          }))
        })
      });

      if (!response.ok) {
        throw new Error('AI响应失败');
      }

      const result = await response.json();
      const aiReply = result.data.reply;
      const detectedEmotion = result.data.emotionDetected;

      // 显示AI回复
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: aiReply, 
        timestamp: new Date(),
        emotion: detectedEmotion 
      }]);

      setCurrentEmotion(detectedEmotion);

    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，我现在有点不舒服，稍后再聊好吗？', 
        timestamp: new Date() 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getEmotionIcon = (emotion: string) => {
    switch (emotion) {
      case 'happy':
        return <Smile className="w-5 h-5 text-yellow-500" />;
      case 'sad':
        return <Frown className="w-5 h-5 text-blue-500" />;
      case 'anxious':
        return <Meh className="w-5 h-5 text-orange-500" />;
      default:
        return <Heart className="w-5 h-5 text-gray-400" />;
    }
  };

  const quickReplies = [
    '今天天气怎么样',
    '我有点想孩子了',
    '给我讲个故事吧',
    '我感觉有点累',
    '推荐一些音乐'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50">
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {/* 头部 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-full flex items-center justify-center">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">AI智能陪伴</h1>
                <p className="text-sm text-gray-600">我在这里陪您聊天</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">当前情绪</span>
              {getEmotionIcon(currentEmotion)}
            </div>
          </div>
        </div>

        {/* 聊天区域 */}
        <div className="bg-white rounded-2xl shadow-lg mb-6 flex flex-col" style={{ height: 'calc(100vh - 300px)' }}>
          {/* 消息列表 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="w-8 h-8 text-blue-600" />
                </div>
                <p className="text-gray-500">开始和我聊天吧，我会一直陪着您</p>
              </div>
            )}

            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[70%] ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'} rounded-2xl px-6 py-4`}>
                  <div className="flex items-start gap-2">
                    {msg.emotion && msg.role === 'assistant' && (
                      <div className="mt-1">{getEmotionIcon(msg.emotion)}</div>
                    )}
                    <p className="text-lg leading-relaxed">{msg.content}</p>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl px-6 py-4">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* 快捷回复 */}
          {messages.length === 0 && (
            <div className="px-6 py-3 border-t border-gray-200">
              <p className="text-sm text-gray-500 mb-2">试试这些话题：</p>
              <div className="flex flex-wrap gap-2">
                {quickReplies.map((reply, index) => (
                  <button
                    key={index}
                    onClick={() => setInputText(reply)}
                    className="px-4 py-2 bg-blue-50 text-blue-600 rounded-full text-sm hover:bg-blue-100 transition-colors"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 输入区域 */}
          <div className="p-6 border-t border-gray-200">
            <div className="flex gap-3">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您想说的话..."
                className="flex-1 px-6 py-4 text-lg border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <button
                onClick={() => setListening(!listening)}
                className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
                  listening ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-200 hover:bg-gray-300'
                }`}
                title="语音输入"
              >
                {listening ? (
                  <MicOff className="w-6 h-6 text-white" />
                ) : (
                  <Mic className="w-6 h-6 text-gray-600" />
                )}
              </button>
              <button
                onClick={handleSendMessage}
                disabled={loading || !inputText.trim()}
                className="w-14 h-14 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-full flex items-center justify-center hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-6 h-6 text-white" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
