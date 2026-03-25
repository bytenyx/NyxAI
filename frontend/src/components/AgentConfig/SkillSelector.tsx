import React, { useEffect, useState } from 'react'
import { Checkbox, Spin, message } from 'antd'
import type { SkillMetadata } from '../../types/agentConfig'
import { agentConfigApi } from '../../services/agentConfigApi'

interface SkillSelectorProps {
  value: string[]
  onChange: (skills: string[]) => void
}

const SkillSelector: React.FC<SkillSelectorProps> = ({ value, onChange }) => {
  const [skills, setSkills] = useState<SkillMetadata[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    agentConfigApi.listSkills()
      .then(setSkills)
      .catch(() => message.error('加载技能列表失败'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <Spin />
  }

  return (
    <Checkbox.Group
      value={value}
      onChange={onChange}
      style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
    >
      {skills.map(skill => (
        <Checkbox key={skill.name} value={skill.name}>
          <strong>{skill.name}</strong>
          <span style={{ color: '#666', marginLeft: '8px' }}>{skill.description}</span>
        </Checkbox>
      ))}
    </Checkbox.Group>
  )
}

export default SkillSelector
