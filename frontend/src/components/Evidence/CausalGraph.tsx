import React, { useEffect, useRef } from 'react';
import { Card, Empty, Typography } from 'antd';

const { Text } = Typography;

interface CausalNode {
  id: string;
  description: string;
  inference_step?: string;
  confidence?: number;
}

interface CausalEdge {
  source: string;
  target: string;
  relation: 'supports' | 'contradicts';
}

interface CausalGraphProps {
  nodes: CausalNode[];
  edges?: CausalEdge[];
}

const CausalGraph: React.FC<CausalGraphProps> = ({ nodes, edges }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;

    ctx.clearRect(0, 0, width, height);

    const nodePositions: { [key: string]: { x: number; y: number } } = {};
    nodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / nodes.length - Math.PI / 2;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    if (edges) {
      edges.forEach((edge) => {
        const source = nodePositions[edge.source];
        const target = nodePositions[edge.target];
        if (source && target) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.strokeStyle = edge.relation === 'supports' ? '#52c41a' : '#ff4d4f';
          ctx.lineWidth = 2;
          ctx.stroke();

          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          ctx.fillStyle = edge.relation === 'supports' ? '#52c41a' : '#ff4d4f';
          ctx.font = '12px sans-serif';
          ctx.fillText(edge.relation === 'supports' ? '支持' : '矛盾', midX, midY);
        }
      });
    }

    nodes.forEach((node) => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 30, 0, 2 * Math.PI);
      ctx.fillStyle = '#1890ff';
      ctx.fill();
      ctx.strokeStyle = '#096dd9';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#fff';
      ctx.font = 'bold 14px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.id.slice(0, 4), pos.x, pos.y);

      ctx.fillStyle = '#333';
      ctx.font = '12px sans-serif';
      const desc = node.description.length > 20 
        ? node.description.slice(0, 20) + '...' 
        : node.description;
      ctx.fillText(desc, pos.x, pos.y + 45);
    });
  }, [nodes, edges]);

  if (nodes.length === 0) {
    return (
      <Card>
        <Empty description="暂无因果关系数据" />
      </Card>
    );
  }

  return (
    <Card title="因果关系图" size="small">
      <canvas
        ref={canvasRef}
        width={500}
        height={400}
        style={{ width: '100%', maxWidth: 500, height: 'auto' }}
      />
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">
          绿色连线: 支持关系 | 红色连线: 矛盾关系
        </Text>
      </div>
    </Card>
  );
};

export default CausalGraph;
