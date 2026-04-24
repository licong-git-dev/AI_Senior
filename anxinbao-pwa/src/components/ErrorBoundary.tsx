/**
 * 全局错误边界
 *
 * 目的：防止任意子组件抛出的未捕获异常导致整个 PWA 白屏崩溃。
 * 老人用户对"白屏"几乎没有恢复能力（不会主动刷新、不会清缓存），
 * 一次白屏 = 一个用户失去信任。
 *
 * 行为：
 * - 捕获 React 渲染期错误
 * - 显示一个适老化的"出问题了"友好页面（大字号、明确的"重试"按钮）
 * - 在控制台打印完整堆栈，便于子女或开发者排查
 * - 不上报到第三方（避免敏感信息泄漏；日后接入 Sentry 可在此扩展）
 */
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 控制台打印（开发者/子女可用）；不向第三方上报敏感数据
    // 日后接 Sentry 在此 hook
    console.error('[ErrorBoundary] 渲染期错误:', error);
    console.error('[ErrorBoundary] 组件堆栈:', errorInfo.componentStack);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 32,
            background: 'linear-gradient(135deg, #fff7ed 0%, #fef3c7 100%)',
            color: '#1f2937',
            fontFamily: 'system-ui, sans-serif',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 80, marginBottom: 16 }}>😟</div>
          <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 12 }}>
            出了一点小问题
          </h1>
          <p style={{ fontSize: 20, color: '#4b5563', maxWidth: 480, lineHeight: 1.6 }}>
            程序遇到了点小麻烦。请按下面的按钮试试看。
            如果反复出现，请联系您的子女或客服。
          </p>

          <div style={{ display: 'flex', gap: 16, marginTop: 32, flexWrap: 'wrap', justifyContent: 'center' }}>
            <button
              onClick={this.handleRetry}
              style={{
                fontSize: 22,
                padding: '16px 40px',
                background: '#4f46e5',
                color: 'white',
                border: 'none',
                borderRadius: 16,
                cursor: 'pointer',
                fontWeight: 600,
                minWidth: 160,
              }}
            >
              重新尝试
            </button>
            <button
              onClick={this.handleHome}
              style={{
                fontSize: 22,
                padding: '16px 40px',
                background: 'white',
                color: '#4f46e5',
                border: '2px solid #4f46e5',
                borderRadius: 16,
                cursor: 'pointer',
                fontWeight: 600,
                minWidth: 160,
              }}
            >
              回到首页
            </button>
          </div>

          {/* 开发模式才展示错误细节，老人用户不暴露技术信息 */}
          {import.meta.env.DEV && this.state.error && (
            <details style={{ marginTop: 32, maxWidth: 720, textAlign: 'left' }}>
              <summary style={{ cursor: 'pointer', fontSize: 14, color: '#6b7280' }}>
                开发者诊断信息（仅 DEV 模式可见）
              </summary>
              <pre
                style={{
                  marginTop: 12,
                  padding: 16,
                  background: '#f3f4f6',
                  borderRadius: 8,
                  fontSize: 12,
                  overflow: 'auto',
                  maxHeight: 300,
                }}
              >
                {this.state.error.stack || this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
