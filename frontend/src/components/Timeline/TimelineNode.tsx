import React from 'react'
import {
  BellOutlined,
  SearchOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import type { TimelineNode as TimelineNodeType } from '../../types/agent'

interface TimelineNodeProps {
  node: TimelineNodeType
}

const typeIcons: Record<string, React.ReactNode> = {
  alert: <BellOutlined />,
  investigation: <SearchOutlined />,
  diagnosis: <ExperimentOutlined />,
  recovery: <MedicineBoxOutlined />,
  complete: <CheckCircleOutlined />,
}

const statusColors: Record<string, string> = {
  pending: '#d9d9d9',
  running: '#1890ff',
  completed: '#52c41a',
  failed: '#ff4d4f',
}

const TimelineNode: React.FC<TimelineNodeProps> = ({ node }) => {
  const icon = typeIcons[node.type] || <CheckCircleOutlined />
  const color = statusColors[node.status]

  return (
    <div
      className="timeline-node-dot"
      style={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        backgroundColor: color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
      }}
    >
      {node.status === 'running' ? <LoadingOutlined spin /> : icon}
    </div>
  )
}

export default TimelineNode
