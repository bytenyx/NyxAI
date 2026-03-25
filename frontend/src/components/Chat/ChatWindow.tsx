import React, { useEffect, useState, useRef } from 'react'
import { Input, Button, message } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { useSessionStore } from '../../stores/sessionStore'
import { useAgentStore } from '../../stores/agentStore'
import { getWebSocket } from '../../services/websocket'
import { sessionsApi } from '../../services/api'
import AgentProcessPanel from '../Agent/AgentProcessPanel'

const ChatWindow: React.FC = () => {
  const { currentSession, setCurrentSession, addSession, updateSession } = useSessionStore()
  const { 
    isConnected, 
    handleMessage, 
    setConnected, 
    reset, 
    loadFromHistory,
    saveSessionState,
    restoreSessionState,
    setCurrentSessionId,
    timeline,
  } = useAgentStore()
  const [input, setInput] = useState('')
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const ws = getWebSocket()
  const prevSessionIdRef = useRef<string | null>(null)
  const messageHandlerRef = useRef<((message: any) => void) | null>(null)
  const connectionHandlerRef = useRef<((connected: boolean) => void) | null>(null)
  const pendingMessageRef = useRef<string | null>(null)

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
        if (pendingMessageRef.current) {
          ws.sendChat(pendingMessageRef.current)
          pendingMessageRef.current = null
        }
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

  const generateTitleFromMessage = (msg: string): string => {
    const maxLength = 10
    let title = msg.trim().replace(/\n/g, ' ')
    if (title.length > maxLength) {
      title = title.substring(0, maxLength) + '...'
    }
    return title || '新会话'
  }

  const handleWelcomeSend = async () => {
    if (!input.trim() || isCreatingSession) return

    setIsCreatingSession(true)
    const messageToSend = input.trim()
    const title = generateTitleFromMessage(messageToSend)
    try {
      if (currentSession) {
        const updatedSession = await sessionsApi.update(currentSession.id, { title })
        updateSession(updatedSession)
        if (ws.isConnected()) {
          ws.sendChat(messageToSend)
        } else {
          pendingMessageRef.current = messageToSend
        }
      } else {
        const response = await sessionsApi.create({
          trigger_type: 'manual',
          trigger_source: 'user',
          title,
        })
        pendingMessageRef.current = messageToSend
        setCurrentSession(response)
        addSession(response)
      }
      setInput('')
    } catch (error) {
      console.error('Failed to create session:', error)
      message.error('创建会话失败')
    } finally {
      setIsCreatingSession(false)
    }
  }

  const showWelcome = !currentSession || timeline.length === 0

  if (showWelcome) {
    return (
      <div className="chat-window-welcome">
        <div className="welcome-content">
          <h1 className="welcome-title">欢迎使用 NyxAI</h1>
          <p className="welcome-subtitle">开始一段新的对话</p>
          <div className="welcome-input-wrapper">
            <Input.TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入您的问题或想法..."
              autoSize={{ minRows: 3, maxRows: 8 }}
              className="welcome-textarea"
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault()
                  handleWelcomeSend()
                }
              }}
            />
            <Button
              type="primary"
              size="large"
              icon={<SendOutlined />}
              onClick={handleWelcomeSend}
              loading={isCreatingSession}
              className="welcome-send-btn"
            >
              开始对话
            </Button>
          </div>
        </div>
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
