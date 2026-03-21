import React from 'react'
import { Timeline } from 'antd'
import { useAgentStore } from '../../stores/agentStore'
import TimelineNode from './TimelineNode'

const VerticalTimeline: React.FC = () => {
  const { timeline } = useAgentStore()

  return (
    <div className="vertical-timeline">
      <Timeline
        items={timeline.map((node) => ({
          key: node.id,
          dot: <TimelineNode node={node} />,
          children: (
            <div className="timeline-content">
              <div className="timeline-header">
                <span className="timeline-title">{node.title}</span>
                <span className="timeline-time">{node.timestamp}</span>
              </div>
              {node.description && (
                <div className="timeline-description">{node.description}</div>
              )}
            </div>
          ),
        }))}
      />
    </div>
  )
}

export default VerticalTimeline
