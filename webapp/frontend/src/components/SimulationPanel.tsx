"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { X, Play, Square, BarChart3 } from 'lucide-react';
import { PlantConfiguration, SimulationParameters, SimulationStatus, TimestepData } from '../types';
import { SimulationChart } from './SimulationChart';

interface SimulationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  plantConfiguration: PlantConfiguration;
}

export function SimulationPanel({ isOpen, onClose, plantConfiguration }: SimulationPanelProps) {
  const [simulationParams, setSimulationParams] = useState<SimulationParameters>({
    timestep: 1/24/60, // 1 minute
    endtime: 7.0, // 7 days
    tempmodel: false,
    activate_dummy: false,
    update_frequency: 10
  });
  
  const [currentSimulation, setCurrentSimulation] = useState<{
    id: string;
    status: SimulationStatus;
    data: TimestepData[];
  } | null>(null);

  const [isRunning, setIsRunning] = useState(false);

  const startSimulation = useCallback(async () => {
    if (!plantConfiguration.nodes.length) {
      alert('Please add some modules to the plant first!');
      return;
    }

    try {
      setIsRunning(true);
      
      // Start simulation
      const response = await fetch('http://localhost:8000/api/simulations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plant_config: plantConfiguration,
          simulation_params: simulationParams
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start simulation');
      }

      const result = await response.json();
      const simulationId = result.simulation_id;

      // Initialize simulation tracking
      setCurrentSimulation({
        id: simulationId,
        status: {
          simulation_id: simulationId,
          status: 'starting',
          progress: 0,
          current_time: 0,
          started_at: new Date().toISOString()
        },
        data: []
      });

      // Poll for simulation status and stream data
      const eventSource = new EventSource(`http://localhost:8000/api/simulations/${simulationId}/stream`);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.error) {
            console.error('Simulation error:', data.error);
            eventSource.close();
            setIsRunning(false);
            return;
          }

          // Update simulation data
          setCurrentSimulation(prev => prev ? {
            ...prev,
            data: [...prev.data, data]
          } : null);

        } catch (error) {
          console.error('Error parsing simulation data:', error);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsRunning(false);
      };

      // Also poll for status updates
      const statusInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/api/simulations/${simulationId}/status`);
          const status = await statusResponse.json();
          
          setCurrentSimulation(prev => prev ? {
            ...prev,
            status
          } : null);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(statusInterval);
            setIsRunning(false);
            eventSource.close();
          }
        } catch (error) {
          console.error('Error fetching status:', error);
        }
      }, 1000);

      // Cleanup function
      return () => {
        clearInterval(statusInterval);
        eventSource.close();
      };

    } catch (error) {
      console.error('Error starting simulation:', error);
      setIsRunning(false);
      alert('Failed to start simulation. Make sure the backend is running.');
    }
  }, [plantConfiguration, simulationParams]);

  const stopSimulation = useCallback(async () => {
    if (currentSimulation) {
      try {
        await fetch(`http://localhost:8000/api/simulations/${currentSimulation.id}`, {
          method: 'DELETE'
        });
        setIsRunning(false);
        setCurrentSimulation(null);
      } catch (error) {
        console.error('Error stopping simulation:', error);
      }
    }
  }, [currentSimulation]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="absolute right-0 top-0 h-full w-1/2 bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Simulation</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Simulation Parameters */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Parameters</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Timestep (minutes)
              </label>
              <input
                type="number"
                min="0.1"
                max="60"
                step="0.1"
                value={simulationParams.timestep * 24 * 60}
                onChange={(e) => setSimulationParams(prev => ({
                  ...prev,
                  timestep: parseFloat(e.target.value) / 24 / 60
                }))}
                className="w-full px-2 py-1 border border-gray-300 rounded"
                disabled={isRunning}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Duration (days)
              </label>
              <input
                type="number"
                min="0.1"
                max="365"
                step="0.1"
                value={simulationParams.endtime}
                onChange={(e) => setSimulationParams(prev => ({
                  ...prev,
                  endtime: parseFloat(e.target.value)
                }))}
                className="w-full px-2 py-1 border border-gray-300 rounded"
                disabled={isRunning}
              />
            </div>
          </div>
          
          <div className="mt-3 flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={simulationParams.tempmodel}
                onChange={(e) => setSimulationParams(prev => ({
                  ...prev,
                  tempmodel: e.target.checked
                }))}
                disabled={isRunning}
                className="rounded"
              />
              Temperature Model
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={simulationParams.activate_dummy}
                onChange={(e) => setSimulationParams(prev => ({
                  ...prev,
                  activate_dummy: e.target.checked
                }))}
                disabled={isRunning}
                className="rounded"
              />
              Dummy States
            </label>
          </div>
        </div>

        {/* Control Panel */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex gap-2">
            {!isRunning ? (
              <button
                onClick={startSimulation}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Play className="w-4 h-4" />
                Start Simulation
              </button>
            ) : (
              <button
                onClick={stopSimulation}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                <Square className="w-4 h-4" />
                Stop Simulation
              </button>
            )}
          </div>

          {/* Status */}
          {currentSimulation && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  Status: <span className="capitalize">{currentSimulation.status.status}</span>
                </span>
                <span className="text-sm text-gray-600">
                  {currentSimulation.status.progress.toFixed(1)}%
                </span>
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${currentSimulation.status.progress}%` }}
                />
              </div>
              <div className="mt-2 text-xs text-gray-600">
                Time: {currentSimulation.status.current_time.toFixed(2)} days
              </div>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="flex-1 overflow-hidden">
          {currentSimulation && currentSimulation.data.length > 0 ? (
            <div className="h-full flex flex-col">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  <h3 className="text-sm font-medium text-gray-900">Live Results</h3>
                </div>
              </div>
              <div className="flex-1 p-4">
                <SimulationChart data={currentSimulation.data} />
              </div>
            </div>
          ) : isRunning ? (
            <div className="p-4 text-center text-gray-500">
              <div className="animate-pulse">Waiting for simulation data...</div>
            </div>
          ) : (
            <div className="p-4 text-center text-gray-500">
              <div>Configure parameters and click "Start Simulation" to begin</div>
              <div className="mt-2 text-sm">
                Plant nodes: {plantConfiguration.nodes.length}, Connections: {plantConfiguration.edges.length}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}