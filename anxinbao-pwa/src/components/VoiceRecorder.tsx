import { useEffect, useRef, useState } from 'react';
import { Mic, Square, Send, X, Loader2 } from 'lucide-react';
import { recordVoiceMessage } from '../lib/api';

/**
 * 老人录音组件（r28 落地 Insight #12）
 *
 * 浏览器 MediaRecorder 录音（webm/opus）→ 上传 audio_url（占位 Blob URL；
 * 真实部署应 PUT 到 OSS/S3 拿持久 URL，这里用 dataURL 让后端落档）→
 * 调 POST /api/voice-message/。
 *
 * 限制：1-60 秒（service 层亦校验）。
 *
 * 设计：
 *   - 大按钮 96px+，老人手抖也能点
 *   - 录音中显示秒数 + 止波动画
 *   - 60 秒强制停止
 *   - 上传中禁用所有按钮
 *   - 失败明确提示，不静默
 */
interface Props {
  senderUserId: number;
  recipientUserAuthId: number;
  recipientName?: string;
  onClose: () => void;
  onSent?: () => void;
}

const MAX_SECONDS = 60;
const MIN_SECONDS = 1;

export default function VoiceRecorder({
  senderUserId, recipientUserAuthId, recipientName, onClose, onSent,
}: Props) {
  const [stage, setStage] = useState<'idle' | 'recording' | 'preview' | 'uploading' | 'done'>('idle');
  const [seconds, setSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [error, setError] = useState('');
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const cleanupStream = () => {
    if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = null; }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  useEffect(() => () => cleanupStream(), []);

  const start = async () => {
    setError('');
    chunksRef.current = [];
    setSeconds(0);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const rec = new MediaRecorder(stream);
      recorderRef.current = rec;
      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setStage('preview');
        cleanupStream();
      };
      rec.start();
      setStage('recording');
      timerRef.current = window.setInterval(() => {
        setSeconds((s) => {
          const next = s + 1;
          if (next >= MAX_SECONDS) {
            try { rec.stop(); } catch (_) {}
          }
          return next;
        });
      }, 1000);
    } catch (e) {
      setError(e instanceof Error ? e.message : '无法访问麦克风，请允许权限');
      cleanupStream();
    }
  };

  const stop = () => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      try { recorderRef.current.stop(); } catch (_) {}
    }
  };

  const reset = () => {
    setStage('idle');
    setSeconds(0);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl('');
  };

  const send = async () => {
    if (seconds < MIN_SECONDS) {
      setError(`录音太短了（${seconds}s），至少 ${MIN_SECONDS} 秒`);
      return;
    }
    setStage('uploading');
    setError('');
    try {
      // 真实部署应当先 PUT 到 OSS 拿持久 url；当前 alpha 用 audio_url 字段
      // 直接传 blob URL 让后端把它视为外部存储（生产时替换为 OSS/S3）
      await recordVoiceMessage({
        sender_user_id: senderUserId,
        recipient_user_auth_id: recipientUserAuthId,
        audio_url: audioUrl, // alpha：本地 blob URL；生产换 OSS
        duration_sec: seconds,
      });
      setStage('done');
      if (onSent) onSent();
      window.setTimeout(onClose, 1500);
    } catch (e) {
      setStage('preview');
      setError(e instanceof Error ? e.message : '发送失败');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50">
      <div className="w-full max-w-md bg-white rounded-t-3xl sm:rounded-3xl p-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            给{recipientName || '家人'}录段话
          </h3>
          <button onClick={onClose} className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

        {/* 主交互区 */}
        {stage === 'idle' && (
          <div className="text-center py-8">
            <button
              onClick={start}
              className="w-32 h-32 mx-auto rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center shadow-xl active:scale-95"
            >
              <Mic className="w-14 h-14 text-white" />
            </button>
            <p className="mt-6 text-gray-600 text-lg">按一下开始说话</p>
            <p className="text-xs text-gray-400 mt-2">最长 {MAX_SECONDS} 秒</p>
          </div>
        )}

        {stage === 'recording' && (
          <div className="text-center py-8">
            <button
              onClick={stop}
              className="w-32 h-32 mx-auto rounded-full bg-red-600 flex items-center justify-center shadow-xl animate-pulse"
            >
              <Square className="w-14 h-14 text-white" />
            </button>
            <p className="mt-6 text-3xl font-bold text-red-600">{seconds}s</p>
            <p className="text-gray-500 text-sm mt-2">说完后按按钮停止</p>
          </div>
        )}

        {stage === 'preview' && (
          <div className="text-center py-4">
            <audio src={audioUrl} controls className="w-full mb-6" />
            <p className="text-gray-600 mb-6">录了 {seconds} 秒，听一下满意吗？</p>
            <div className="flex gap-3">
              <button
                onClick={reset}
                className="flex-1 py-4 rounded-2xl border-2 border-gray-200 text-gray-600 font-medium"
              >
                重新录
              </button>
              <button
                onClick={send}
                className="flex-1 py-4 rounded-2xl bg-indigo-500 hover:bg-indigo-600 text-white font-medium flex items-center justify-center gap-2"
              >
                <Send className="w-5 h-5" /> 发出去
              </button>
            </div>
          </div>
        )}

        {stage === 'uploading' && (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 mx-auto text-indigo-500 animate-spin" />
            <p className="text-gray-600 mt-4">正在发出去...</p>
          </div>
        )}

        {stage === 'done' && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✅</div>
            <p className="text-xl font-bold text-gray-800">已发给{recipientName || '家人'}</p>
            <p className="text-gray-500 text-sm mt-2">他们一打开就能听到您的声音</p>
          </div>
        )}
      </div>
    </div>
  );
}
