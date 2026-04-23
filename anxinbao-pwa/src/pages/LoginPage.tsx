import { useState } from 'react';
import { login, registerUser } from '../lib/api';
import type { AuthUser } from '../lib/api';

interface LoginPageProps {
  onLogin: (user: AuthUser) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<'elder' | 'family'>('family');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [registerSuccess, setRegisterSuccess] = useState(false);

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      setError('请输入手机号和密码');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const user = await login(username.trim(), password);
      onLogin(user);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '登录失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) {
      setError('请填写手机号和密码');
      return;
    }
    if (password.length < 6) {
      setError('密码至少需要6位');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await registerUser(username.trim(), password, role, name.trim() || undefined);
      setRegisterSuccess(true);
      // Auto switch to login
      setTimeout(() => {
        setRegisterSuccess(false);
        setTab('login');
      }, 1500);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-indigo-800 flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <div className="text-center mb-10">
        <div className="text-6xl mb-3">🏠</div>
        <h1 className="text-4xl font-bold text-white">安心宝</h1>
        <p className="text-indigo-200 text-lg mt-2">用乡音守护爸妈</p>
      </div>

      {/* Card */}
      <div className="w-full max-w-sm bg-white rounded-3xl shadow-2xl p-8">
        {/* Tab */}
        <div className="flex bg-gray-100 rounded-2xl p-1 mb-8">
          {(['login', 'register'] as const).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(''); }}
              className={`flex-1 py-3 rounded-xl text-lg font-medium transition-all ${
                tab === t ? 'bg-white shadow text-indigo-600' : 'text-gray-500'
              }`}
            >
              {t === 'login' ? '登录' : '注册'}
            </button>
          ))}
        </div>

        {registerSuccess ? (
          <div className="text-center py-8">
            <div className="text-5xl mb-4">✅</div>
            <p className="text-xl font-bold text-gray-800">注册成功！</p>
            <p className="text-gray-500 mt-2">正在跳转到登录页...</p>
          </div>
        ) : (
          <div className="space-y-5">
            {tab === 'register' && (
              <>
                <div>
                  <label className="block text-gray-600 text-base mb-2 font-medium">我是</label>
                  <div className="flex gap-3">
                    {([['family', '👨‍👩‍👧 子女家属'], ['elder', '👴 老人本人']] as const).map(([v, label]) => (
                      <button
                        key={v}
                        onClick={() => setRole(v)}
                        className={`flex-1 py-3 rounded-2xl text-base font-medium border-2 transition-all ${
                          role === v
                            ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                            : 'border-gray-200 text-gray-500'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-gray-600 text-base mb-2 font-medium">姓名（选填）</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={role === 'elder' ? '例如：李奶奶' : '例如：李明'}
                    className="w-full border-2 border-gray-200 rounded-2xl px-4 py-4 text-xl focus:border-indigo-400 focus:outline-none"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-gray-600 text-base mb-2 font-medium">手机号</label>
              <input
                type="tel"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入手机号"
                className="w-full border-2 border-gray-200 rounded-2xl px-4 py-4 text-xl focus:border-indigo-400 focus:outline-none"
                onKeyDown={(e) => e.key === 'Enter' && (tab === 'login' ? handleLogin() : handleRegister())}
              />
            </div>

            <div>
              <label className="block text-gray-600 text-base mb-2 font-medium">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={tab === 'register' ? '至少6位' : '请输入密码'}
                className="w-full border-2 border-gray-200 rounded-2xl px-4 py-4 text-xl focus:border-indigo-400 focus:outline-none"
                onKeyDown={(e) => e.key === 'Enter' && (tab === 'login' ? handleLogin() : handleRegister())}
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-2xl px-4 py-3 text-red-600 text-base">
                {error}
              </div>
            )}

            <button
              onClick={tab === 'login' ? handleLogin : handleRegister}
              disabled={loading}
              className="w-full bg-indigo-600 text-white rounded-2xl py-5 text-xl font-bold hover:bg-indigo-700 active:scale-98 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? '请稍候...' : tab === 'login' ? '登录' : '注册'}
            </button>
          </div>
        )}
      </div>

      <p className="text-indigo-300 text-sm mt-8 text-center">
        安心宝 · 让家人更安心
      </p>
    </div>
  );
}
