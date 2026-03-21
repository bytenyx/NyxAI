import { List, Typography, Input, Button, Space, Spin, Card, Collapse } from 'antd'
import { UserOutlined, RobotOutlined, SendOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { chatApi } from '../../services/api'
import { useSessionStore } from '../../stores/sessionStore'
import EvidenceChain from '../Evidence/EvidenceChain'

const { TextArea } = Input
const { Text, Title } = Typography

interface Evidence {
  id: string
  evidence_type: string
  description: string
  source_data?: Record<string, any>
  source_system: string
  timestamp: string
  confidence: number
}

interface EvidenceNode {
  id: string
  description: string
  inference_step?: string
  confidence?: number
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  evidence?: Evidence[]
  evidenceChain?: EvidenceNode[]
  rootCause?: string
  actions?: any[]
}

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
        renderItem={(item: any) => (
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
                
                {item.role === 'assistant' && (item.evidence?.length > 0 || item.evidenceChain?.length > 0) && (
                  <Collapse
                    style={{ marginTop: 12 }}
                    items={[
                      {
                        key: 'evidence',
                        label: (
                          <Space>
                            <CheckCircleOutlined style={{ color: '#52c41a' }} />
                            <span>证据链分析 ({item.evidence?.length || 0} 条证据)</span>
                          </Space>
                        ),
                        children: (
                          <EvidenceChain 
                            evidence={item.evidence || []} 
                            evidenceChain={item.evidenceChain} 
                          />
                        ),
                      },
                    ]}
                  />
                )}
                
                {item.role === 'assistant' && item.rootCause && (
                  <Card size="small" style={{ marginTop: 12, borderColor: '#faad14' }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Text strong style={{ color: '#faad14' }}>
                        <ExclamationCircleOutlined /> 根因分析
                      </Text>
                      <Text>{item.rootCause}</Text>
                    </Space>
                  </Card>
                )}
                
                {item.role === 'assistant' && item.actions?.length > 0 && (
                  <Card size="small" style={{ marginTop: 12, borderColor: '#52c41a' }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Text strong style={{ color: '#52c41a' }}>
                        <CheckCircleOutlined /> 建议操作
                      </Text>
                      {item.actions.map((action: any, idx: number) => (
                        <div key={idx}>
                          <Text>{idx + 1}. {action.description}</Text>
                          <Text type="secondary" style={{ marginLeft: 8 }}>
                            (风险: {action.risk_level})
                          </Text>
                        </div>
                      ))}
                    </Space>
                  </Card>
                )}
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
