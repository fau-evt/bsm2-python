"use client";

import React, { useState, useCallback, useRef } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  Connection,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { ModuleNode } from './ModuleNode';
import { Sidebar } from './Sidebar';
import { SimulationPanel } from './SimulationPanel';
import { PlantConfiguration, ModuleType } from '../types';

const nodeTypes = {
  moduleNode: ModuleNode,
};

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'moduleNode',
    position: { x: 250, y: 25 },
    data: { 
      label: 'Primary Clarifier',
      moduleType: 'primary_clarifier' as ModuleType,
      parameters: {}
    },
  },
];

const initialEdges: Edge[] = [];

export function PlantDesigner() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isSimulationPanelOpen, setIsSimulationPanelOpen] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const label = event.dataTransfer.getData('application/reactflow-label');
      const moduleType = event.dataTransfer.getData('application/reactflow-moduletype');

      // Check if the dropped element is valid
      if (typeof type === 'undefined' || !type || !reactFlowInstance) {
        return;
      }

      // Get the position where the node was dropped
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: getId(),
        type,
        position,
        data: { 
          label,
          moduleType: moduleType as ModuleType,
          parameters: {}
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const updateNodeParameters = useCallback((nodeId: string, parameters: any) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, parameters } }
          : node
      )
    );
  }, [setNodes]);

  const getCurrentConfiguration = useCallback((): PlantConfiguration => {
    return {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.data.moduleType,
        position: node.position,
        parameters: node.data.parameters || {},
        name: node.data.label
      })),
      edges: edges.map(edge => ({
        id: edge.id || `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        sourcePort: edge.sourceHandle || 'output',
        targetPort: edge.targetHandle || 'input',
        parameters: {}
      }))
    };
  }, [nodes, edges]);

  const loadTemplate = useCallback((template: any) => {
    const templateNodes = template.nodes.map((node: any) => ({
      id: node.id,
      type: 'moduleNode',
      position: node.position,
      data: {
        label: getModuleLabel(node.type),
        moduleType: node.type,
        parameters: node.parameters || {}
      }
    }));

    const templateEdges = template.edges.map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourcePort,
      targetHandle: edge.targetPort
    }));

    setNodes(templateNodes);
    setEdges(templateEdges);
  }, [setNodes, setEdges]);

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <Sidebar 
        selectedNode={selectedNode}
        onNodeParametersChange={updateNodeParameters}
        onLoadTemplate={loadTemplate}
      />
      
      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 p-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-900">
            Wastewater Treatment Plant Designer
          </h1>
          <div className="flex gap-2">
            <button
              onClick={() => setIsSimulationPanelOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Run Simulation
            </button>
            <button
              onClick={() => {
                setNodes([]);
                setEdges([]);
                setSelectedNode(null);
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Clear All
            </button>
          </div>
        </div>
        
        <div
          ref={reactFlowWrapper}
          className="flex-1"
          onDrop={onDrop}
          onDragOver={onDragOver}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </div>
      </div>

      {/* Simulation Panel */}
      <SimulationPanel
        isOpen={isSimulationPanelOpen}
        onClose={() => setIsSimulationPanelOpen(false)}
        plantConfiguration={getCurrentConfiguration()}
      />
    </div>
  );
}

// Helper functions
let id = 0;
const getId = () => `dndnode_${id++}`;

const getModuleLabel = (moduleType: string): string => {
  const labels: Record<string, string> = {
    'primary_clarifier': 'Primary Clarifier',
    'asm1_reactor': 'ASM1 Reactor',
    'settler': 'Secondary Clarifier',
    'thickener': 'Sludge Thickener',
    'adm1_reactor': 'Anaerobic Digester',
    'dewatering': 'Dewatering Unit',
    'splitter': 'Flow Splitter',
    'combiner': 'Flow Combiner',
    'storage': 'Storage Tank'
  };
  return labels[moduleType] || moduleType;
};