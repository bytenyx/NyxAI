import React from 'react'
import { ArrowDownOutlined } from '@ant-design/icons'

interface HandoffIndicatorProps {
  from: string
  to: string
  context?: string
}

const HandoffIndicator: React.FC<HandoffIndicatorProps> = ({
  from,
  to,
  context,
}) => {
  return (
    <div className="handoff-indicator">
      <ArrowDownOutlined style={{ fontSize: 16, color: '#1890ff' }} />
      <span className="handoff-text">
        {from} → {to}
      </span>
      {context && <span className="handoff-context">{context}</span>}
    </div>
  )
}

export default HandoffIndicator
