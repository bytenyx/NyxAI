import React from 'react'
import { Timeline, Typography, Empty } from 'antd'
import type { AgentConfigVersion } from '../../types/agentConfig'

const { Text } = Typography

interface VersionHistoryProps {
  versions: AgentConfigVersion[]
  onRollback: (version: number) => void
}

const VersionHistory: React.FC<VersionHistoryProps> = ({ versions, onRollback }) => {
  if (versions.length === 0) {
    return <Empty description="暂无版本历史" />
  }

  return (
    <Timeline
      items={versions.map(v => ({
        color: 'blue',
        children: (
          <div>
            <Text strong>版本 {v.version}</Text>
            <br />
            <Text type="secondary">{v.change_reason || '无变更说明'}</Text>
            <br />
            <Text type="secondary">{new Date(v.created_at).toLocaleString()}</Text>
          </div>
        ),
      }))}
    />
  )
}

export default VersionHistory
