// API 配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ========== 认证存储 ==========
const TOKEN_KEY = 'anxinbao_token';
const USER_KEY = 'anxinbao_user';

export interface AuthUser {
  user_id: string;
  role: 'elder' | 'family' | 'admin';
  username: string;
  name?: string;
  elder_id?: number;
}

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function storeUser(user: AuthUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function isAuthenticated(): boolean {
  return !!getAuthToken() && !!getStoredUser();
}

// Auth-aware fetch helper (exported for use in page components)
export async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  // Support both relative paths and full URLs
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
  return authFetchInternal(fullUrl, options);
}

async function authFetchInternal(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
}

// ========== 认证 API ==========

export async function login(username: string, password: string): Promise<AuthUser> {
  const resp = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || '登录失败');
  }
  const tokens = await resp.json();
  setAuthToken(tokens.access_token);

  const meResp = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { 'Authorization': `Bearer ${tokens.access_token}` },
  });
  if (!meResp.ok) throw new Error('获取用户信息失败');
  const me = await meResp.json();

  const user: AuthUser = {
    user_id: me.user_id,
    role: me.role,
    username: me.username || username,
    name: me.name,
    elder_id: me.elder_id,
  };
  storeUser(user);
  return user;
}

export async function registerUser(
  username: string,
  password: string,
  role: 'elder' | 'family',
  name?: string
): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role, name }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || '注册失败');
  }
}

// ========== 类型定义 ==========

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  riskScore?: number;
  needNotify?: boolean;
  foodTherapy?: FoodTherapy[];
}

export interface FoodTherapy {
  name: string;
  ingredients: string[];
  benefits: string;
  instructions: string;
}

export interface ChatResponse {
  reply: string;
  risk_score: number;
  need_notify: boolean;
  food_therapy?: FoodTherapy[];
  session_id: string;
  risk_info: {
    risk_score: number;
    need_notify: boolean;
    category: string;
    reason: string;
  };
}

export interface HealthSummary {
  user_id: string;
  recent_symptoms: string[];
  risk_level: 'low' | 'medium' | 'high';
  last_high_risk_time?: string;
  recommendations: string[];
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  content: string;
  risk_score: number;
  category: string;
  is_read: boolean;
  is_handled: boolean;
  created_at: string;
}

// ========== 对话 API ==========

export async function sendMessage(
  message: string,
  userId: string,
  sessionId?: string
): Promise<ChatResponse> {
  const response = await authFetch(`${API_BASE_URL}/api/chat/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId, session_id: sessionId }),
  });
  if (!response.ok) throw new Error('发送消息失败');
  return response.json();
}

export async function getChatHistory(sessionId: string): Promise<ChatMessage[]> {
  const response = await authFetch(`${API_BASE_URL}/api/chat/history/${sessionId}`);
  if (!response.ok) throw new Error('获取历史记录失败');
  return response.json();
}

export async function getHealthSummary(userId: string): Promise<HealthSummary> {
  const response = await authFetch(`${API_BASE_URL}/api/chat/health-summary/${userId}`);
  if (!response.ok) throw new Error('获取健康摘要失败');
  return response.json();
}

// ========== 语音 API ==========

export async function speechToText(audioBlob: Blob, dialect: string = 'mandarin'): Promise<string> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.pcm');
  formData.append('dialect', dialect);
  const token = getAuthToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  // 注意：不设 Content-Type，让浏览器自动设置 multipart boundary
  const response = await fetch(`${API_BASE_URL}/api/voice/asr`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!response.ok) throw new Error('语音识别失败');
  const data = await response.json();
  return (data as { text?: string }).text || '';
}

export async function textToSpeech(text: string, voice: string = 'xiaoyan'): Promise<string> {
  const response = await authFetch(`${API_BASE_URL}/api/voice/tts/base64`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice, speed: 50, volume: 50 }),
  });
  if (!response.ok) throw new Error('语音合成失败');
  const data = await response.json();
  return data.audio;
}

// ========== 通知 API ==========

export async function triggerSOS(userId: string, payload: {
  description?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
} = {}): Promise<{ success: boolean; event_id: string; status: string; notified_contacts: number; message: string }> {
  const response = await authFetch(`${API_BASE_URL}/api/emergency/sos?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify({ description: payload.description ?? '紧急求助', latitude: payload.latitude, longitude: payload.longitude, address: payload.address }),
  });
  if (!response.ok) throw new Error('发送SOS失败');
  return response.json();
}

