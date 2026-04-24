import { useState, useEffect } from 'react';
import StandbyScreen from './pages/StandbyScreen';
import ChatPage from './pages/ChatPage';
import ChildDashboard from './pages/ChildDashboard';
import VideoCallPage from './pages/VideoCallPage';
import HealthTrendsPage from './pages/HealthTrendsPage';
import NotificationsPage from './pages/NotificationsPage';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import MedicationPage from './pages/MedicationPage';
import FamilyBindingGuide from './pages/FamilyBindingGuide';
import CompanionPreview from './pages/CompanionPreview';
import { getStoredUser } from './lib/api';
import type { AuthUser } from './lib/api';
import './index.css';

type Screen = 'standby' | 'chat' | 'child' | 'video' | 'trends' | 'notifications' | 'landing' | 'medication';

interface VideoCallState {
  targetId: string;
  targetName: string;
  isIncoming: boolean;
  callId?: string;
}

function App() {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser());
  const urlParams = new URLSearchParams(window.location.search);
  const initialInviteCode = (urlParams.get('invite') || '').trim().toUpperCase().slice(0, 8);

  // 根据用户角色决定模式，未登录时回退到URL参数
  const mode = user?.role === 'family' ? 'child' : user?.role === 'elder' ? 'elder' : (() => {
    const m = urlParams.get('mode');
    if (m === 'child') return 'child';
    if (m === 'landing') return 'landing';
    return 'elder';
  })();

  const [currentScreen, setCurrentScreen] = useState<Screen>(
    mode === 'child' ? 'child' : mode === 'landing' ? 'landing' : 'standby'
  );
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [videoCallState, setVideoCallState] = useState<VideoCallState | null>(null);

  const userId = user?.elder_id ? String(user.elder_id) : user?.user_id;
  const familyId = user?.role === 'family' ? user.user_id : undefined;
  // 家属端未绑定老人
  const isFamilyUnbound = user?.role === 'family' && !user.elder_id;

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (currentScreen !== 'chat') return;

    let timeout: number;
    const resetTimeout = () => {
      clearTimeout(timeout);
      timeout = window.setTimeout(() => {
        setCurrentScreen('standby');
      }, 5 * 60 * 1000);
    };

    const events = ['mousedown', 'touchstart', 'keydown'];
    events.forEach(event => {
      window.addEventListener(event, resetTimeout);
    });

    resetTimeout();

    return () => {
      clearTimeout(timeout);
      events.forEach(event => {
        window.removeEventListener(event, resetTimeout);
      });
    };
  }, [currentScreen]);

  // 登录成功回调
  const handleLogin = (loggedInUser: AuthUser) => {
    setUser(loggedInUser);
    // 根据角色跳转到对应初始页面
    if (loggedInUser.role === 'family') {
      setCurrentScreen('child');
    } else {
      setCurrentScreen('standby');
    }
  };

  const handleLandingTryNow = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete('mode');
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
    setCurrentScreen('standby');
  };

  const handleOpenFamilyInvite = () => {
    const url = new URL(window.location.href);
    url.searchParams.set('mode', 'child');
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
    setCurrentScreen('child');
  };

  // 未登录且不在落地页时，显示登录页
  if (!user && currentScreen !== 'landing') {
    return <LoginPage onLogin={handleLogin} />;
  }

  // 发起视频通话
  const startVideoCall = (targetId: string, targetName: string) => {
    setVideoCallState({
      targetId,
      targetName,
      isIncoming: false,
    });
    setCurrentScreen('video');
  };

  // 结束视频通话
  const endVideoCall = () => {
    setVideoCallState(null);
    setCurrentScreen(mode === 'child' ? 'child' : 'chat');
  };

  if (!userId && currentScreen !== 'landing') {
    return <LoginPage onLogin={handleLogin} />;
  }

  // 视频通话页面
  if (currentScreen === 'video' && videoCallState && userId) {
    return (
      <VideoCallPage
        userId={userId}
        targetId={videoCallState.targetId}
        targetName={videoCallState.targetName}
        isIncoming={videoCallState.isIncoming}
        callId={videoCallState.callId}
        onClose={endVideoCall}
      />
    );
  }

  // Companion Alpha 预览入口：仅当 URL 含 ?mode=companion-preview 时渲染
  // 不经过正常路由、不在菜单里出现；需后端 COMPANION_ENABLED=true 才能调通
  if (urlParams.get('mode') === 'companion-preview') {
    return <CompanionPreview />;
  }

  // 子女端 - 健康趋势页面
  if (mode === 'child' && currentScreen === 'trends') {
    return (
      <div className="App min-h-screen">
        {!isOnline && (
          <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 z-50">
            <span className="text-sm font-medium">当前离线，部分功能可能受限</span>
          </div>
        )}
        <HealthTrendsPage
          userId={userId}
          onBack={() => setCurrentScreen('child')}
        />
      </div>
    );
  }

  // 子女端 - 通知中心页面
  if (mode === 'child' && currentScreen === 'notifications') {
    return (
      <div className="App min-h-screen">
        {!isOnline && (
          <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 z-50">
            <span className="text-sm font-medium">当前离线，部分功能可能受限</span>
          </div>
        )}
        <NotificationsPage
          familyId={familyId}
          onBack={() => setCurrentScreen('child')}
          onNavigate={(page) => setCurrentScreen(page === 'child' ? 'child' : page)}
          onCallParent={() => {
            if (!userId) return;
            startVideoCall(userId, '妈妈');
          }}
        />
      </div>
    );
  }

  // 营销落地页模式
  if (currentScreen === 'landing') {
    return (
      <div className="App min-h-screen bg-white">
        <LandingPage onTryNow={handleLandingTryNow} onOpenFamilyInvite={handleOpenFamilyInvite} />
      </div>
    );
  }

  // 子女端模式
  if (mode === 'child') {
    // 未绑定老人时显示引导界面
    if (isFamilyUnbound) {
      return <FamilyBindingGuide initialInviteCode={initialInviteCode} onBound={(updatedUser) => setUser(updatedUser)} />;
    }
    return (
      <div className="App min-h-screen">
        {!isOnline && (
          <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 z-50">
            <span className="text-sm font-medium">当前离线，部分功能可能受限</span>
          </div>
        )}
        <ChildDashboard
          parentUserId={userId}
          onStartVideoCall={startVideoCall}
          onNavigate={(page) => setCurrentScreen(page)}
        />
      </div>
    );
  }

  // 老人端 - 通知页面
  if (mode === 'elder' && currentScreen === 'notifications') {
    return (
      <div className="App min-h-screen">
        <NotificationsPage
          familyId={familyId}
          onBack={() => setCurrentScreen('standby')}
        />
      </div>
    );
  }

  // 老人端 - 用药提醒页面
  if (mode === 'elder' && currentScreen === 'medication') {
    return (
      <div className="App min-h-screen">
        <MedicationPage onBack={() => setCurrentScreen('standby')} />
      </div>
    );
  }

  // 老人端模式
  return (
    <div className="App min-h-screen">
      {!isOnline && (
        <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 z-50">
          <span className="text-sm font-medium">当前离线，部分功能可能受限</span>
        </div>
      )}

      {currentScreen === 'standby' ? (
        <StandbyScreen
          onWakeUp={() => setCurrentScreen('chat')}
          onNavigate={(page) => setCurrentScreen(page as Screen)}
        />
      ) : (
        <ChatPage userId={userId} />
      )}

      {currentScreen === 'chat' && (
        <button
          onClick={() => setCurrentScreen('standby')}
          className="fixed top-4 left-4 w-10 h-10 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all z-40"
        >
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default App;
