import type { ServerMessage } from '../types/agent'

type MessageHandler = (message: ServerMessage) => void
type ConnectionHandler = (connected: boolean) => void

export class ChatWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private connectionHandlers: Set<ConnectionHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  private reconnectDelay = 1000
  private messageQueue: string[] = []

  constructor(baseUrl: string) {
    this.url = baseUrl.replace('http', 'ws')
  }

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${this.url}/api/v1/ws/chat/${sessionId}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.notifyConnectionHandlers(true)

        this.messageQueue.forEach((msg) => {
          this.ws?.send(msg)
        })
        this.messageQueue = []

        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: ServerMessage = JSON.parse(event.data)
          this.emit(message.type, message)
          this.emit('*', message)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.notifyConnectionHandlers(false)
        this.attemptReconnect(sessionId)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }
    })
  }

  private attemptReconnect(sessionId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

      console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`)

      setTimeout(() => {
        this.connect(sessionId)
      }, delay)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  on(eventType: string, handler: MessageHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set())
    }
    this.handlers.get(eventType)!.add(handler)
  }

  off(eventType: string, handler: MessageHandler) {
    if (this.handlers.has(eventType)) {
      this.handlers.get(eventType)!.delete(handler)
    }
  }

  onConnection(handler: ConnectionHandler) {
    this.connectionHandlers.add(handler)
  }

  offConnection(handler: ConnectionHandler) {
    this.connectionHandlers.delete(handler)
  }

  private emit(eventType: string, message: ServerMessage) {
    if (this.handlers.has(eventType)) {
      this.handlers.get(eventType)!.forEach((handler) => handler(message))
    }
  }

  private notifyConnectionHandlers(connected: boolean) {
    this.connectionHandlers.forEach((handler) => handler(connected))
  }

  sendChat(content: string) {
    const message = JSON.stringify({ type: 'chat', content })
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message)
    } else {
      this.messageQueue.push(message)
    }
  }

  sendStop() {
    const message = JSON.stringify({ type: 'stop' })
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message)
    }
  }

  sendPing() {
    const message = JSON.stringify({ type: 'ping' })
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message)
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

let wsInstance: ChatWebSocket | null = null

export function getWebSocket(): ChatWebSocket {
  if (!wsInstance) {
    const apiUrl = (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || 'http://localhost:8000'
    wsInstance = new ChatWebSocket(apiUrl)
  }
  return wsInstance
}
