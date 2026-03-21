import React, { useState } from 'react'
import { Card, Tag } from 'antd'
import {
  SearchOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import type { AgentIdentity, ToolCallRecord } from '../../types/agent'
import ThinkingStream from './ThinkingStream'
import ToolCallItem from './ToolCallItem'

interface AgentCardProps {
  agent: AgentIdentity
  status: 'idle' | 'running' | 'completed' | 'failed'
  thoughts: string[]
  toolCalls: ToolCallRecord[]
  result?: string
}

const agentIcons: Record<string, React.ReactNode> = {
  investigation: <SearchOutlined />,
  diagnosis: <ExperimentOutlined />,
  recovery: <MedicineBoxOutlined />,
}

const statusIcons: Record<string, React.ReactNode> = {
  idle: null,
  running: <LoadingOutlined spin />,
  completed: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  failed: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
}

const statusColors: Record<string, string> = {
  idle: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
}

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  status,
  thoughts,
  toolCalls,
  result,
}) => {
  const [expanded, setExpanded] = useState(true)

  return (
    <Card
      className="agent-card"
      title={
        <div className="agent-card-header">
          <span className="agent-icon">
            {agentIcons[agent.type] || agent.icon}
          </span>
          <span className="agent-name">{agent.display_name}</span>
          <Tag color={statusColors[status]}>
            {statusIcons[status]} {status}
          </Tag>
        </div>
      }
      extra={
        <a onClick={() => setExpanded(!expanded)}>
          {expanded ? '折叠' : '展开'}
        </a>
      }
    >
      {expanded && (
        <div className="agent-card-content">
          {thoughts.length > 0 && <ThinkingStream thoughts={thoughts} />}

          {toolCalls.length > 0 && (
            <div className="tool-calls">
              {toolCalls.map((tc, idx) => (
                <ToolCallItem key={idx} toolCall={tc} />
              ))}
            </div>
          )}

          {result && (
            <div className="agent-result">
              <strong>结果：</strong>
              <p>{result}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

export default AgentCard
