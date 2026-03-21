import React from 'react'
import { Input, Button, Tooltip } from 'antd'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'

interface SessionToolbarProps {
  searchQuery: string
  onSearch: (query: string) => void
  onNewSession: () => void
}

const SessionToolbar: React.FC<SessionToolbarProps> = ({
  searchQuery,
  onSearch,
  onNewSession,
}) => {
  return (
    <div className="session-toolbar">
      <Input
        placeholder="搜索会话..."
        prefix={<SearchOutlined />}
        value={searchQuery}
        onChange={(e) => onSearch(e.target.value)}
        className="session-search"
      />
      <Tooltip title="新建会话">
        <Button type="primary" icon={<PlusOutlined />} onClick={onNewSession} />
      </Tooltip>
    </div>
  )
}

export default SessionToolbar
