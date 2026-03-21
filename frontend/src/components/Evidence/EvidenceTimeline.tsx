import React from 'react';
import { Timeline, Card, Tag, Typography, Space, Tooltip } from 'antd';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface EvidenceNode {
  id: string;
  description: string;
  inference_step?: string;
  confidence?: number;
  timestamp?: string;
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

interface EvidenceTimelineProps {
  evidence: Evidence[];
  evidenceChain?: EvidenceNode[];
}

const getEvidenceIcon = (type: string) => {
  switch (type) {
    case 'metric':
      return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
    case 'log':
      return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
    case 'trace':
      return <ClockCircleOutlined style={{ color: '#722ed1' }} />;
    case 'knowledge':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    default:
      return <InfoCircleOutlined />;
  }
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'green';
  if (confidence >= 0.5) return 'orange';
  return 'red';
};

const EvidenceTimeline: React.FC<EvidenceTimelineProps> = ({ evidence, evidenceChain }) => {
  const timelineItems = evidence.map((e) => ({
    key: e.id,
    dot: getEvidenceIcon(e.evidence_type),
    children: (
      <Card size="small" style={{ marginBottom: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Tag color={getConfidenceColor(e.confidence)}>
              置信度: {(e.confidence * 100).toFixed(0)}%
            </Tag>
            <Tag>{e.evidence_type}</Tag>
            <Text type="secondary">{e.source_system}</Text>
          </Space>
          <Paragraph style={{ margin: 0 }}>{e.description}</Paragraph>
          {e.source_data && Object.keys(e.source_data).length > 0 && (
            <Tooltip title={JSON.stringify(e.source_data, null, 2)}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                <InfoCircleOutlined /> 查看详情
              </Text>
            </Tooltip>
          )}
        </Space>
      </Card>
    ),
  }));

  const chainItems = evidenceChain?.map((node, index) => ({
    key: node.id,
    dot: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    children: (
      <Card size="small" style={{ marginBottom: 8, borderColor: '#52c41a' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Tag color="green">推理节点 {index + 1}</Tag>
            {node.confidence !== undefined && (
              <Tag color={getConfidenceColor(node.confidence)}>
                置信度: {(node.confidence * 100).toFixed(0)}%
              </Tag>
            )}
          </Space>
          <Paragraph style={{ margin: 0 }}>{node.description}</Paragraph>
          {node.inference_step && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              推理: {node.inference_step}
            </Text>
          )}
        </Space>
      </Card>
    ),
  })) || [];

  return (
    <div style={{ padding: '16px 0' }}>
      {chainItems.length > 0 && (
        <>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>
            证据链推理过程
          </Text>
          <Timeline items={chainItems} />
        </>
      )}
      {timelineItems.length > 0 && (
        <>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>
            收集的证据
          </Text>
          <Timeline items={timelineItems} />
        </>
      )}
    </div>
  );
};

export default EvidenceTimeline;
