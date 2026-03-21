import { List, Typography, Input, Button, Space, Spin } from 'antd'
import { UserOutlined, RobotOutlined, SendOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { chatApi } from '../../services/api'
import { useSessionStore } from '../../stores/sessionStore'

const { TextArea } = Input
const { Text } = Typography

export function ChatWindow() {
  const messages = useSessionStore((state) => state.messages)
  const loading = useSessionStore((state) => state.loading)

  return (
    <div style={{ height: 'calc(100vh - 200px)', overflow: 'auto', padding: 16 }}>
      {messages.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>
          <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
          <div>开始对话，描述您的问题...</div>
        </div>
      )}
      <List
        dataSource={messages}
        renderItem={(item) => (
          <List.Item style={{ border: 'none', padding: '12px 0' }}>
            <div style={{ display: 'flex', gap: 12, width: '100%' }}>
              {item.role === 'user' ? (
                <UserOutlined style={{ fontSize: 20, color: '#1890ff' }} />
              ) : (
                <RobotOutlined style={{ fontSize: 20, color: '#52c41a' }} />
              )}
              <div style={{ flex: 1 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {item.role === 'user' ? '用户' : 'NyxAI'}
                </Text>
                <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{item.content}</div>
              </div>
            </div>
          </List.Item>
        )}
      />
      {loading && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <Spin tip="分析中..." />
        </div>
      )}
    </div>
  )
}

export function MessageInput() {
  const [message, setMessage] = useState('')
  const { currentSession, addMessage, setCurrentSession, setLoading } = useSessionStore()

  const handleSend = async () => {
    if (!message.trim()) return

    addMessage('user', message)
    setLoading(true)
    const currentMessage = message
    setMessage('')

    try {
      const response = await chatApi.message({
        session_id: currentSession?.id,
        message: currentMessage,
      })
      
      addMessage('assistant', response.data.response)
      
      if (!currentSession) {
        setCurrentSession({
          id: response.data.session_id,
          trigger_type: 'chat',
          trigger_source: 'user-input',
          status: 'investigating',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      }
    } catch (error) {
      addMessage('assistant', '抱歉，发生了错误，请重试。')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Space.Compact style={{ width: '100%' }}>
      <TextArea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="描述您的问题..."
        autoSize={{ minRows: 1, maxRows: 4 }}
        onPressEnter={(e) => {
          if (!e.shiftKey) {
            e.preventDefault()
            handleSend()
          }
        }}
        style={{ flex: 1 }}
      />
      <Button type="primary" onClick={handleSend}>
        <SendOutlined />
      </Button>
    </Space.Compact>
  )
}