export async function getNotifications(
  familyId: string,
  unreadOnly: boolean = false
): Promise<{ notifications: Notification[]; unread_count: number }> {
  const url = new URL(`${API_BASE_URL}/api/notify/list/${familyId}`);
  if (unreadOnly) url.searchParams.set('unread_only', 'true');
  const response = await authFetch(url.toString());
  if (!response.ok) throw new Error('获取通知失败');
  return response.json();
}

export async function markNotificationRead(notificationId: string, familyId: string): Promise<void> {
  const response = await authFetch(
    `${API_BASE_URL}/api/notify/read/${notificationId}?family_id=${familyId}`,
    { method: 'PUT' }
  );
  if (!response.ok) throw new Error('标记已读失败');
}

export async function markNotificationHandled(notificationId: string, familyId: string): Promise<void> {
  const response = await authFetch(
    `${API_BASE_URL}/api/notify/handle/${notificationId}?family_id=${familyId}`,
    { method: 'PUT' }
  );
  if (!response.ok) throw new Error('标记已处理失败');
}

export interface ProactiveGreetingPreview {
  greeting: string;
  components: Record<string, string>;
  personalization_applied: string[];
  generated_at: string;
}

export async function generateProactiveGreeting(userId: string | number): Promise<ProactiveGreetingPreview> {
  const response = await authFetch(`${API_BASE_URL}/api/proactive/generate-greeting`, {
    method: 'POST',
    body: JSON.stringify({ user_id: Number(userId), context: { source: 'standby_screen' } }),
  });
  if (!response.ok) throw new Error('生成主动问候失败');
  return response.json();
}

// ========== 健康数据 API ==========

export interface HealthRecordItem {
  id: number;
  user_id: number;
  record_type: string;
  systolic?: number;
  diastolic?: number;
  heart_rate?: number;
  blood_sugar?: number;
  blood_oxygen?: number;
  temperature?: number;
  weight?: number;
  steps?: number;
  value: Record<string, number> | string;
  unit?: string;
  measured_at: string;
  notes?: string;
}

export async function createHealthRecord(
  userId: string,
  recordType: string,
  value: Record<string, number | boolean>,
  notes?: string
): Promise<void> {
  const response = await authFetch(`${API_BASE_URL}/api/health/record/create`, {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      record_type: recordType,
      value,
      source: 'manual',
      notes: notes || undefined,
    }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || '保存失败');
  }
}

export async function getHealthRecords(
  userId: string,
  recordType?: string,
  days: number = 7
): Promise<{ records: HealthRecordItem[]; total: number }> {
  const url = new URL(`${API_BASE_URL}/api/health/record/list/${userId}`);
  if (recordType) url.searchParams.set('record_type', recordType);
  url.searchParams.set('days', String(days));
  url.searchParams.set('limit', '100');
  const response = await authFetch(url.toString());
  if (!response.ok) throw new Error('获取健康记录失败');
  return response.json();
}

export async function getHealthTrend(
  userId: string,
  recordType: string,
  days: number = 7
): Promise<{ user_id: string; record_type: string; days: number; trend: Array<{ date: string; avg_value: number; count: number }> }> {
  const url = new URL(`${API_BASE_URL}/api/health/trend/${userId}/${recordType}`);
  url.searchParams.set('days', String(days));
  const response = await authFetch(url.toString());
  if (!response.ok) throw new Error('获取健康趋势失败');
  return response.json();
}

export async function getTodayMedications(userId: string) {
  const response = await authFetch(`${API_BASE_URL}/api/health/medication/today/${userId}`);
  if (!response.ok) throw new Error('获取用药计划失败');
  return response.json();
}

export async function getWeeklyHealthReport(userId: string) {
  const response = await authFetch(`${API_BASE_URL}/api/health/report/weekly/${userId}`);
  if (!response.ok) throw new Error('获取健康报告失败');
  return response.json();
}

// ========== 工具函数 ==========

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export function getWeatherInfo(): { temp: number; condition: string; icon: string } {
  const conditions = [
    { condition: '晴', icon: '☀️' },
    { condition: '多云', icon: '⛅' },
    { condition: '阴', icon: '☁️' },
  ];
  const random = conditions[Math.floor(Math.random() * conditions.length)];
  return { temp: Math.floor(Math.random() * 15) + 5, ...random };
}

