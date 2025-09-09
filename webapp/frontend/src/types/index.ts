// Type definitions for the BSM2 wastewater plant simulator

export type ModuleType =
  | 'primary_clarifier'
  | 'asm1_reactor'
  | 'settler'
  | 'thickener'
  | 'adm1_reactor'
  | 'dewatering'
  | 'splitter'
  | 'combiner'
  | 'storage';

export interface Position {
  x: number;
  y: number;
}

export interface ModuleNode {
  id: string;
  type: ModuleType;
  position: Position;
  parameters: Record<string, any>;
  name?: string;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  sourcePort: string;
  targetPort: string;
  parameters: Record<string, any>;
}

export interface PlantConfiguration {
  nodes: ModuleNode[];
  edges: FlowEdge[];
  influent_data?: Record<string, any>;
}

export interface SimulationParameters {
  timestep: number;
  endtime: number;
  tempmodel: boolean;
  activate_dummy: boolean;
  update_frequency: number;
}

export interface SimulationRequest {
  plant_config: PlantConfiguration;
  simulation_params: SimulationParameters;
}

export interface SimulationStatus {
  simulation_id: string;
  status: 'starting' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_time: number;
  started_at: string;
  message?: string;
}

export interface ComponentData {
  SI: number;
  SS: number;
  XI: number;
  XS: number;
  XBH: number;
  XBA: number;
  XP: number;
  SO: number;
  SNO: number;
  SNH: number;
  SND: number;
  XND: number;
  SALK: number;
  TSS: number;
  Q: number;
  TEMP: number;
}

export interface EdgeFlowData {
  edge_id: string;
  timestep: number;
  time: number;
  components: ComponentData;
}

export interface PerformanceMetrics {
  IQI: number;
  EQI: number;
  OCI: number;
  aeration_energy: number;
  pumping_energy: number;
  mixing_energy: number;
}

export interface TimestepData {
  timestep: number;
  time: number;
  edge_flows: EdgeFlowData[];
  performance: PerformanceMetrics;
}

export interface SimulationResult {
  simulation_id: string;
  plant_config: PlantConfiguration;
  simulation_params: SimulationParameters;
  timesteps: TimestepData[];
  final_performance: PerformanceMetrics;
  completed_at: string;
}

export interface ModuleDefinition {
  id: string;
  name: string;
  type: string;
  inputs: string[];
  outputs: string[];
  parameters: string[];
  description: string;
}

export interface PlantTemplate {
  id: string;
  name: string;
  description: string;
  nodes: ModuleNode[];
  edges: FlowEdge[];
}