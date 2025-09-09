"use client";

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { TimestepData } from '../types';

interface SimulationChartProps {
  data: TimestepData[];
}

export function SimulationChart({ data }: SimulationChartProps) {
  const chartData = useMemo(() => {
    return data.map((timestep) => {
      const averageFlowRate = timestep.edge_flows.length > 0
        ? timestep.edge_flows.reduce((sum, flow) => sum + flow.components.Q, 0) / timestep.edge_flows.length
        : 0;

      const averageCOD = timestep.edge_flows.length > 0
        ? timestep.edge_flows.reduce((sum, flow) => sum + (flow.components.SI + flow.components.SS + flow.components.XS), 0) / timestep.edge_flows.length
        : 0;

      const averageNitrogen = timestep.edge_flows.length > 0
        ? timestep.edge_flows.reduce((sum, flow) => sum + (flow.components.SNO + flow.components.SNH), 0) / timestep.edge_flows.length
        : 0;

      return {
        time: timestep.time,
        timestep: timestep.timestep,
        flowRate: averageFlowRate,
        COD: averageCOD,
        nitrogen: averageNitrogen,
        IQI: timestep.performance.IQI,
        EQI: timestep.performance.EQI,
        OCI: timestep.performance.OCI,
        aerationEnergy: timestep.performance.aeration_energy,
        pumpingEnergy: timestep.performance.pumping_energy,
        mixingEnergy: timestep.performance.mixing_energy,
      };
    });
  }, [data]);

  if (chartData.length === 0) {
    return <div className="text-center text-gray-500 py-8">No simulation data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Flow Rate Chart */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Average Flow Rate</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                type="number"
                scale="linear"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => `${value.toFixed(1)}d`}
              />
              <YAxis tickFormatter={(value) => `${value.toFixed(0)}`} />
              <Tooltip 
                labelFormatter={(value) => `Time: ${Number(value).toFixed(2)} days`}
                formatter={(value: number, name) => [
                  `${value.toFixed(2)} ${name === 'flowRate' ? 'm³/d' : ''}`,
                  'Flow Rate'
                ]}
              />
              <Area 
                type="monotone" 
                dataKey="flowRate" 
                stroke="#3B82F6" 
                fill="#3B82F6" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* COD and Nitrogen Chart */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Water Quality Indicators</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                type="number"
                scale="linear"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => `${value.toFixed(1)}d`}
              />
              <YAxis tickFormatter={(value) => `${value.toFixed(0)}`} />
              <Tooltip 
                labelFormatter={(value) => `Time: ${Number(value).toFixed(2)} days`}
                formatter={(value: number, name) => [
                  `${value.toFixed(2)} g/m³`,
                  name === 'COD' ? 'COD' : 'Nitrogen'
                ]}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="COD" 
                stroke="#F59E0B" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="nitrogen" 
                stroke="#10B981" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Performance Indices</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                type="number"
                scale="linear"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => `${value.toFixed(1)}d`}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => `Time: ${Number(value).toFixed(2)} days`}
                formatter={(value: number, name) => [
                  `${value.toFixed(4)}`,
                  name.toUpperCase()
                ]}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="IQI" 
                stroke="#EF4444" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="EQI" 
                stroke="#8B5CF6" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="OCI" 
                stroke="#F97316" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Energy Consumption */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Energy Consumption</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                type="number"
                scale="linear"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => `${value.toFixed(1)}d`}
              />
              <YAxis tickFormatter={(value) => `${value.toFixed(0)}`} />
              <Tooltip 
                labelFormatter={(value) => `Time: ${Number(value).toFixed(2)} days`}
                formatter={(value: number, name) => [
                  `${value.toFixed(2)} kWh/d`,
                  name === 'aerationEnergy' ? 'Aeration' :
                  name === 'pumpingEnergy' ? 'Pumping' : 'Mixing'
                ]}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="aerationEnergy" 
                stackId="1"
                stroke="#DC2626" 
                fill="#DC2626" 
                fillOpacity={0.8}
              />
              <Area 
                type="monotone" 
                dataKey="pumpingEnergy" 
                stackId="1"
                stroke="#2563EB" 
                fill="#2563EB" 
                fillOpacity={0.8}
              />
              <Area 
                type="monotone" 
                dataKey="mixingEnergy" 
                stackId="1"
                stroke="#059669" 
                fill="#059669" 
                fillOpacity={0.8}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Current Statistics</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-600">Simulation Time</div>
            <div className="font-medium">{chartData[chartData.length - 1]?.time.toFixed(2)} days</div>
          </div>
          <div>
            <div className="text-gray-600">Data Points</div>
            <div className="font-medium">{chartData.length}</div>
          </div>
          <div>
            <div className="text-gray-600">Avg Flow Rate</div>
            <div className="font-medium">
              {chartData.length > 0 
                ? (chartData.reduce((sum, d) => sum + d.flowRate, 0) / chartData.length).toFixed(0) 
                : 0} m³/d
            </div>
          </div>
          <div>
            <div className="text-gray-600">Avg COD</div>
            <div className="font-medium">
              {chartData.length > 0 
                ? (chartData.reduce((sum, d) => sum + d.COD, 0) / chartData.length).toFixed(1)
                : 0} g/m³
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}