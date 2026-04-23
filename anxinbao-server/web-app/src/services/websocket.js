/**
 * WebSocket 客户端服务
 * 用于实时消息推送和通知
 */

class WebSocketService {
  constructor() {
    this.ws = null
    this.url = ''
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.heartbeatInterval = 30000
    this.heartbeatTimer = null
    this.reconnectTimer = null
    this.listeners = new Map()
    this.isConnected = false
    this.token = ''
  }

  /**
   * 连接WebSocket服务器
   * @param {string} url - WebSocket服务器地址
   * @param {string} token - 认证令牌
   */
  connect(url, token) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected')
      return
    }

    this.url = url
    this.token = token

    try {
      // 将token作为查询参数传递
      const wsUrl = `${url}?token=${encodeURIComponent(token)}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
    } catch (error) {
      console.error('WebSocket connection error:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * 连接成功处理
   */
  handleOpen() {
    console.log('WebSocket connected')
    this.isConnected = true
    this.reconnectAttempts = 0
    this.startHeartbeat()
    this.emit('connected', null)
  }

  /**
   * 消息处理
   * @param {MessageEvent} event - WebSocket消息事件
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data)

      // 处理心跳响应
      if (data.type === 'pong') {
        return
      }

      // 分发消息到对应监听器
      this.emit(data.type, data.payload)

      // 通用消息事件
      this.emit('message', data)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  /**
   * 错误处理
   * @param {Event} error - 错误事件
   */
  handleError(error) {
    console.error('WebSocket error:', error)
    this.emit('error', error)
  }

  /**
   * 连接关闭处理
   * @param {CloseEvent} event - 关闭事件
   */
  handleClose(event) {
    console.log('WebSocket closed:', event.code, event.reason)
    this.isConnected = false
    this.stopHeartbeat()
    this.emit('disconnected', { code: event.code, reason: event.reason })

    // 非正常关闭时尝试重连
    if (event.code !== 1000) {
      this.scheduleReconnect()
    }
  }

  /**
   * 发送消息
   * @param {string} type - 消息类型
   * @param {any} payload - 消息内容
   */
  send(type, payload) {
    if (!this.isConnected) {
      console.warn('WebSocket is not connected')
      return false
    }

    try {
      const message = JSON.stringify({ type, payload, timestamp: Date.now() })
      this.ws.send(message)
      return true
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
      return false
    }
  }

  /**
   * 启动心跳
   */
  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send('ping', { timestamp: Date.now() })
      }
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 计划重连
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      this.emit('maxReconnectAttempts', null)
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectAttempts++
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1) // 指数退避

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect(this.url, this.token)
    }, delay)

    this.emit('reconnecting', { attempt: this.reconnectAttempts, delay })
  }

  /**
   * 添加事件监听器
   * @param {string} event - 事件类型
   * @param {Function} callback - 回调函数
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  /**
   * 移除事件监听器
   * @param {string} event - 事件类型
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    if (!this.listeners.has(event)) return

    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件类型
   * @param {any} data - 事件数据
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return

    this.listeners.get(event).forEach(callback => {
      try {
        callback(data)
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error)
      }
    })
  }

  /**
   * 关闭连接
   */
  disconnect() {
    this.stopHeartbeat()

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close(1000, 'Normal closure')
      this.ws = null
    }

    this.isConnected = false
    this.reconnectAttempts = 0
  }

  /**
   * 获取连接状态
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      readyState: this.ws?.readyState
    }
  }
}

// 创建单例实例
const wsService = new WebSocketService()

// Vue 3 Composable
export function useWebSocket() {
  const connect = (token) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/ws`
    wsService.connect(wsUrl, token)
  }

  const disconnect = () => {
    wsService.disconnect()
  }

  const send = (type, payload) => {
    return wsService.send(type, payload)
  }

  const on = (event, callback) => {
    wsService.on(event, callback)
  }

  const off = (event, callback) => {
    wsService.off(event, callback)
  }

  const getStatus = () => {
    return wsService.getStatus()
  }

  return {
    connect,
    disconnect,
    send,
    on,
    off,
    getStatus
  }
}

// 常用事件类型
export const WS_EVENTS = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error',
  MESSAGE: 'message',

  // 业务事件
  ALERT: 'alert',              // 告警通知
  SOS: 'sos',                  // SOS紧急求助
  HEALTH_UPDATE: 'health_update',  // 健康数据更新
  DEVICE_STATUS: 'device_status',  // 设备状态变化
  MEDICATION_REMINDER: 'medication_reminder', // 用药提醒
  CHAT_MESSAGE: 'chat_message' // 聊天消息
}

export default wsService
