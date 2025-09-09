"use client";

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ModuleType } from '../types';

interface ModuleNodeData {
  label: string;
  moduleType: ModuleType;
  parameters: Record<string, any>;
}

export const ModuleNode = memo(({ data, selected }: NodeProps<ModuleNodeData>) => {
  const getModuleColor = (type: ModuleType): string => {
    const colors: Record<ModuleType, string> = {
      'primary_clarifier': 'bg-blue-100 border-blue-500',
      'asm1_reactor': 'bg-green-100 border-green-500',
      'settler': 'bg-blue-100 border-blue-500',
      'thickener': 'bg-purple-100 border-purple-500',
      'adm1_reactor': 'bg-orange-100 border-orange-500',
      'dewatering': 'bg-yellow-100 border-yellow-500',
      'splitter': 'bg-gray-100 border-gray-500',
      'combiner': 'bg-gray-100 border-gray-500',
      'storage': 'bg-indigo-100 border-indigo-500'
    };
    return colors[type] || 'bg-gray-100 border-gray-500';
  };

  const getInputHandles = (type: ModuleType): string[] => {
    const inputs: Record<ModuleType, string[]> = {
      'primary_clarifier': ['influent', 'recycle_sludge'],
      'asm1_reactor': ['influent'],
      'settler': ['mixed_liquor'],
      'thickener': ['waste_sludge'],
      'adm1_reactor': ['organic_sludge'],
      'dewatering': ['digested_sludge'],
      'splitter': ['inlet'],
      'combiner': ['inlet1', 'inlet2'],
      'storage': ['inlet']
    };
    return inputs[type] || ['input'];
  };

  const getOutputHandles = (type: ModuleType): string[] => {
    const outputs: Record<ModuleType, string[]> = {
      'primary_clarifier': ['underflow', 'overflow'],
      'asm1_reactor': ['effluent'],
      'settler': ['return_sludge', 'waste_sludge', 'effluent'],
      'thickener': ['thickened_sludge'],
      'adm1_reactor': ['biogas', 'digested_sludge'],
      'dewatering': ['dewatered_cake', 'filtrate'],
      'splitter': ['outlet1', 'outlet2'],
      'combiner': ['outlet'],
      'storage': ['outlet']
    };
    return outputs[type] || ['output'];
  };

  const inputHandles = getInputHandles(data.moduleType);
  const outputHandles = getOutputHandles(data.moduleType);
  const moduleColor = getModuleColor(data.moduleType);

  return (
    <div className={`px-4 py-2 shadow-md rounded-md border-2 ${moduleColor} ${selected ? 'ring-2 ring-blue-400' : ''} min-w-[120px]`}>
      {/* Input Handles */}
      {inputHandles.map((handle, index) => (
        <Handle
          key={`input-${handle}`}
          type="target"
          position={Position.Left}
          id={handle}
          style={{ 
            top: inputHandles.length === 1 ? '50%' : `${(index + 1) * (100 / (inputHandles.length + 1))}%`,
            background: '#555' 
          }}
        />
      ))}

      {/* Node Content */}
      <div className="text-center">
        <div className="text-sm font-medium text-gray-900">
          {data.label}
        </div>
        {Object.keys(data.parameters).length > 0 && (
          <div className="text-xs text-gray-500 mt-1">
            {Object.keys(data.parameters).length} param(s)
          </div>
        )}
      </div>

      {/* Output Handles */}
      {outputHandles.map((handle, index) => (
        <Handle
          key={`output-${handle}`}
          type="source"
          position={Position.Right}
          id={handle}
          style={{ 
            top: outputHandles.length === 1 ? '50%' : `${(index + 1) * (100 / (outputHandles.length + 1))}%`,
            background: '#555' 
          }}
        />
      ))}
    </div>
  );
});

ModuleNode.displayName = 'ModuleNode';