export const storage = {
  get: <T>(key: string): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch { return null; }
  },
  set: <T>(key: string, value: T): void => {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch { console.error('存储失败'); }
  },
  remove: (key: string): void => { localStorage.removeItem(key); },
};

export function getUserId(): string {
  const user = getStoredUser();
  if (user?.elder_id) return String(user.elder_id);
  if (user?.user_id) return user.user_id;
  // fallback
  let userId = storage.get<string>('user_id');
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).substring(2, 10);
    storage.set('user_id', userId);
  }
  return userId;
}

export function getFamilyId(): string {
  const user = getStoredUser();
  if (user?.role === 'family') return user.user_id;
  let familyId = storage.get<string>('family_id');
  if (!familyId) {
    familyId = 'family_' + Math.random().toString(36).substring(2, 10);
    storage.set('family_id', familyId);
  }
  return familyId;
}

// ========== 家庭绑定 API ==========

export interface FamilyGroupSummary {
  id?: string;
  group_id?: string;
  group_name?: string;
  name?: string;
  elder_name: string;
  elder_id: number;
}

export function getFamilyGroupId(group: FamilyGroupSummary): string {
  const groupId = group.group_id || group.id;
  if (!groupId) throw new Error('家庭组数据缺少 group_id');
  return groupId;
}

export async function getMyFamilyGroups(): Promise<{ groups: FamilyGroupSummary[]; count: number }> {
  const response = await authFetch(`${API_BASE_URL}/api/family/groups`);
  if (!response.ok) throw new Error('获取家庭组失败');
  return response.json();
}

