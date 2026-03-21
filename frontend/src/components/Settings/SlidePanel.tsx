import React from 'react'
import { Drawer } from 'antd'
import { useSettingsStore } from '../../stores/settingsStore'
import DataSourceForm from './DataSourceForm'
import KnowledgeForm from './KnowledgeForm'
import type { DataSource } from '../../types/datasource'
import type { Knowledge } from '../../types/knowledge'

const SlidePanel: React.FC = () => {
  const { slidePanel, closeSlidePanel } = useSettingsStore()

  if (!slidePanel?.open) return null

  return (
    <Drawer
      title={slidePanel.mode === 'add' ? '添加' : '编辑'}
      placement="right"
      width={400}
      open={slidePanel.open}
      onClose={closeSlidePanel}
      destroyOnClose
    >
      {slidePanel.type === 'datasource' ? (
        <DataSourceForm
          mode={slidePanel.mode}
          data={slidePanel.data as DataSource | undefined}
          onSuccess={closeSlidePanel}
        />
      ) : (
        <KnowledgeForm
          mode={slidePanel.mode}
          data={slidePanel.data as Knowledge | undefined}
          onSuccess={closeSlidePanel}
        />
      )}
    </Drawer>
  )
}

export default SlidePanel
