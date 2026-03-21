import React from 'react'
import { Collapse, Tag } from 'antd'
import { ToolOutlined } from '@ant-design/icons'
import type { ToolCallRecord } from '../../types/agent'

interface ToolCallItemProps {
  toolCall: ToolCallRecord
}

const ToolCallItem: React.FC<ToolCallItemProps> = ({ toolCall }) => {
  return (
    <Collapse
      className="tool-call-item"
      items={[
        {
          key: '1',
          label: (
            <div className="tool-call-header">
              <ToolOutlined style={{ marginRight: 8 }} />
              <span>{toolCall.tool}</span>
              <Tag>{toolCall.status}</Tag>
            </div>
          ),
          children: (
            <div className="tool-call-content">
              <div className="params">
                <strong>参数：</strong>
                <pre>{JSON.stringify(toolCall.params, null, 2)}</pre>
              </div>
              {toolCall.result !== undefined && (
                <div className="result">
                  <strong>结果：</strong>
                  <pre>
                    {typeof toolCall.result === 'string'
                      ? toolCall.result
                      : JSON.stringify(toolCall.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ),
        },
      ]}
    />
  )
}

export default ToolCallItem
