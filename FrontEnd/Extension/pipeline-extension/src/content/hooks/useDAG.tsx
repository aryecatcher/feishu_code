import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  NodeTypes,
  NodeProps,
  PanOnScrollMode,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from '@dagrejs/dagre';

export interface DAGNode extends Record<string, unknown> {
  id: string;
  label: string;
  status: 'success' | 'failed' | 'running' | 'pending';
}

type CustomNodeType = Node<DAGNode, 'custom'>;

export interface DAGEdge {
  from: string;
  to: string;
}

export interface UseDAGOptions {
  onNodeClick?: (node: DAGNode) => void;
}

const getStatusColor = (status: DAGNode['status']) => {
  switch (status) {
    case 'success':
      return '#52c41a';
    case 'failed':
      return '#ff4d4f';
    case 'running':
      return '#1890ff';
    case 'pending':
      return '#d9d9d9';
    default:
      return '#d9d9d9';
  }
};

const CustomNode = ({ data, selected }: NodeProps<CustomNodeType>) => {
  const statusColor = getStatusColor(data.status);
  
  return (
    <div
      style={{
        padding: '10px',
        border: `2px solid ${statusColor}`,
        borderRadius: '8px',
        backgroundColor: '#fff',
        minWidth: '50px',
        textAlign: 'center',
        boxShadow: selected ? `0 0 2px 3px ${statusColor}` : '0 2px 5px rgba(0, 0, 0, 0.1)',
        transition: 'all 1s ease',
        position: 'relative',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ visibility: 'hidden' }} />
      <div style={{ fontWeight: 500, fontSize: '14px', marginBottom: '4px', color: '#000' }}>{data.label}</div>
      <div
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: statusColor,
          margin: '0 auto',
        }}
      />
      <Handle type="source" position={Position.Right} style={{ visibility: 'hidden' }} />
    </div>
  );
};

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  dagreGraph.setGraph({
      rankdir: direction,
      nodesep: 30,
      ranksep: 30,
    });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 60, height: 40 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 60 / 2,
        y: nodeWithPosition.y - 40 / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

export const useDAG = (
  nodes: DAGNode[],
  edges: DAGEdge[],
  options: UseDAGOptions = {}
) => {
  const { onNodeClick } = options;

  const flowNodes: Node<DAGNode>[] = useMemo(() => {
    return nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      position: { x: 0, y: 0 },
      data: node,
    }));
  }, [nodes]);

  const flowEdges: Edge[] = useMemo(() => {
    return edges.map((edge, index) => ({
      id: `edge-${index}`,
      source: edge.from,
      target: edge.to,
      type: 'smoothstep',
      animated: false,
      style: { stroke: '#91d5ff', strokeWidth: 2 },
    }));
  }, [edges]);

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    return getLayoutedElements(flowNodes, flowEdges, 'LR');
  }, [flowNodes, flowEdges]);

  const [reactFlowNodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [reactFlowEdges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: any) => {
      if (onNodeClick) {
        onNodeClick(node.data as DAGNode);
      }
    },
    [onNodeClick]
  );

  const DAGComponent = useCallback(() => {
    return (
      <div className="no-drag" style={{ width: '100%', height: '100%', overflowX: 'auto', overflowY: 'hidden' }}>
        <div style={{ minWidth: 'max-content', height: '100%' }}>
          <ReactFlow
            nodes={reactFlowNodes}
            edges={reactFlowEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            nodeTypes={nodeTypes}
            panOnDrag={true}
            panOnScroll={true}
            panOnScrollMode={PanOnScrollMode.Horizontal}
            zoomOnPinch={false}
            zoomOnDoubleClick={false}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={true}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={16} size={1} color="#f0f0f0" />
          </ReactFlow>
        </div>
      </div>
    );
  }, [reactFlowNodes, reactFlowEdges, onNodesChange, onEdgesChange, handleNodeClick]);

  return {
    DAGComponent,
    nodes: reactFlowNodes,
    edges: reactFlowEdges,
  };
};