export async function createFamilyGroup(groupName: string, elderName: string): Promise<{ success: boolean; group: FamilyGroupSummary }> {
  const response = await authFetch(`${API_BASE_URL}/api/family/groups`, {
    method: 'POST',
    body: JSON.stringify({ group_name: groupName, elder_name: elderName }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || '创建家庭组失败');
  }
  return response.json();
}

export async function createBindingRequest(groupId: string): Promise<{ success: boolean; invite_code: string }> {
  const response = await authFetch(`${API_BASE_URL}/api/family/bindings/request`, {
    method: 'POST',
    body: JSON.stringify({ group_id: groupId, relationship: '家人', role: 'guardian', permission_level: 3 }),
  });
  if (!response.ok) throw new Error('创建邀请码失败');
  return response.json();
}

export function buildFamilyInviteLink(inviteCode: string): string {
  const url = new URL(window.location.href);
  url.searchParams.set('mode', 'child');
  url.searchParams.set('invite', inviteCode.trim().toUpperCase());
  return url.toString();
}

export async function copyText(text: string): Promise<void> {
  if (!navigator.clipboard?.writeText) {
    throw new Error('当前浏览器暂不支持复制，请手动复制');
  }

  await navigator.clipboard.writeText(text);
}

export async function shareContent(payload: ShareData): Promise<boolean> {
  if (!navigator.share) {
    return false;
  }

  await navigator.share(payload);
  return true;
}

// ========== 安心日报 API ==========

export interface SubscriptionPlan {
  plan_id: string;
  name: string;
  tier: string;
  billing_cycle: string;
  price: number;
  original_price?: number | null;
  discount_percent?: number | null;
  description: string;
  max_family_members: number;
  is_popular: boolean;
  trial_days: number;
  benefits: Array<{
    benefit_id: string;
    name: string;
    description: string;
    icon: string;
    value?: string | null;
  }>;
}

export async function getSubscriptionPlans(): Promise<{ plans: SubscriptionPlan[]; count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/subscription/plans`);
  if (!response.ok) throw new Error('获取订阅方案失败');
  return response.json();
}

export interface MySubscription {
  has_subscription: boolean;
  tier: string;
  message?: string;
  subscription?: {
    subscription_id: string;
    plan_id: string;
    tier: string;
    status: string;
    start_date: string;
    end_date: string | null;
    days_remaining: number;
    auto_renew: boolean;
    is_active: boolean;
  };
  plan?: SubscriptionPlan | null;
}

export async function getMySubscription(): Promise<MySubscription> {
  const response = await authFetch(`${API_BASE_URL}/api/subscription/my`);
  if (!response.ok) throw new Error('获取订阅状态失败');
  return response.json();
}

export async function startSubscriptionTrial(planId: string): Promise<{ success: boolean; subscription: MySubscription['subscription']; message: string }> {
  const response = await authFetch(`${API_BASE_URL}/api/subscription/trial/${planId}`, { method: 'POST' });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || '开启试用失败');
  }
  return response.json();
}

export async function subscribeToPlan(planId: string, paymentMethod: 'wechat' | 'alipay' | 'bank_card' = 'wechat'): Promise<{ success: boolean; message: string }> {
  const response = await authFetch(`${API_BASE_URL}/api/subscription/subscribe`, {
    method: 'POST',
    body: JSON.stringify({
      plan_id: planId,
      payment_method: paymentMethod,
      is_trial: false,
    }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || '开通会员失败');
  }
  return response.json();
}

export interface DailyReport {
  user_id: number;
  user_name: string;
  report_date: string;
  anxin_score: number;
  anxin_level: string;
  one_line_summary: string;
  emotion: {
    dominant_emotion: string;
    emotion_score: number;
    emotion_changes: string[];
    highlights: string[];
  };
  conversation: {
    total_conversations: number;
    total_messages: number;
    topics: string[];
    key_quotes: string[];
    first_chat_time: string | null;
    last_chat_time: string | null;
  };
  health: {
    blood_pressure: string | null;
    heart_rate: string | null;
    medication_taken: boolean;
    health_alerts: string[];
    overall_status: string;
  };
  tips_for_children: string[];
  generated_at: string;
}

export interface DailyReportHistoryItem {
  date: string;
  anxin_score: number;
  anxin_level: string;
  one_line_summary: string;
  emotion: string;
  health_status: string;
}

export interface AnxinScoreTrendPoint {
  date: string;
  score: number;
  level: string;
}

export interface DailyReportSharePayload {
  elder_id: number;
  elder_name: string;
  share_title: string;
  share_text: string;
  one_line_summary: string;
  anxin_score: number;
  anxin_level: string;
  top_tip: string;
  quote: string;
  health_status: string;
  report_date: string;
}

export interface DashboardSummaryAlert {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high';
  title: string;
  summary: string;
  action_suggestion: string;
  status: 'pending' | 'handled';
  created_at?: string | null;
}

export interface DashboardSummaryTimelineItem {
  time: string;
  type: string;
  text: string;
}

export interface DashboardSummary {
  elder: {
    id: number;
    name: string;
  };
  overview: {
    score: number;
    score_trend: number;
    status: 'stable' | 'attention' | 'alert';
    summary: string;
    health_status: string;
    emotion_status: string;
    medication_status: 'taken' | 'pending';
    generated_at: string;
  };
  alerts: DashboardSummaryAlert[];
  timeline: DashboardSummaryTimelineItem[];
  recommended_actions: string[];
  empty_state: {
    is_empty: boolean;
    reason: string | null;
  };
  report: DailyReport;
}

export async function getDashboardSummary(elderId: string | number): Promise<DashboardSummary> {
  const response = await authFetch(`${API_BASE_URL}/api/daily-report/summary/${elderId}`);
  if (!response.ok) throw new Error('获取安心中心摘要失败');
  return response.json();
}

export async function getDailyReport(elderId: string | number): Promise<DailyReport> {
  const response = await authFetch(`${API_BASE_URL}/api/daily-report/today/${elderId}`);
  if (!response.ok) throw new Error('获取日报失败');
  return response.json();
}

export async function getDailyReportSharePayload(elderId: string | number): Promise<DailyReportSharePayload> {
  const response = await authFetch(`${API_BASE_URL}/api/daily-report/share/${elderId}`);
  if (!response.ok) throw new Error('获取分享文案失败');
  return response.json();
}

export async function getDailyReportHistory(elderId: string | number, days = 7): Promise<{
  elder_id: number;
  total: number;
  reports: DailyReportHistoryItem[];
}> {
  const response = await authFetch(`${API_BASE_URL}/api/daily-report/history/${elderId}?days=${days}`);
  if (!response.ok) throw new Error('获取历史日报失败');
  return response.json();
}

export async function getAnxinScoreTrend(elderId: string | number, days = 7): Promise<{
  elder_id: number;
  trend: AnxinScoreTrendPoint[];
}> {
  const response = await authFetch(`${API_BASE_URL}/api/daily-report/anxin-score/${elderId}?days=${days}`);
  if (!response.ok) throw new Error('获取安心指数趋势失败');
  return response.json();
}

// ===================================================================
// r28 · Companion 新端点封装（onboarding / voice_message / intent）
// ===================================================================

export interface OnboardingProfile {
  family_name?: string;
  addressed_as?: string;
  closest_child_name?: string;
  favorite_tv_show?: string;
  health_focus?: string;
}

export async function updateOnboardingProfile(profile: OnboardingProfile): Promise<{
  ok: boolean;
  user_id: number;
  fields_set: Record<string, string | null>;
}> {
  const resp = await authFetch(`/api/companion/onboarding/profile`, {
    method: 'PUT',
    body: JSON.stringify(profile),
  });
  if (!resp.ok) throw new Error('保存老人个性化字段失败');
  return resp.json();
}

export async function getActivationScript(): Promise<{
  is_first_visit: boolean;
  dialect: string;
  estimated_total_seconds: number;
  lines: string[];
  full_text: string;
}> {
  const resp = await authFetch(`/api/companion/onboarding/activation`);
  if (!resp.ok) throw new Error('获取激活脚本失败');
  return resp.json();
}

export async function markOnboardingDone(): Promise<{ ok: boolean }> {
  const resp = await authFetch(`/api/companion/onboarding/mark-done`, {
    method: 'POST',
  });
  if (!resp.ok) throw new Error('标记 onboarding 完成失败');
  return resp.json();
}

// ----- Voice Message -----

export interface VoiceMessage {
  id: number;
  sender_user_id: number;
  recipient_user_auth_id: number;
  audio_url: string;
  duration_sec: number;
  transcript?: string | null;
  ai_caption?: string | null;
  emotion?: string | null;
  created_at: string;
  delivered_at?: string | null;
  read_at?: string | null;
}

export async function recordVoiceMessage(payload: {
  sender_user_id: number;
  recipient_user_auth_id: number;
  audio_url: string;
  duration_sec: number;
}): Promise<VoiceMessage> {
  const resp = await authFetch(`/api/voice-message/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error('录音入库失败');
  return resp.json();
}

export async function getVoiceInbox(unreadOnly = false, limit = 30): Promise<{
  items: VoiceMessage[];
  total: number;
}> {
  const url = `/api/voice-message/inbox?unread_only=${unreadOnly}&limit=${limit}`;
  const resp = await authFetch(url);
  if (!resp.ok) throw new Error('拉取语音收件箱失败');
  return resp.json();
}

export async function markVoiceRead(messageId: number): Promise<{ ok: boolean }> {
  const resp = await authFetch(`/api/voice-message/${messageId}/read`, {
    method: 'POST',
  });
  if (!resp.ok) throw new Error('标记语音已读失败');
  return resp.json();
}

// ----- Commercial Intent (payer-only) -----

export interface CommercialIntent {
  id: number;
  category: string;
  keyword: string;
  suggested_title?: string;
  confidence: number;
  status: string;
  detected_at: string;
  reviewed_at?: string | null;
  expires_at?: string | null;
  source_text?: string;
}

export async function listCommercialIntents(
  elderUserId: number,
  status?: string,
): Promise<{ items: CommercialIntent[] }> {
  const params = new URLSearchParams({ elder_user_id: String(elderUserId) });
  if (status) params.set('status', status);
  const resp = await authFetch(`/api/companion/intents/?${params.toString()}`);
  if (!resp.ok) throw new Error('拉取商业意图失败');
  return resp.json();
}

export async function reviewIntent(intentId: number): Promise<{ id: number; status: string }> {
  const resp = await authFetch(`/api/companion/intents/${intentId}/review`, {
    method: 'POST',
  });
  if (!resp.ok) throw new Error('标记已查看失败');
  return resp.json();
}

export async function dismissIntent(intentId: number): Promise<{ id: number; status: string }> {
  const resp = await authFetch(`/api/companion/intents/${intentId}/dismiss`, {
    method: 'POST',
  });
  if (!resp.ok) throw new Error('关闭意图失败');
  return resp.json();
}
