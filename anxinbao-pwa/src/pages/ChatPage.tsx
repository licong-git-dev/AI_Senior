import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Heart, Smile, Mic, MicOff, Volume2, VolumeX, Activity } from 'lucide-react';
import { sendMessage, textToSpeech, getChatHistory, createHealthRecord, getUserId, speechToText } from '../lib/api';
import type { ChatMessage, FoodTherapy } from '../lib/api';
import { format } from 'date-fns';

/** 将后端返回的食疗 Dict 规范化为 FoodTherapy 数组 */
function normalizeFoodTherapy(raw: unknown): { items: FoodTherapy[]; dialectTip?: string } {
  if (!raw || typeof raw !== 'object') return { items: [] };
  const r = raw as Record<string, unknown>;
  // 后端返回单个对象 {name, ingredients, steps/instructions, effect/benefits, dialect_tip}
  if ('name' in r || 'steps' in r || 'effect' in r) {
    const item: FoodTherapy = {
      name: String(r.name || ''),
      ingredients: Array.isArray(r.ingredients) ? r.ingredients.map(String) : [],
      benefits: String(r.effect || r.benefits || ''),
      instructions: String(r.steps || r.instructions || ''),
    };
    return { items: [item], dialectTip: r.dialect_tip ? String(r.dialect_tip) : undefined };
  }
  // 已经是数组
  if (Array.isArray(raw)) {
    return { items: raw as FoodTherapy[] };
  }
  return { items: [] };
}

interface ChatPageProps {
  userId?: string;
}

