import React from 'react'
import { useAgentStore } from '../../stores/agentStore'
import AgentCard from './AgentCard'
import HandoffIndicator from './HandoffIndicator'

const AgentProcessPanel: React.FC = () => {
  const { agents, timeline } = useAgentStore()

  const agentList = Object.values(agents)
  const handoffs = timeline.filter((n) => n.id.startsWith('handoff-'))

  return (
    <div className="agent-process-panel">
      {agentList.map((agent, index) => (
        <React.Fragment key={agent.id}>
          <AgentCard
            agent={agent.agent}
            status={agent.status}
            thoughts={agent.thoughts}
            toolCalls={agent.tool_calls}
            result={agent.result}
          />
          {index < agentList.length - 1 && handoffs[index] && (
            <HandoffIndicator
              from={agent.agent.display_name}
              to={handoffs[index].title.split(' → ')[1]}
              context={handoffs[index].description}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}

export default AgentProcessPanel
