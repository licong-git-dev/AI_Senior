import { useState, useEffect, useRef, useCallback } from 'react';
import { Phone, PhoneOff, Video, VideoOff, Mic, MicOff, X } from 'lucide-react';
import { authFetch } from '../lib/api';

interface VideoCallPageProps {
  userId: string;
  targetId: string;
  targetName: string;
  isIncoming?: boolean;
  callId?: string;
  onClose: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function VideoCallPage({
  userId,
  targetId,
  targetName,
  isIncoming = false,
  callId: initialCallId,
  onClose,
}: VideoCallPageProps) {
  const [callStatus, setCallStatus] = useState<'connecting' | 'ringing' | 'connected' | 'ended'>(
    isIncoming ? 'ringing' : 'connecting'
  );
  const [callId, setCallId] = useState<string | null>(initialCallId || null);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [callDuration, setCallDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<number | null>(null);

  // 初始化WebSocket连接
  const initWebSocket = useCallback(() => {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + `/api/video/ws/${userId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data.type);

      switch (data.type) {
        case 'call_accepted':
          setCallStatus('connected');
          startCallTimer();
          break;

        case 'call_rejected':
          setError('对方拒绝了通话');
          setCallStatus('ended');
          break;

        case 'call_ended':
          setCallStatus('ended');
          break;

        case 'offer':
          await handleOffer(data);
          break;

        case 'answer':
          await handleAnswer(data);
          break;

        case 'ice_candidate':
          await handleIceCandidate(data);
          break;
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setError('连接失败');
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };

    wsRef.current = ws;
  }, [userId]);

  // 初始化媒体和WebRTC
  const initMedia = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      localStreamRef.current = stream;

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // 创建RTCPeerConnection
      const config: RTCConfiguration = {
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
        ],
      };

      const pc = new RTCPeerConnection(config);

      // 添加本地流
      stream.getTracks().forEach((track) => {
        pc.addTrack(track, stream);
      });

      // 处理远程流
      pc.ontrack = (event) => {
        if (remoteVideoRef.current && event.streams[0]) {
          remoteVideoRef.current.srcObject = event.streams[0];
        }
      };

      // 处理ICE候选
      pc.onicecandidate = (event) => {
        if (event.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'ice_candidate',
            target_id: targetId,
            call_id: callId,
            candidate: event.candidate,
          }));
        }
      };

      pc.onconnectionstatechange = () => {
        console.log('Connection state:', pc.connectionState);
        if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
          setCallStatus('ended');
        }
      };

      peerConnectionRef.current = pc;

      return pc;
    } catch (err) {
      console.error('Media error:', err);
      setError('无法访问摄像头或麦克风');
      return null;
    }
  }, [targetId, callId]);

  // 发起通话
  const initiateCall = useCallback(async () => {
    try {
      const response = await authFetch(`/api/video/call/initiate`, {
        method: 'POST',
        body: JSON.stringify({
          caller_id: userId,
          callee_id: targetId,
          caller_name: '家人',
        }),
      });

      const data = await response.json();

      if (data.success) {
        setCallId(data.call_id);
        setCallStatus('ringing');
      } else {
        setError(data.error || '呼叫失败');
        setCallStatus('ended');
      }
    } catch (err) {
      console.error('Call initiation error:', err);
      setError('网络连接失败');
      setCallStatus('ended');
    }
  }, [userId, targetId]);

  // 接听通话
  const acceptCall = useCallback(async () => {
    if (!callId) return;

    try {
      await authFetch(`/api/video/call/respond`, {
        method: 'POST',
        body: JSON.stringify({
          call_id: callId,
          action: 'accept',
        }),
      });

      setCallStatus('connected');
      startCallTimer();

      // 创建并发送SDP offer
      const pc = peerConnectionRef.current;
      if (pc) {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        wsRef.current?.send(JSON.stringify({
          type: 'offer',
          target_id: targetId,
          call_id: callId,
          sdp: offer,
        }));
      }
    } catch (err) {
      console.error('Accept call error:', err);
      setError('接听失败');
    }
  }, [callId, targetId]);

  // 拒绝通话
  const rejectCall = useCallback(async () => {
    if (!callId) return;

    try {
      await authFetch(`/api/video/call/respond`, {
        method: 'POST',
        body: JSON.stringify({
          call_id: callId,
          action: 'reject',
        }),
      });

      setCallStatus('ended');
    } catch (err) {
      console.error('Reject call error:', err);
    }
  }, [callId]);

  // 结束通话
  const endCall = useCallback(async () => {
    if (callId) {
      try {
      await authFetch(`/api/video/call/end/${callId}?user_id=${userId}`, {
        method: 'POST',
      });
      } catch (err) {
        console.error('End call error:', err);
      }
    }

    setCallStatus('ended');
  }, [callId, userId]);

  // 处理SDP Offer
  const handleOffer = async (data: { sdp: RTCSessionDescriptionInit }) => {
    const pc = peerConnectionRef.current;
    if (!pc) return;

    await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    wsRef.current?.send(JSON.stringify({
      type: 'answer',
      target_id: targetId,
      call_id: callId,
      sdp: answer,
    }));
  };

  // 处理SDP Answer
  const handleAnswer = async (data: { sdp: RTCSessionDescriptionInit }) => {
    const pc = peerConnectionRef.current;
    if (!pc) return;

    await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
  };

  // 处理ICE候选
  const handleIceCandidate = async (data: { candidate: RTCIceCandidateInit }) => {
    const pc = peerConnectionRef.current;
    if (!pc) return;

    await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
  };

  // 开始计时
  const startCallTimer = () => {
    timerRef.current = window.setInterval(() => {
      setCallDuration((prev) => prev + 1);
    }, 1000);
  };

  // 切换视频
  const toggleVideo = () => {
    const videoTrack = localStreamRef.current?.getVideoTracks()[0];
    if (videoTrack) {
      videoTrack.enabled = !videoTrack.enabled;
      setIsVideoEnabled(videoTrack.enabled);
    }
  };

  // 切换音频
  const toggleAudio = () => {
    const audioTrack = localStreamRef.current?.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.enabled = !audioTrack.enabled;
      setIsAudioEnabled(audioTrack.enabled);
    }
  };

  // 格式化通话时长
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 初始化
  useEffect(() => {
    initWebSocket();
    initMedia().then((pc) => {
      if (pc && !isIncoming) {
        initiateCall();
      }
    });

    return () => {
      // 清理
      wsRef.current?.close();
      peerConnectionRef.current?.close();
      localStreamRef.current?.getTracks().forEach((track) => track.stop());
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [initWebSocket, initMedia, initiateCall, isIncoming]);

  // 通话结束后自动关闭
  useEffect(() => {
    if (callStatus === 'ended') {
      const timer = setTimeout(onClose, 2000);
      return () => clearTimeout(timer);
    }
  }, [callStatus, onClose]);

  return (
    <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col">
      {/* 远程视频（全屏背景） */}
      <div className="absolute inset-0">
        <video
          ref={remoteVideoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
        />
        {callStatus !== 'connected' && (
          <div className="absolute inset-0 bg-gray-900 flex items-center justify-center">
            <div className="text-center text-white">
              <div className="w-24 h-24 bg-indigo-500 rounded-full flex items-center justify-center mx-auto mb-4 text-4xl">
                {targetName.charAt(0)}
              </div>
              <h2 className="text-2xl font-bold mb-2">{targetName}</h2>
              <p className="text-gray-400">
                {callStatus === 'connecting' && '正在连接...'}
                {callStatus === 'ringing' && (isIncoming ? '来电中...' : '正在呼叫...')}
                {callStatus === 'ended' && (error || '通话已结束')}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 本地视频（小窗口） */}
      <div className="absolute top-4 right-4 w-32 h-44 bg-gray-800 rounded-2xl overflow-hidden shadow-lg">
        <video
          ref={localVideoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        {!isVideoEnabled && (
          <div className="absolute inset-0 bg-gray-800 flex items-center justify-center">
            <VideoOff className="w-8 h-8 text-gray-500" />
          </div>
        )}
      </div>

      {/* 顶部状态栏 */}
      <div className="absolute top-4 left-4 right-40">
        <div className="flex items-center justify-between">
          <button
            onClick={onClose}
            className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center"
          >
            <X className="w-5 h-5 text-white" />
          </button>
          {callStatus === 'connected' && (
            <div className="bg-green-500 px-4 py-2 rounded-full">
              <span className="text-white font-medium">{formatDuration(callDuration)}</span>
            </div>
          )}
        </div>
      </div>

      {/* 底部控制栏 */}
      <div className="absolute bottom-8 left-0 right-0">
        {callStatus === 'ringing' && isIncoming ? (
          // 来电接听/拒绝按钮
          <div className="flex items-center justify-center gap-8">
            <button
              onClick={rejectCall}
              className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center shadow-lg"
            >
              <PhoneOff className="w-8 h-8 text-white" />
            </button>
            <button
              onClick={acceptCall}
              className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center shadow-lg animate-pulse"
            >
              <Phone className="w-8 h-8 text-white" />
            </button>
          </div>
        ) : callStatus === 'connected' ? (
          // 通话中控制按钮
          <div className="flex items-center justify-center gap-6">
            <button
              onClick={toggleAudio}
              className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg ${
                isAudioEnabled ? 'bg-white/20' : 'bg-red-500'
              }`}
            >
              {isAudioEnabled ? (
                <Mic className="w-6 h-6 text-white" />
              ) : (
                <MicOff className="w-6 h-6 text-white" />
              )}
            </button>
            <button
              onClick={endCall}
              className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center shadow-lg"
            >
              <PhoneOff className="w-8 h-8 text-white" />
            </button>
            <button
              onClick={toggleVideo}
              className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg ${
                isVideoEnabled ? 'bg-white/20' : 'bg-red-500'
              }`}
            >
              {isVideoEnabled ? (
                <Video className="w-6 h-6 text-white" />
              ) : (
                <VideoOff className="w-6 h-6 text-white" />
              )}
            </button>
          </div>
        ) : callStatus === 'ringing' || callStatus === 'connecting' ? (
          // 呼叫中取消按钮
          <div className="flex items-center justify-center">
            <button
              onClick={endCall}
              className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center shadow-lg"
            >
              <PhoneOff className="w-8 h-8 text-white" />
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
