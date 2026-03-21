import React, { useEffect, useState } from 'react'
import { Input, Button } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { useSessionStore } from '../../stores/sessionStore'
import { useAgentStore } from '../../stores/agentStore'
import { getWebSocket } from '../../services/websocket'
import AgentProcessPanel from '../Agent/AgentProcessPanel'
import VerticalTimeline from '../Timeline/VerticalTimeline'

const ChatWindow: React.FC = () => {
  const { currentSession } = useSessionStore()
  const { isConnected, handleMessage, setConnected, reset } = useAgentStore()
  const [input, setInput] = useState('')
  const ws = getWebSocket()

  useEffect(() => {
    if (currentSession) {
      reset()
      ws.connect(currentSession.id).then(() => {
        setConnected(true)
      })

      ws.on('*', (message) => {
        handleMessage(message)
      })

      ws.onConnection((connected) => {
        setConnected(connected)
      })
    }

    return () => {
      ws.disconnect()
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
        <VerticalTimeline />
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
