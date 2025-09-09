"use client";

import React, { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { ModuleDefinition, PlantTemplate } from '../types';

interface SidebarProps {
  selectedNode: Node | null;
  onNodeParametersChange: (nodeId: string, parameters: any) => void;
  onLoadTemplate: (template: PlantTemplate) => void;
}

export function Sidebar({ selectedNode, onNodeParametersChange, onLoadTemplate }: SidebarProps) {
  const [modules, setModules] = useState<ModuleDefinition[]>([]);
  const [templates, setTemplates] = useState<PlantTemplate[]>([]);
  const [parameters, setParameters] = useState<Record<string, any>>({});

  useEffect(() => {
    // Fetch available modules from backend
    fetch('http://localhost:8000/api/modules')
      .then(res => res.json())
      .then(data => setModules(data.modules))
      .catch(console.error);

    // Fetch plant templates from backend
    fetch('http://localhost:8000/api/templates')
      .then(res => res.json())
      .then(data => setTemplates(data.templates))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedNode) {
      setParameters(selectedNode.data.parameters || {});
    } else {
      setParameters({});
    }
  }, [selectedNode]);

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string, moduleType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('application/reactflow-label', label);
    event.dataTransfer.setData('application/reactflow-moduletype', moduleType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleParameterChange = (key: string, value: any) => {
    const newParameters = { ...parameters, [key]: value };
    setParameters(newParameters);
    if (selectedNode) {
      onNodeParametersChange(selectedNode.id, newParameters);
    }
  };

  const getDefaultParameters = (moduleType: string): Record<string, any> => {
    const defaults: Record<string, Record<string, any>> = {
      'primary_clarifier': {
        volume: 1500,
        area: 1500,
        settling_velocity: 0.5
      },
      'asm1_reactor': {
        volume: 1333,
        kla: 240,
        temperature: 15
      },
      'settler': {
        area: 1500,
        depth: 4,
        settling_parameters: {}
      },
      'thickener': {
        area: 250,
        solids_flux: 3.0
      },
      'adm1_reactor': {
        volume: 3000,
        temperature: 35,
        ph: 7.0
      },
      'dewatering': {
        efficiency: 0.95,
        polymer_dose: 5
      },
      'splitter': {
        split_ratio: 0.5
      },
      'combiner': {},
      'storage': {
        volume: 500
      }
    };
    return defaults[moduleType] || {};
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-screen">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Plant Designer</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {/* Module Palette */}
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Available Modules</h3>
          <div className="space-y-2">
            {modules.map((module) => (
              <div
                key={module.id}
                className="p-3 bg-gray-50 rounded-lg border cursor-move hover:bg-gray-100"
                draggable
                onDragStart={(event) => onDragStart(event, 'moduleNode', module.name, module.id)}
              >
                <div className="font-medium text-sm text-gray-900">{module.name}</div>
                <div className="text-xs text-gray-500 mt-1">{module.description}</div>
                <div className="flex gap-1 mt-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    {module.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Templates */}
        <div className="p-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Plant Templates</h3>
          <div className="space-y-2">
            {templates.map((template) => (
              <div
                key={template.id}
                className="p-3 bg-green-50 rounded-lg border cursor-pointer hover:bg-green-100"
                onClick={() => onLoadTemplate(template)}
              >
                <div className="font-medium text-sm text-gray-900">{template.name}</div>
                <div className="text-xs text-gray-500 mt-1">{template.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Node Parameters */}
        {selectedNode && (
          <div className="p-4 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              {selectedNode.data.label} Parameters
            </h3>
            <div className="space-y-3">
              {Object.entries(getDefaultParameters(selectedNode.data.moduleType)).map(([key, defaultValue]) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </label>
                  {typeof defaultValue === 'number' ? (
                    <input
                      type="number"
                      step="any"
                      value={parameters[key] || defaultValue}
                      onChange={(e) => handleParameterChange(key, parseFloat(e.target.value) || 0)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  ) : typeof defaultValue === 'boolean' ? (
                    <input
                      type="checkbox"
                      checked={parameters[key] || defaultValue}
                      onChange={(e) => handleParameterChange(key, e.target.checked)}
                      className="rounded"
                    />
                  ) : (
                    <input
                      type="text"
                      value={parameters[key] || defaultValue}
                      onChange={(e) => handleParameterChange(key, e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}