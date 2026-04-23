import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, Send, Clock, User, Bot, Wifi, WifiOff } from 'lucide-react';
import { invokeVoiceAssistant } from '../lib/supabase';

const VoiceAssistantSystem = () => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: '您好！我是您的智能语音助手小云。我现在使用阿里云先进的语音识别和自然语言理解技术，可以更准确地理解您的需求。请问有什么可以帮助您的吗？',
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const recordingRef = useRef(null);

  const voiceCommands = [
    {
      command: '今天的健康报告',
      response: '您今天的血压是120/80mmHg，心率78次/分钟，整体健康状况良好。建议继续保持当前的作息和饮食习惯。',
      category: '健康查询'
    },
    {
      command: '播放轻音乐',
      response: '好的，为您播放舒缓的轻音乐。音乐有助于放松心情和缓解压力。',
      category: '娱乐服务'
    },
    {
      command: '呼叫护理人员',
      response: '正在为您联系护理人员。请稍等，专业护理人员将尽快到达您的位置。',
      category: '紧急呼叫'
    },
    {
      command: '提醒吃药',
      response: '已为您设置用药提醒。根据您的用药计划，将在今天上午10点提醒您服用降压药。',
      category: '用药提醒'
    },
    {
      command: '查看天气',
      response: '今天天气晴朗，气温18-25℃，适合户外活动。建议适当外出晒太阳，有助于维生素D的合成。',
      category: '生活信息'
    }
  ];

  useEffect(() => {
    // 测试连接到阿里云API
    testConnection();
    return () => {
      // 清理资源
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
    };
  }, []);

  const testConnection = async () => {
    try {
      setIsConnected(false);
      const data = await invokeVoiceAssistant({
        body: {
          action: 'natural_language_understanding',
          text: '连接测试',
          conversationHistory: []
        }
      });
      
      setIsConnected(true);
    } catch (error) {
      console.error('连接测试错误:', error);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleVoiceInput = async (text) => {
    setIsListening(false);
    setIsProcessing(true);
    
    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // 调用自然语言理解API
      const data = await invokeVoiceAssistant({
        body: {
          action: 'natural_language_understanding',
          text: text,
          conversationHistory: conversationHistory
        }
      });

      const botResponse = {
        id: messages.length + 2,
        type: 'bot',
        content: data.response || '抱歉，我现在无法理解您的问题，请稍后再试。',
        timestamp: new Date(),
        intent: data.intent || 'general_conversation'
      };

      setMessages(prev => [...prev, botResponse]);
      
      // 更新对话历史
      const newHistory = [...conversationHistory];
      newHistory.push({ role: 'user', content: text });
      newHistory.push({ role: 'assistant', content: botResponse.content });
      setConversationHistory(newHistory);

      // 语音合成回复
      await speakText(botResponse.content);

    } catch (error) {
      console.error('语音助手处理错误:', error);
      
      const errorMessage = {
        id: messages.length + 2,
        type: 'bot',
        content: '抱歉，语音助手服务暂时不可用。请尝试手动输入您的需求。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const speakText = async (text) => {
    if (!text) return;
    
    try {
      setIsSpeaking(true);
      
      // 调用阿里云TTS API
      const data = await invokeVoiceAssistant({
        body: {
          action: 'text_to_speech',
          text: text,
          voice: 'xiaoxiao', // 阿里云的女声，适合养老场景
          speed: 0.8 // 稍慢的语速，适合老年人
        }
      });

      if (data?.audioData) {
        // 创建音频对象并播放
        const AudioContextConstructor = window.AudioContext || (window as any).webkitAudioContext;
        const audioContext = new AudioContextConstructor();
        const audioBuffer = await audioContext.decodeAudioData(
          Uint8Array.from(atob(data.audioData), c => c.charCodeAt(0)).buffer
        );
        
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        
        source.onend = () => {
          setIsSpeaking(false);
        };
        
        source.onerror = () => {
          setIsSpeaking(false);
        };
        
        source.start();
      } else {
        // 降级到浏览器TTS
        fallbackToBrowserTTS(text);
      }

    } catch (error) {
      console.error('语音合成错误:', error);
      // 降级到浏览器TTS
      fallbackToBrowserTTS(text);
    }
  };

  const fallbackToBrowserTTS = (text) => {
    if ('speechSynthesis' in window) {
      const synth = window.speechSynthesis;
      const utterance = new SpeechSynthesisUtterance(text);
      
      // 选择中文语音
      const voices = synth.getVoices();
      const chineseVoice = voices.find(voice => 
        voice.lang.includes('zh') || voice.name.includes('Chinese')
      );
      if (chineseVoice) {
        utterance.voice = chineseVoice;
      }
      
      utterance.rate = 0.8; // 慢语速，适合老年人
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      
      synth.speak(utterance);
    } else {
      setIsSpeaking(false);
    }
  };

  const startListening = async () => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // 创建录音器
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      recorder.onstop = async () => {
        try {
          const audioBlob = new Blob(chunks, { type: 'audio/webm' });
          const arrayBuffer = await audioBlob.arrayBuffer();
          const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
          
          // 调用语音识别API
          await processSpeechInput(base64Audio);
          
          // 停止所有音频轨道
          stream.getTracks().forEach(track => track.stop());
        } catch (error) {
          console.error('语音识别处理错误:', error);
          setIsListening(false);
          setIsProcessing(false);
        }
      };
      
      recorder.onerror = (event) => {
        console.error('录音错误:', (event as any).error);
        setIsListening(false);
        setIsProcessing(false);
        stream.getTracks().forEach(track => track.stop());
      };
      
      setMediaRecorder(recorder);
      setAudioChunks([]);
      setIsListening(true);
      
      // 开始录音
      recorder.start();
      
    } catch (error) {
      console.error('无法访问麦克风:', error);
      alert('无法访问麦克风，请检查浏览器权限设置');
    }
  };

  const stopListening = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsProcessing(true);
    }
  };

  const processSpeechInput = async (audioData) => {
    try {
      setIsProcessing(true);
      
      // 调用语音识别API
      const data = await invokeVoiceAssistant({
        body: {
          action: 'speech_to_text',
          audioData: audioData
        }
      });

      if (data?.text) {
        await handleVoiceInput(data.text);
      } else {
        const errorMessage = '抱歉，没有识别到语音内容，请重试。';
        setMessages(prev => [...prev, {
          id: messages.length + 1,
          type: 'bot',
          content: errorMessage,
          timestamp: new Date()
        }]);
      }

    } catch (error) {
      console.error('语音识别错误:', error);
      
      const errorMessage = {
        id: messages.length + 1,
        type: 'bot',
        content: '语音识别服务暂时不可用，请尝试手动输入您的需求。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsListening(false);
      setIsProcessing(false);
    }
  };

  const sendMessage = () => {
    if (inputText.trim()) {
      const userMessage = {
        id: messages.length + 1,
        type: 'user',
        content: inputText,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      
      // 模拟回复
      setTimeout(() => {
        const botResponse = {
          id: messages.length + 2,
          type: 'bot',
          content: '感谢您的询问。我会尽力为您提供帮助。您也可以通过语音与我交流。',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botResponse]);
        speakText(botResponse.content);
      }, 1000);
      
      setInputText('');
    }
  };

  const quickCommands = [
    '今天的健康报告',
    '播放轻音乐',
    '呼叫护理人员',
    '提醒吃药',
    '查看天气'
  ];

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Mic className="h-8 w-8 mr-3 text-green-600" />
            语音助手系统
          </h1>
          <p className="text-gray-600 mt-2">
            智能语音交互系统，支持语音识别、自然语言理解和语音合成功能
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            isSpeaking ? 'bg-red-100 text-red-800' : 
            isProcessing ? 'bg-yellow-100 text-yellow-800' : 
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {isSpeaking ? '正在播放' : 
             isProcessing ? '正在处理' : 
             isConnected ? '已连接' : '未连接'}
          </div>
          <div className={`flex items-center ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
            {isConnected ? <Wifi className="h-5 w-5" /> : <WifiOff className="h-5 w-5" />}
            <span className="ml-1 text-sm">{isConnected ? '阿里云API已连接' : 'API连接失败'}</span>
          </div>
        </div>
      </div>

      {/* 控制面板 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">语音控制</h3>
        <div className="flex items-center justify-center space-x-6">
          <button
            onClick={isListening ? stopListening : startListening}
            className={`flex items-center justify-center w-16 h-16 rounded-full text-white transition-all ${
              isListening 
                ? 'bg-red-600 hover:bg-red-700 animate-pulse' 
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {isListening ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
          </button>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-900">
              {isProcessing ? '正在识别语音...' : 
               isListening ? '正在聆听，请说话...' : 
               isConnected ? '点击开始语音识别' : 'API连接中...'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              阿里云语音识别，准确率≥98%
            </p>
          </div>
        </div>
      </div>

      {/* 聊天界面 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <MessageCircle className="h-5 w-5 mr-2" />
            智能对话
          </h3>
        </div>
        
        {/* 消息列表 */}
        <div className="h-96 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start space-x-3 max-w-xs lg:max-w-md ${
                message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'user' ? 'bg-blue-600' : 'bg-gray-600'
                }`}>
                  {message.type === 'user' ? 
                    <User className="h-4 w-4 text-white" /> : 
                    <Bot className="h-4 w-4 text-white" />
                  }
                </div>
                <div className={`rounded-lg p-3 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 快速命令 */}
        <div className="p-4 border-t bg-gray-50">
          <p className="text-sm font-medium text-gray-700 mb-3">快速命令:</p>
          <div className="flex flex-wrap gap-2">
            {quickCommands.map((command, index) => (
              <button
                key={index}
                onClick={() => handleVoiceInput(command)}
                className="px-3 py-1 bg-white border border-gray-300 rounded-full text-sm text-gray-700 hover:bg-gray-100 transition-colors"
              >
                {command}
              </button>
            ))}
          </div>
        </div>

        {/* 输入区域 */}
        <div className="p-4 border-t">
          <div className="flex space-x-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="输入消息..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button
              onClick={sendMessage}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 语音命令列表 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">支持的语音命令</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {voiceCommands.map((cmd, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{cmd.command}</h4>
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                  {cmd.category}
                </span>
              </div>
              <p className="text-sm text-gray-600">{cmd.response}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 技术特性 */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">技术特性</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-gray-700">
          <div>
            <h4 className="font-medium mb-2">语音识别 (ASR)</h4>
            <p>阿里云ASR API，准确率≥98%，支持多种方言</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">自然语言理解 (NLU)</h4>
            <p>通义千问大模型，智能意图识别和多轮对话</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">语音合成 (TTS)</h4>
            <p>阿里云语音合成，自然流畅，支持多音色</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">降级机制</h4>
            <p>智能降级到浏览器TTS，确保服务可用性</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantSystem;