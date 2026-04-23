import { useMemo, useState } from 'react';
import { Link2, ArrowRight, Loader2 } from 'lucide-react';
import { authFetch } from '../lib/api';
import type { AuthUser } from '../lib/api';

interface FamilyBindingGuideProps {
  onBound: (user: AuthUser) => void;
  initialInviteCode?: string;
}

export default function FamilyBindingGuide({ onBound, initialInviteCode = '' }: FamilyBindingGuideProps) {
  const normalizedInitialInviteCode = useMemo(
    () => initialInviteCode.trim().toUpperCase().slice(0, 8),
    [initialInviteCode]
  );
  const [inviteCode, setInviteCode] = useState(normalizedInitialInviteCode);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = async () => {
    if (!inviteCode.trim() || inviteCode.length !== 8) {
      setError('请输入8位邀请码');
      return;
    }
    if (!name.trim()) {
      setError('请输入您的姓名');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const resp = await authFetch('/api/family/bindings/join', {
        method: 'POST',
        body: JSON.stringify({
          invite_code: inviteCode.trim().toUpperCase(),
          name: name.trim(),
          phone: phone.trim(),
        }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || '绑定失败，请检查邀请码是否正确');
      }

      // 绑定成功后重新获取用户信息（含 elder_id）
      const meResp = await authFetch('/api/auth/me');
      if (meResp.ok) {
        const me = await meResp.json();
        const updatedUser: AuthUser = {
          user_id: me.user_id,
          role: me.role,
          username: me.username || '',
          name: me.name,
          elder_id: me.elder_id,
        };
        localStorage.setItem('anxinbao_user', JSON.stringify(updatedUser));
        onBound(updatedUser);
      } else {
        throw new Error('绑定成功，但获取用户信息失败，请重新登录');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '绑定失败');
    } finally {
      setLoading(false);
    }
  };

  // 退出登录
  const handleLogout = () => {
    localStorage.removeItem('anxinbao_token');
    localStorage.removeItem('anxinbao_user');
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-sm">
        {/* 图标和标题 */}
        <div className="text-center mb-10">
          <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Link2 className="w-10 h-10 text-indigo-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">绑定家人</h1>
          <p className="text-gray-500 text-lg">请输入老人设备上显示的邀请码</p>
        </div>

        {/* 邀请码输入 */}
        <div className="bg-white rounded-3xl shadow-sm p-6 space-y-5">
          <div>
            <label className="block text-base font-medium text-gray-700 mb-2">邀请码（8位）</label>
            <input
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              maxLength={8}
              placeholder="例如：ABCD1234"
              className="w-full px-5 py-4 text-xl font-mono text-center border-2 border-gray-200 rounded-2xl focus:outline-none focus:border-indigo-500 tracking-widest"
            />
          </div>

          <div>
            <label className="block text-base font-medium text-gray-700 mb-2">您的姓名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="请输入您的姓名"
              className="w-full px-5 py-4 text-lg border-2 border-gray-200 rounded-2xl focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-base font-medium text-gray-700 mb-2">手机号（选填）</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="用于接收紧急通知"
              className="w-full px-5 py-4 text-lg border-2 border-gray-200 rounded-2xl focus:outline-none focus:border-indigo-500"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl px-4 py-3 text-red-600 text-base">
              {error}
            </div>
          )}

          <button
            onClick={handleJoin}
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xl font-bold rounded-2xl flex items-center justify-center gap-3 disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <>绑定家人 <ArrowRight className="w-6 h-6" /></>
            )}
          </button>
        </div>

        {/* 说明 */}
        <div className="mt-6 bg-white/60 rounded-2xl p-4">
          <p className="text-gray-500 text-sm text-center">
            💡 邀请码由老人在安心宝设备上生成，有效期7天
          </p>
        </div>

        {/* 退出登录 */}
        <button
          onClick={handleLogout}
          className="mt-6 w-full text-center text-gray-400 text-sm"
        >
          退出登录，切换账号
        </button>
      </div>
    </div>
  );
}
