import React, { useState } from 'react'
import { Card, Tag } from 'antd'
import {
  SearchOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
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
  startedAt?: string
  completedAt?: string
  durationMs?: number
}

const formatTime = (timestamp?: string): string => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const formatDuration = (ms?: number): string => {
  if (!ms) return ''
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
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
  startedAt,
  completedAt,
  durationMs,
}) => {
  const [expanded, setExpanded] = useState(true)

  const renderTimeInfo = () => {
    if (!startedAt) return null
    
    return (
      <div className="agent-time-info" style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        marginLeft: 'auto',
        marginRight: '12px',
        color: '#8c8c8c',
        fontSize: '12px'
      }}>
        <ClockCircleOutlined />
        <span>{formatTime(startedAt)}</span>
        {durationMs && (
          <span style={{ marginLeft: '4px' }}>
            (耗时: {formatDuration(durationMs)})
          </span>
        )}
        {completedAt && status === 'completed' && (
          <span style={{ marginLeft: '4px' }}>
            → {formatTime(completedAt)}
          </span>
        )}
      </div>
    )
  }

  return (
    <Card
      className="agent-card"
      title={
        <div className="agent-card-header" style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <span className="agent-icon">
            {agentIcons[agent.type] || agent.icon}
          </span>
          <span className="agent-name">{agent.display_name}</span>
          <Tag color={statusColors[status]}>
            {statusIcons[status]} {status}
          </Tag>
          {renderTimeInfo()}
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
