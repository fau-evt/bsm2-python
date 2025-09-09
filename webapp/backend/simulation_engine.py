"""
Simulation engine that handles the conversion from node-edge plant configurations
to BSM2 module simulations, orchestrates the execution, and provides real-time data.
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np
import uuid

from bsm2_python import BSM2OL
from bsm2_python.bsm2.helpers_bsm2 import Splitter, Combiner
from bsm2_python.bsm2.asm1_bsm2 import ASM1Reactor
from bsm2_python.bsm2.primclar_bsm2 import PrimaryClarifier
from bsm2_python.bsm2.settler1d_bsm2 import Settler
from bsm2_python.bsm2.thickener_bsm2 import Thickener
from bsm2_python.bsm2.adm1_bsm2 import ADM1Reactor
from bsm2_python.bsm2.dewatering_bsm2 import Dewatering
from bsm2_python.bsm2.storage_bsm2 import Storage

from models import (
    PlantConfiguration,
    SimulationParameters,
    SimulationStatus,
    ValidationResult,
    TimestepData,
    EdgeFlowData,
    ComponentData,
    PerformanceMetrics,
    SimulationResult,
    ModuleType
)


class ModuleInstance:
    """Wrapper for BSM2 module instances with metadata."""
    
    def __init__(self, node_id: str, module_type: ModuleType, bsm2_module: Any, parameters: Dict[str, Any]):
        self.node_id = node_id
        self.module_type = module_type
        self.bsm2_module = bsm2_module
        self.parameters = parameters
        self.inputs: Dict[str, np.ndarray] = {}
        self.outputs: Dict[str, np.ndarray] = {}


class PlantNetwork:
    """Represents the plant as a network of connected modules."""
    
    def __init__(self, config: PlantConfiguration):
        self.config = config
        self.modules: Dict[str, ModuleInstance] = {}
        self.execution_order: List[str] = []
        self.edge_map: Dict[str, Dict[str, str]] = {}  # edge_id -> {source_node, target_node, source_port, target_port}
        self._build_network()
    
    def _build_network(self):
        """Build the module network from configuration."""
        # Create module instances
        for node in self.config.nodes:
            module_instance = self._create_module_instance(node)
            self.modules[node.id] = module_instance
        
        # Build edge mapping
        for edge in self.config.edges:
            self.edge_map[edge.id] = {
                'source_node': edge.source,
                'target_node': edge.target,
                'source_port': edge.sourcePort,
                'target_port': edge.targetPort
            }
        
        # Determine execution order (topological sort)
        self.execution_order = self._topological_sort()
    
    def _create_module_instance(self, node) -> ModuleInstance:
        """Create a BSM2 module instance based on node configuration."""
        # Import initialization parameters
        import bsm2_python.bsm2.init.asm1init_bsm2 as asm1init
        import bsm2_python.bsm2.init.primclarinit_bsm2 as primclarinit
        import bsm2_python.bsm2.init.settler1dinit_bsm2 as settler1dinit
        import bsm2_python.bsm2.init.thickenerinit_bsm2 as thickenerinit
        import bsm2_python.bsm2.init.adm1init_bsm2 as adm1init
        import bsm2_python.bsm2.init.dewateringinit_bsm2 as dewateringinit
        import bsm2_python.bsm2.init.storageinit_bsm2 as storageinit
        
        # Default parameters from node config
        params = node.parameters.copy()
        
        if node.type == ModuleType.PRIMARY_CLARIFIER:
            volume = params.get('volume', primclarinit.VOL_P)
            area = params.get('area', primclarinit.A_P)
            height = params.get('height', primclarinit.H_P)
            module = PrimaryClarifier(volume, area, height, primclarinit.X_I, primclarinit.X_S, 
                                    primclarinit.X_BH, primclarinit.X_BA, primclarinit.X_P)
        
        elif node.type == ModuleType.ASM1_REACTOR:
            volume = params.get('volume', asm1init.V_R1)
            kla = params.get('kla', asm1init.KLA1)
            temp = params.get('temperature', 15.0)
            module = ASM1Reactor(volume)
            module.kla = kla
        
        elif node.type == ModuleType.SETTLER:
            area = params.get('area', settler1dinit.AS)
            height = params.get('height', settler1dinit.H_S)
            module = Settler(area, height, settler1dinit.X_MIN, settler1dinit.F_NS, 
                           settler1dinit.V_DN, settler1dinit.V_UP, settler1dinit.X_TH, 
                           settler1dinit.F_TH, settler1dinit.R_H, settler1dinit.R_P, 
                           settler1dinit.F_UP, settler1dinit.N_LAYER, settler1dinit.LAYER)
        
        elif node.type == ModuleType.THICKENER:
            area = params.get('area', thickenerinit.A_TH)
            module = Thickener(area, thickenerinit.Q_TH, thickenerinit.N_TH, 
                             thickenerinit.X_TH_MIN, thickenerinit.R_TH)
        
        elif node.type == ModuleType.ADM1_REACTOR:
            volume = params.get('volume', adm1init.V_AD)
            temp = params.get('temperature', 35.0)
            module = ADM1Reactor(volume, temp)
        
        elif node.type == ModuleType.DEWATERING:
            module = Dewatering(dewateringinit.QDW, dewateringinit.N_DW, dewateringinit.X_DW_MIN)
        
        elif node.type == ModuleType.STORAGE:
            volume = params.get('volume', storageinit.V_ST)
            module = Storage(volume)
        
        elif node.type == ModuleType.SPLITTER:
            split_ratio = params.get('split_ratio', [0.5, 0.5])
            module = Splitter(sp_type=1)  # Custom splitter
        
        elif node.type == ModuleType.COMBINER:
            module = Combiner()
        
        else:
            raise ValueError(f"Unsupported module type: {node.type}")
        
        return ModuleInstance(node.id, node.type, module, params)
    
    def _topological_sort(self) -> List[str]:
        """Determine the execution order using topological sort."""
        # Build dependency graph
        dependencies = {node_id: set() for node_id in self.modules.keys()}
        
        for edge in self.config.edges:
            dependencies[edge.target].add(edge.source)
        
        # Kahn's algorithm
        execution_order = []
        no_deps = [node_id for node_id, deps in dependencies.items() if not deps]
        
        while no_deps:
            node = no_deps.pop()
            execution_order.append(node)
            
            # Remove this node from all dependency lists
            for dependent, deps in dependencies.items():
                if node in deps:
                    deps.remove(node)
                    if not deps and dependent not in execution_order:
                        no_deps.append(dependent)
        
        if len(execution_order) != len(self.modules):
            raise ValueError("Circular dependency detected in plant configuration")
        
        return execution_order


class SimulationEngine:
    """Main simulation engine that orchestrates BSM2 simulations."""
    
    def __init__(self):
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
        self.simulation_lock = threading.Lock()
    
    def validate_plant_configuration(self, config: PlantConfiguration) -> ValidationResult:
        """Validate a plant configuration for correctness."""
        errors = []
        warnings = []
        
        # Check for empty configuration
        if not config.nodes:
            errors.append("Plant configuration must contain at least one module")
        
        # Check for unique node IDs
        node_ids = [node.id for node in config.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("All module IDs must be unique")
        
        # Validate edges reference existing nodes
        for edge in config.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge {edge.id} references non-existent source node {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge {edge.id} references non-existent target node {edge.target}")
        
        # Check for circular dependencies
        try:
            network = PlantNetwork(config)
        except ValueError as e:
            errors.append(str(e))
        
        # Check for isolated nodes (warning)
        connected_nodes = set()
        for edge in config.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        isolated_nodes = set(node_ids) - connected_nodes
        if isolated_nodes:
            warnings.append(f"Isolated nodes detected: {', '.join(isolated_nodes)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def run_simulation(self, simulation_id: str, config: PlantConfiguration, params: SimulationParameters):
        """Run a simulation in a background thread."""
        try:
            with self.simulation_lock:
                self.active_simulations[simulation_id] = {
                    'status': SimulationStatus(
                        simulation_id=simulation_id,
                        status='starting',
                        progress=0.0,
                        current_time=0.0,
                        started_at=datetime.now().isoformat()
                    ),
                    'network': None,
                    'timestep_data': [],
                    'latest_data': None,
                    'thread': threading.current_thread()
                }
            
            # Build the plant network
            network = PlantNetwork(config)
            
            with self.simulation_lock:
                self.active_simulations[simulation_id]['network'] = network
                self.active_simulations[simulation_id]['status'].status = 'running'
            
            # Run simulation timesteps
            timesteps = np.arange(0, params.endtime, params.timestep)
            
            for i, current_time in enumerate(timesteps):
                # Check if simulation was cancelled
                with self.simulation_lock:
                    if self.active_simulations[simulation_id]['status'].status == 'cancelled':
                        return
                
                # Execute one timestep
                timestep_data = self._execute_timestep(network, i, current_time, params)
                
                # Update simulation status
                progress = (i + 1) / len(timesteps) * 100
                
                with self.simulation_lock:
                    sim_data = self.active_simulations[simulation_id]
                    sim_data['status'].progress = progress
                    sim_data['status'].current_time = current_time
                    sim_data['timestep_data'].append(timestep_data)
                    
                    # Update latest data every N timesteps
                    if i % params.update_frequency == 0:
                        sim_data['latest_data'] = timestep_data
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.001)
            
            # Mark simulation as completed
            with self.simulation_lock:
                self.active_simulations[simulation_id]['status'].status = 'completed'
                self.active_simulations[simulation_id]['status'].progress = 100.0
        
        except Exception as e:
            with self.simulation_lock:
                if simulation_id in self.active_simulations:
                    self.active_simulations[simulation_id]['status'].status = 'failed'
                    self.active_simulations[simulation_id]['status'].message = str(e)
    
    def _execute_timestep(self, network: PlantNetwork, timestep: int, current_time: float, 
                         params: SimulationParameters) -> TimestepData:
        """Execute a single simulation timestep."""
        # Initialize influent data (simplified - using BSM2 default)
        influent = self._get_influent_data(current_time)
        
        # Execute modules in topological order
        edge_flows = []
        
        for node_id in network.execution_order:
            module = network.modules[node_id]
            
            # Collect inputs for this module
            inputs = self._collect_module_inputs(module, network, influent)
            
            # Execute module
            if hasattr(module.bsm2_module, 'output'):
                if module.module_type in [ModuleType.ASM1_REACTOR, ModuleType.ADM1_REACTOR]:
                    # Reactors need timestep information
                    output = module.bsm2_module.output(params.timestep, current_time, inputs[0])
                else:
                    # Other modules
                    if len(inputs) == 1:
                        output = module.bsm2_module.output(inputs[0])
                    else:
                        output = module.bsm2_module.output(*inputs)
                
                # Store outputs
                module.outputs = {'default': output if isinstance(output, np.ndarray) else output[0]}
        
        # Collect edge flow data
        for edge in network.config.edges:
            source_module = network.modules[edge.source]
            if 'default' in source_module.outputs:
                flow_data = EdgeFlowData(
                    edge_id=edge.id,
                    timestep=timestep,
                    time=current_time,
                    components=self._array_to_components(source_module.outputs['default'])
                )
                edge_flows.append(flow_data)
        
        # Calculate performance metrics (simplified)
        performance = PerformanceMetrics(
            IQI=0.0,  # Would calculate from influent
            EQI=0.0,  # Would calculate from effluent
            OCI=0.0,  # Would calculate from costs
            aeration_energy=0.0,
            pumping_energy=0.0,
            mixing_energy=0.0
        )
        
        return TimestepData(
            timestep=timestep,
            time=current_time,
            edge_flows=edge_flows,
            performance=performance
        )
    
    def _get_influent_data(self, current_time: float) -> np.ndarray:
        """Get influent data for the current time (simplified default data)."""
        # This would normally read from the BSM2 influent file
        # For now, return constant default values
        return np.array([
            30.0,    # SI - Soluble inert organic matter
            69.5,    # SS - Readily biodegradable substrate  
            51.2,    # XI - Particulate inert organic matter
            202.32,  # XS - Slowly biodegradable substrate
            0.0,     # XBH - Active heterotrophic biomass
            0.0,     # XBA - Active autotrophic biomass
            0.0,     # XP - Particulate products from biomass decay
            0.0,     # SO - Oxygen
            0.0,     # SNO - Nitrate and nitrite nitrogen
            16.0,    # SNH - Ammonium nitrogen
            6.95,    # SND - Soluble biodegradable organic nitrogen
            10.59,   # XND - Particulate biodegradable organic nitrogen
            7.0,     # SALK - Alkalinity
            0.0,     # TSS - Total suspended solids (calculated)
            18446.0, # Q - Flow rate [m³/d]
            15.0,    # TEMP - Temperature [°C]
            0.0,     # SD1 - Dummy state 1
            0.0,     # SD2 - Dummy state 2
            0.0,     # SD3 - Dummy state 3
            0.0,     # XD4 - Dummy state 4
            0.0      # XD5 - Dummy state 5
        ])
    
    def _collect_module_inputs(self, module: ModuleInstance, network: PlantNetwork, 
                             influent: np.ndarray) -> List[np.ndarray]:
        """Collect inputs for a module from connected edges or influent."""
        inputs = []
        
        # Find edges that target this module
        input_edges = [edge for edge in network.config.edges if edge.target == module.node_id]
        
        if not input_edges:
            # No input edges, use influent data
            inputs.append(influent)
        else:
            # Collect inputs from source modules
            for edge in input_edges:
                source_module = network.modules[edge.source]
                if 'default' in source_module.outputs:
                    inputs.append(source_module.outputs['default'])
                else:
                    # If source hasn't been executed yet, use influent
                    inputs.append(influent)
        
        return inputs if inputs else [influent]
    
    def _array_to_components(self, arr: np.ndarray) -> ComponentData:
        """Convert numpy array to ComponentData."""
        if len(arr) < 16:
            # Pad with zeros if array is too short
            padded = np.zeros(21)
            padded[:len(arr)] = arr
            arr = padded
        
        return ComponentData(
            SI=float(arr[0]),
            SS=float(arr[1]),
            XI=float(arr[2]),
            XS=float(arr[3]),
            XBH=float(arr[4]),
            XBA=float(arr[5]),
            XP=float(arr[6]),
            SO=float(arr[7]),
            SNO=float(arr[8]),
            SNH=float(arr[9]),
            SND=float(arr[10]),
            XND=float(arr[11]),
            SALK=float(arr[12]),
            TSS=float(arr[13]) if len(arr) > 13 else 0.0,
            Q=float(arr[14]) if len(arr) > 14 else 0.0,
            TEMP=float(arr[15]) if len(arr) > 15 else 15.0
        )
    
    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationStatus]:
        """Get the current status of a simulation."""
        with self.simulation_lock:
            if simulation_id not in self.active_simulations:
                return None
            return self.active_simulations[simulation_id]['status']
    
    def get_latest_data(self, simulation_id: str) -> Optional[TimestepData]:
        """Get the latest simulation data."""
        with self.simulation_lock:
            if simulation_id not in self.active_simulations:
                return None
            return self.active_simulations[simulation_id]['latest_data']
    
    def get_simulation_results(self, simulation_id: str) -> Optional[SimulationResult]:
        """Get complete simulation results."""
        with self.simulation_lock:
            if simulation_id not in self.active_simulations:
                return None
            
            sim_data = self.active_simulations[simulation_id]
            if sim_data['status'].status != 'completed':
                return None
            
            # Return complete results (simplified)
            return SimulationResult(
                simulation_id=simulation_id,
                plant_config=sim_data['network'].config,
                simulation_params=SimulationParameters(),  # Would store actual params
                timesteps=sim_data['timestep_data'],
                final_performance=sim_data['timestep_data'][-1].performance if sim_data['timestep_data'] else PerformanceMetrics(IQI=0, EQI=0, OCI=0, aeration_energy=0, pumping_energy=0, mixing_energy=0),
                completed_at=datetime.now().isoformat()
            )
    
    def cancel_simulation(self, simulation_id: str) -> bool:
        """Cancel a running simulation."""
        with self.simulation_lock:
            if simulation_id not in self.active_simulations:
                return False
            
            self.active_simulations[simulation_id]['status'].status = 'cancelled'
            return True