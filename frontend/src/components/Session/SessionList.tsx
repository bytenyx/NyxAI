import React from 'react'
import { List, Tag, Popconfirm, Button } from 'antd'
import { DeleteOutlined } from '@ant-design/icons'
import type { SessionListItem } from '../../types'

interface SessionListProps {
  sessions: SessionListItem[]
  currentSessionId: string | null
  onSelect: (session: SessionListItem) => void
  onDelete: (sessionId: string) => void
}

const statusLabels: Record<string, string> = {
  investigating: '调查中',
  diagnosing: '诊断中',
  recovering: '恢复中',
  completed: '已完成',
  failed: '失败',
}

const statusColors: Record<string, string> = {
  investigating: 'processing',
  diagnosing: 'processing',
  recovering: 'processing',
  completed: 'success',
  failed: 'error',
}

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
}) => {
  const groupByDate = (sessions: SessionListItem[]) => {
    const groups: Record<string, SessionListItem[]> = {}
    const today = new Date().toDateString()
    const yesterday = new Date(Date.now() - 86400000).toDateString()

    sessions.forEach((session) => {
      const date = new Date(session.created_at).toDateString()
      let label = date

      if (date === today) label = '今天'
      else if (date === yesterday) label = '昨天'

      if (!groups[label]) groups[label] = []
      groups[label].push(session)
    })

    return groups
  }

  const grouped = groupByDate(sessions)

  return (
    <div className="session-list">
      {Object.entries(grouped).map(([date, items]) => (
        <div key={date} className="session-group">
          <div className="session-group-label">{date}</div>
          <List
            dataSource={items}
            renderItem={(session) => (
              <List.Item
                className={`session-item ${
                  session.id === currentSessionId ? 'active' : ''
                }`}
                onClick={() => onSelect(session)}
              >
                <div className="session-item-content">
                  <div className="session-title">{session.title || '新会话'}</div>
                  <div className="session-meta">
                    <Tag color={statusColors[session.status]}>
                      {statusLabels[session.status]}
                    </Tag>
                    <span className="session-time">
                      {new Date(session.updated_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <Popconfirm
                  title="确定删除此会话？"
                  onConfirm={(e) => {
                    e?.stopPropagation()
                    onDelete(session.id)
                  }}
                >
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    size="small"
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>
              </List.Item>
            )}
          />
        </div>
      ))}
    </div>
  )
}

export default SessionList
