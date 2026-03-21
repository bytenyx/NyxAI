import React from 'react'
import { Typography } from 'antd'
import { BulbOutlined } from '@ant-design/icons'

const { Text } = Typography

interface ThinkingStreamProps {
  thoughts: string[]
}

const ThinkingStream: React.FC<ThinkingStreamProps> = ({ thoughts }) => {
  return (
    <div className="thinking-stream">
      {thoughts.map((thought, index) => (
        <div key={index} className="thought-item">
          <BulbOutlined style={{ marginRight: 8, color: '#faad14' }} />
          <Text type="secondary">{thought}</Text>
        </div>
      ))}
    </div>
  )
}

export default ThinkingStream