export default function ChatPage({ userId }: ChatPageProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(() => {
    // 从 localStorage 恢复上次的会话 ID，避免刷新后丢失对话连续性
    return localStorage.getItem('anxinbao_session_id');
  });
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showFoodTherapy, setShowFoodTherapy] = useState<FoodTherapy[] | null>(null);
  const [foodTherapyDialectTip, setFoodTherapyDialectTip] = useState<string | undefined>(undefined);
  const [showHealthEntry, setShowHealthEntry] = useState(false);
  const [healthEntryType, setHealthEntryType] = useState<'blood_pressure' | 'heart_rate' | 'blood_sugar' | 'weight'>('blood_pressure');
  const [healthEntryValues, setHealthEntryValues] = useState<Record<string, string>>({});
  const [healthEntrySaving, setHealthEntrySaving] = useState(false);
  const [healthEntrySaved, setHealthEntrySaved] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [playingMessageIndex, setPlayingMessageIndex] = useState<number | null>(null);
  const [dialect, setDialect] = useState<'mandarin' | 'wuhan' | 'ezhou'>('mandarin');
  const [asrLoading, setAsrLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const effectiveUserId = userId || getUserId();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // 讯飞 ASR 录音相关 refs
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const pcmChunksRef = useRef<Int16Array[]>([]);

  // 更新时间
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 恢复历史消息（sessionId 存在时从服务器加载）
  useEffect(() => {
    if (!sessionId) return;
    getChatHistory(sessionId)
      .then((resp) => {
        // 后端返回 {session_id, history: [{role, content, timestamp}]}
        const raw = resp as unknown as { history?: Array<{ role: string; content: string; timestamp?: string }> };
        const history = raw?.history ?? (Array.isArray(resp) ? resp : []);
        if (history.length > 0) {
          setMessages(history.map((m) => ({
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
          })));
        }
      })
      .catch(() => {
        // 历史加载失败不影响新对话
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 仅在组件挂载时执行一次

  // 初始化音频元素
  useEffect(() => {
    const audio = new Audio();
    audio.onended = () => {
      setIsPlayingAudio(false);
      setPlayingMessageIndex(null);
    };
    audio.onerror = () => {
      setIsPlayingAudio(false);
      setPlayingMessageIndex(null);
    };
    audioRef.current = audio;
    return () => {
      audio.pause();
      audio.src = '';
    };
  }, []);

  // 播放TTS语音
  const playTTS = useCallback(async (text: string, messageIndex: number) => {
    if (!audioRef.current) return;
    // 停止当前播放
    audioRef.current.pause();
    audioRef.current.src = '';

    try {
      setIsPlayingAudio(true);
      setPlayingMessageIndex(messageIndex);
      const audioBase64 = await textToSpeech(text);
      if (audioRef.current) {
        audioRef.current.src = `data:audio/wav;base64,${audioBase64}`;
        await audioRef.current.play();
      }
    } catch {
      console.error('TTS播放失败，已回退到文字显示');
      setIsPlayingAudio(false);
      setPlayingMessageIndex(null);
    }
  }, []);

  // 停止播放
  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    setIsPlayingAudio(false);
    setPlayingMessageIndex(null);
  }, []);

  // 将 Float32 采样转换为 Int16 PCM
  const float32ToInt16 = (float32: Float32Array): Int16Array => {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
  };

  // 线性降采样（当 AudioContext 不支持 16000Hz 时使用）
  const resampleTo16k = (samples: Int16Array, fromRate: number): Int16Array => {
    if (fromRate === 16000) return samples;
    const ratio = fromRate / 16000;
    const outLen = Math.floor(samples.length / ratio);
    const out = new Int16Array(outLen);
    for (let i = 0; i < outLen; i++) {
      out[i] = samples[Math.floor(i * ratio)];
    }
    return out;
  };

  // 停止录音并上传识别
  const stopAndRecognize = useCallback(async () => {
    processorRef.current?.disconnect();
    streamRef.current?.getTracks().forEach(t => t.stop());
    const actualRate = audioCtxRef.current?.sampleRate ?? 16000;
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
    processorRef.current = null;
    streamRef.current = null;
    setIsRecording(false);

    const chunks = pcmChunksRef.current;
    pcmChunksRef.current = [];
    if (chunks.length === 0) return;

    // 合并所有 PCM 块
    const totalLen = chunks.reduce((acc, c) => acc + c.length, 0);
    const combined = new Int16Array(totalLen);
    let offset = 0;
    for (const c of chunks) { combined.set(c, offset); offset += c.length; }

    // 降采样到 16k（若需要）
    const pcm16k = resampleTo16k(combined, actualRate);
    const blob = new Blob([pcm16k.buffer as ArrayBuffer], { type: 'audio/pcm' });

    setAsrLoading(true);
    try {
      const text = await speechToText(blob, dialect);
      if (text) setInputText(text);
    } catch {
      console.error('讯飞 ASR 识别失败');
    } finally {
      setAsrLoading(false);
    }
  }, [dialect]);

  // 开始/停止录音
  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      await stopAndRecognize();
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      alert('您的浏览器不支持麦克风录音');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      pcmChunksRef.current = [];

      // 尝试以 16000Hz 创建 AudioContext，不支持则使用默认采样率（stopAndRecognize 会降采样）
      let audioCtx: AudioContext;
      try {
        audioCtx = new AudioContext({ sampleRate: 16000 });
      } catch {
        audioCtx = new AudioContext();
      }
      audioCtxRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      // eslint-disable-next-line @typescript-eslint/no-deprecated
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e: AudioProcessingEvent) => {
        const float32 = e.inputBuffer.getChannelData(0);
        pcmChunksRef.current.push(float32ToInt16(float32));
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
      setIsRecording(true);
      setInputText('');
    } catch {
      alert('无法访问麦克风，请检查权限设置');
    }
  }, [isRecording, stopAndRecognize]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputText.trim() || loading) return;

    const userMessage = inputText.trim();
    setInputText('');
    setLoading(true);
    stopAudio(); // 发送新消息时停止当前播放

    // 立即显示用户消息
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    }]);

    try {
      setError(null);
      const response = await sendMessage(userMessage, effectiveUserId, sessionId || undefined);

      if (!sessionId) {
        setSessionId(response.session_id);
        localStorage.setItem('anxinbao_session_id', response.session_id);
      }

      // 显示AI回复
      const newMessageIndex = messages.length + 1; // +1 for the user message we just added
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.reply,
        timestamp: new Date(),
        riskScore: response.risk_score,
        needNotify: response.need_notify,
        foodTherapy: response.food_therapy,
      }]);

      // 如果有食疗建议，显示
      if (response.food_therapy) {
        const { items, dialectTip } = normalizeFoodTherapy(response.food_therapy);
        if (items.length > 0) {
          setShowFoodTherapy(items);
          setFoodTherapyDialectTip(dialectTip);
        }
      }

      // TTS自动播放AI回复
      if (ttsEnabled) {
        playTTS(response.reply, newMessageIndex);
      }
    } catch (error) {
      console.error('发送失败:', error);
      setError('消息发送失败，请检查网络后重试。');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '当前暂时无法连接安心宝服务，请稍后重试。',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  // 按键处理
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 快捷回复
  const quickReplies = [
    '今天身体怎么样',
    '有点头疼',
    '睡眠不太好',
    '给我讲个笑话',
    '推荐点好吃的',
  ];

  // 问候语
  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 6) return '夜深了，注意休息哦';
    if (hour < 12) return '早上好，今天感觉怎么样？';
    if (hour < 14) return '中午好，吃饭了吗？';
    if (hour < 18) return '下午好，记得活动一下';
    return '晚上好，今天过得开心吗？';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100">
      {/* 顶部状态栏 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-4 rounded-b-3xl shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center animate-pulse-ring">
              <Heart className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">安心宝</h1>
              <p className="text-indigo-200 text-sm">您的健康小助手</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => { setShowHealthEntry(true); setHealthEntrySaved(false); setHealthEntryValues({}); }}
              className="w-10 h-10 rounded-full flex items-center justify-center transition-colors bg-white/20 text-white"
              title="记录健康数据"
            >
              <Activity className="w-5 h-5" />
            </button>
            <button
              onClick={() => { setTtsEnabled(prev => !prev); if (isPlayingAudio) stopAudio(); }}
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                ttsEnabled ? 'bg-white/20 text-white' : 'bg-white/10 text-white/50'
              }`}
              title={ttsEnabled ? '关闭语音播报' : '开启语音播报'}
            >
              {ttsEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            </button>
            <div className="text-right">
            <p className="text-3xl font-bold">{format(currentTime, 'HH:mm')}</p>
            <p className="text-indigo-200 text-sm">{format(currentTime, 'MM月dd日 EEEE')}</p>
          </div>
          </div>
        </div>
        <p className="text-lg text-indigo-100">{getGreeting()}</p>
      </div>

      {/* 聊天区域 */}
      <div className="flex flex-col" style={{ height: 'calc(100vh - 200px)' }}>
        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              {error && (
                <div className="mx-auto mb-4 max-w-sm rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
                  {error}
                </div>
              )}
              <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Smile className="w-10 h-10 text-indigo-600" />
              </div>
              <p className="text-gray-500 text-lg mb-2">您好！我是安心宝</p>
              <p className="text-gray-400">有什么想聊的，尽管告诉我</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
            >
              <div
                className={`max-w-[85%] rounded-3xl px-6 py-4 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
                    : 'bg-white text-gray-800'
                }`}
              >
                <p className="text-lg leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                {msg.role === 'assistant' && (
                  <button
                    onClick={() => playingMessageIndex === index && isPlayingAudio ? stopAudio() : playTTS(msg.content, index)}
                    className="mt-2 flex items-center gap-1 text-sm opacity-60 hover:opacity-100 transition-opacity"
                  >
                    {playingMessageIndex === index && isPlayingAudio ? (
                      <><VolumeX className="w-4 h-4" /><span>停止播放</span></>
                    ) : (
                      <><Volume2 className="w-4 h-4" /><span>播放语音</span></>
                    )}
                  </button>
                )}
                {msg.riskScore !== undefined && msg.riskScore >= 5 && (
                  <div className="mt-2 flex items-center gap-2 text-sm opacity-80">
                    <Heart className="w-4 h-4" />
                    <span>健康关注度: {msg.riskScore}/10</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-3xl px-6 py-4 shadow-sm">
                <div className="flex gap-2">
                  <div className="w-3 h-3 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-3 h-3 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-3 h-3 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 快捷回复 */}
        {messages.length === 0 && (
          <div className="px-4 py-3">
            <p className="text-sm text-gray-500 mb-2">试试这些话题：</p>
            <div className="flex flex-wrap gap-2">
              {quickReplies.map((reply, index) => (
                <button
                  key={index}
                  onClick={() => setInputText(reply)}
                  className="px-4 py-2 bg-white text-indigo-600 rounded-full text-sm shadow-sm hover:shadow-md transition-all active:scale-95"
                >
                  {reply}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 输入区域 */}
        <div className="p-4 bg-white/80 backdrop-blur-sm">
          {/* 方言选择器（仅在未录音时显示） */}
          {!isRecording && !asrLoading && (
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs text-gray-400">方言：</span>
              {([
                { key: 'mandarin', label: '普通话' },
                { key: 'wuhan', label: '武汉话' },
                { key: 'ezhou', label: '鄂州话' },
              ] as const).map((item) => (
                <button
                  key={item.key}
                  onClick={() => setDialect(item.key)}
                  className={`px-3 py-1 rounded-full text-xs transition-all ${
                    dialect === item.key
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-3 items-center">
            {/* 语音输入按钮 */}
            <button
              onClick={toggleRecording}
              disabled={loading || asrLoading}
              className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 ${
                isRecording
                  ? 'bg-red-500 animate-pulse'
                  : asrLoading
                  ? 'bg-yellow-400'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {asrLoading ? (
                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" />
              ) : isRecording ? (
                <MicOff className="w-6 h-6 text-white" />
              ) : (
                <Mic className="w-6 h-6 text-gray-600" />
              )}
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={asrLoading ? '识别中...' : isRecording ? `正在录音（${dialect === 'mandarin' ? '普通话' : dialect === 'wuhan' ? '武汉话' : '鄂州话'}）...` : '想说什么就说什么...'}
              className={`flex-1 px-6 py-4 text-lg border-2 rounded-full focus:outline-none transition-colors ${
                isRecording
                  ? 'border-red-300 bg-red-50'
                  : asrLoading
                  ? 'border-yellow-300 bg-yellow-50'
                  : 'border-gray-200 focus:border-indigo-500'
              }`}
              disabled={loading || isRecording || asrLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={loading || !inputText.trim()}
              className="w-14 h-14 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-6 h-6 text-white" />
            </button>
          </div>
          {isRecording && (
            <p className="text-center text-red-500 text-sm mt-2 animate-pulse">
              🎤 正在录音，说完后再次点击麦克风上传识别...
            </p>
          )}
          {asrLoading && (
            <p className="text-center text-yellow-600 text-sm mt-2">
              ⏳ 讯飞方言识别中，请稍候...
            </p>
          )}
        </div>
      </div>

      {/* 食疗建议弹窗 */}
      {showFoodTherapy && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span>🍲</span> 食疗推荐
            </h3>
            {foodTherapyDialectTip && (
              <div className="mb-4 p-3 bg-yellow-50 rounded-2xl text-sm text-yellow-800">
                💬 {foodTherapyDialectTip}
              </div>
            )}
            {showFoodTherapy.map((food, index) => (
              <div key={index} className="mb-4 p-4 bg-orange-50 rounded-2xl">
                <h4 className="font-bold text-orange-800 mb-2">{food.name}</h4>
                <p className="text-sm text-orange-700 mb-2">
                  <strong>食材：</strong>{food.ingredients.join('、')}
                </p>
                <p className="text-sm text-orange-700 mb-2">
                  <strong>功效：</strong>{food.benefits}
                </p>
                <p className="text-sm text-orange-600">
                  <strong>做法：</strong>{food.instructions}
                </p>
              </div>
            ))}
            <button
              onClick={() => setShowFoodTherapy(null)}
              className="w-full py-3 bg-gradient-to-r from-orange-400 to-orange-500 text-white rounded-full font-bold"
            >
              知道了
            </button>
          </div>
        </div>
      )}

      {/* 健康数据录入弹窗 */}
      {showHealthEntry && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Activity className="w-6 h-6 text-indigo-600" /> 记录健康数据
            </h3>

            {/* 类型切换 */}
            <div className="grid grid-cols-4 gap-1 mb-5 bg-gray-100 rounded-2xl p-1">
              {([
                { key: 'blood_pressure', label: '血压' },
                { key: 'heart_rate', label: '心率' },
                { key: 'blood_sugar', label: '血糖' },
                { key: 'weight', label: '体重' },
              ] as const).map((item) => (
                <button
                  key={item.key}
                  onClick={() => { setHealthEntryType(item.key); setHealthEntryValues({}); setHealthEntrySaved(false); }}
                  className={`py-2 rounded-xl text-xs font-medium transition-all ${
                    healthEntryType === item.key ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* 输入字段 */}
            {healthEntryType === 'blood_pressure' && (
              <div className="space-y-3 mb-5">
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-xs text-gray-500 mb-1 block">收缩压（高压）</label>
                    <input type="number" placeholder="120" className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl text-lg focus:border-indigo-400 focus:outline-none"
                      value={healthEntryValues.systolic || ''}
                      onChange={(e) => setHealthEntryValues(v => ({ ...v, systolic: e.target.value }))} />
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-gray-500 mb-1 block">舒张压（低压）</label>
                    <input type="number" placeholder="80" className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl text-lg focus:border-indigo-400 focus:outline-none"
                      value={healthEntryValues.diastolic || ''}
                      onChange={(e) => setHealthEntryValues(v => ({ ...v, diastolic: e.target.value }))} />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">脉搏（可选）</label>
                  <input type="number" placeholder="70" className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl text-lg focus:border-indigo-400 focus:outline-none"
                    value={healthEntryValues.pulse || ''}
                    onChange={(e) => setHealthEntryValues(v => ({ ...v, pulse: e.target.value }))} />
                </div>
                <p className="text-xs text-gray-400">单位：mmHg</p>
              </div>
            )}
            {healthEntryType === 'heart_rate' && (
              <div className="mb-5">
                <label className="text-xs text-gray-500 mb-1 block">心率</label>
                <input type="number" placeholder="75" className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl text-2xl text-center focus:border-indigo-400 focus:outline-none"
                  value={healthEntryValues.bpm || ''}
                  onChange={(e) => setHealthEntryValues({ bpm: e.target.value })} />
                <p className="text-xs text-gray-400 mt-1">单位：次/分钟，正常范围 60-100</p>
              </div>
            )}
            {healthEntryType === 'blood_sugar' && (
              <div className="mb-5">
                <label className="text-xs text-gray-500 mb-1 block">血糖值</label>
                <input type="number" step="0.1" placeholder="5.5" className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl text-2xl text-center focus:border-indigo-400 focus:outline-none"
                  value={healthEntryValues.value || ''}
                  onChange={(e) => setHealthEntryValues({ value: e.target.value })} />
                <p className="text-xs text-gray-400 mt-1">单位：mmol/L，空腹正常范围 3.9-6.1</p>
              </div>
            )}
            {healthEntryType === 'weight' && (
              <div className="mb-5">
                <label className="text-xs text-gray-500 mb-1 block">体重</label>
                <input type="number" step="0.1" placeholder="65.0" className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl text-2xl text-center focus:border-indigo-400 focus:outline-none"
                  value={healthEntryValues.kg || ''}
                  onChange={(e) => setHealthEntryValues({ kg: e.target.value })} />
                <p className="text-xs text-gray-400 mt-1">单位：kg</p>
              </div>
            )}

            {healthEntrySaved && (
              <div className="bg-green-50 rounded-2xl p-3 mb-4 text-center">
                <p className="text-green-700 font-medium">✅ 已保存成功！</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setShowHealthEntry(false)}
                className="flex-1 py-3 bg-gray-100 rounded-2xl text-gray-700 font-medium"
              >
                关闭
              </button>
              <button
                disabled={healthEntrySaving}
                onClick={async () => {
                  setHealthEntrySaving(true);
                  try {
                    let value: Record<string, number> = {};
                    if (healthEntryType === 'blood_pressure') {
                      if (!healthEntryValues.systolic || !healthEntryValues.diastolic) {
                        alert('请输入收缩压和舒张压');
                        setHealthEntrySaving(false);
                        return;
                      }
                      value = {
                        systolic: Number(healthEntryValues.systolic),
                        diastolic: Number(healthEntryValues.diastolic),
                        ...(healthEntryValues.pulse ? { pulse: Number(healthEntryValues.pulse) } : {}),
                      };
                    } else if (healthEntryType === 'heart_rate') {
                      if (!healthEntryValues.bpm) { alert('请输入心率'); setHealthEntrySaving(false); return; }
                      value = { bpm: Number(healthEntryValues.bpm) };
                    } else if (healthEntryType === 'blood_sugar') {
                      if (!healthEntryValues.value) { alert('请输入血糖值'); setHealthEntrySaving(false); return; }
                      value = { value: Number(healthEntryValues.value) };
                    } else if (healthEntryType === 'weight') {
                      if (!healthEntryValues.kg) { alert('请输入体重'); setHealthEntrySaving(false); return; }
                      value = { kg: Number(healthEntryValues.kg) };
                    }
                    await createHealthRecord(effectiveUserId, healthEntryType, value);
                    setHealthEntrySaved(true);
                    setHealthEntryValues({});
                  } catch (err) {
                    alert(err instanceof Error ? err.message : '保存失败');
                  } finally {
                    setHealthEntrySaving(false);
                  }
                }}
                className="flex-1 py-3 bg-indigo-600 rounded-2xl text-white font-bold disabled:opacity-50"
              >
                {healthEntrySaving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
