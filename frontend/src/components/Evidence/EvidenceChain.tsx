import React from 'react';
import { Card, Tabs, Typography } from 'antd';
import EvidenceTimeline from './EvidenceTimeline';
import CausalGraph from './CausalGraph';

const { Title } = Typography;

interface EvidenceNode {
  id: string;
  description: string;
  inference_step?: string;
  confidence?: number;
}

interface Evidence {
  id: string;
  evidence_type: string;
  description: string;
  source_data?: Record<string, any>;
  source_system: string;
  timestamp: string;
  confidence: number;
}

interface EvidenceChainProps {
  evidence: Evidence[];
  evidenceChain?: EvidenceNode[];
}

const EvidenceChain: React.FC<EvidenceChainProps> = ({ evidence, evidenceChain }) => {
  const items = [
    {
      key: 'timeline',
      label: '证据时间线',
      children: (
        <EvidenceTimeline evidence={evidence} evidenceChain={evidenceChain} />
      ),
    },
    {
      key: 'graph',
      label: '因果关系图',
      children: (
        <CausalGraph 
          nodes={evidenceChain || []} 
          edges={[]}
        />
      ),
    },
  ];

  return (
    <Card 
      title={<Title level={5} style={{ margin: 0 }}>证据链分析</Title>}
      size="small"
    >
      <Tabs items={items} />
    </Card>
  );
};

export default EvidenceChain;
