import React, { useEffect, useState, useRef } from 'react'
import { Input, Button, message } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { useSessionStore } from '../../stores/sessionStore'
import { useAgentStore } from '../../stores/agentStore'
import { getWebSocket } from '../../services/websocket'
import { sessionsApi } from '../../services/api'
import AgentProcessPanel from '../Agent/AgentProcessPanel'

const ChatWindow: React.FC = () => {
  const { currentSession } = useSessionStore()
  const { 
    isConnected, 
    handleMessage, 
    setConnected, 
    reset, 
    loadFromHistory,
    saveSessionState,
    restoreSessionState,
    setCurrentSessionId,
  } = useAgentStore()
  const [input, setInput] = useState('')
  const ws = getWebSocket()
  const prevSessionIdRef = useRef<string | null>(null)
  const messageHandlerRef = useRef<((message: any) => void) | null>(null)
  const connectionHandlerRef = useRef<((connected: boolean) => void) | null>(null)

  useEffect(() => {
    if (currentSession) {
      const prevSessionId = prevSessionIdRef.current
      const newSessionId = currentSession.id

      if (prevSessionId && prevSessionId !== newSessionId) {
        saveSessionState(prevSessionId)
        ws.disconnect()
      }

      const restored = restoreSessionState(newSessionId)
      setCurrentSessionId(newSessionId)

      if (!restored) {
        reset()
      }

      ws.connect(newSessionId).then(() => {
        setConnected(true)
      }).catch((error) => {
        console.error('WebSocket connection failed:', error)
      })

      if (messageHandlerRef.current) {
        ws.off('*', messageHandlerRef.current)
      }
      if (connectionHandlerRef.current) {
        ws.offConnection(connectionHandlerRef.current)
      }

      const messageHandler = (msg: any) => {
        handleMessage(msg)
      }
      const connectionHandler = (connected: boolean) => {
        setConnected(connected)
      }

      messageHandlerRef.current = messageHandler
      connectionHandlerRef.current = connectionHandler

      ws.on('*', messageHandler)
      ws.onConnection(connectionHandler)

      if (!restored) {
        sessionsApi.getExecutions(newSessionId)
          .then((executions) => {
            if (executions && executions.length > 0) {
              loadFromHistory(executions)
            }
          })
          .catch((error) => {
            console.error('Failed to load session history:', error)
            message.error('加载历史会话失败')
          })
      }

      prevSessionIdRef.current = newSessionId

      return () => {
        if (messageHandlerRef.current) {
          ws.off('*', messageHandlerRef.current)
        }
        if (connectionHandlerRef.current) {
          ws.offConnection(connectionHandlerRef.current)
        }
        ws.disconnect()
      }
    }
  }, [currentSession?.id])

  const handleSend = () => {
    if (input.trim() && ws.isConnected()) {
      ws.sendChat(input.trim())
      setInput('')
    }
  }

  if (!currentSession) {
    return (
      <div className="chat-window-empty">
        <p>选择或创建一个会话开始对话</p>
      </div>
    )
  }

  return (
    <div className="chat-window">
      <div className="chat-content">
        <AgentProcessPanel />
      </div>

      <div className="chat-input">
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入消息..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={!isConnected}
        >
          发送
        </Button>
      </div>
    </div>
  )
}

export default ChatWindow
