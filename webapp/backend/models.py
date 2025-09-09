"""
Pydantic models for the BSM2 wastewater plant simulator API.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import numpy as np


class ModuleType(str, Enum):
    """Available module types in the BSM2 system."""
    PRIMARY_CLARIFIER = "primary_clarifier"
    ASM1_REACTOR = "asm1_reactor"
    SETTLER = "settler"
    THICKENER = "thickener"
    ADM1_REACTOR = "adm1_reactor"
    DEWATERING = "dewatering"
    SPLITTER = "splitter"
    COMBINER = "combiner"
    STORAGE = "storage"


class Position(BaseModel):
    """2D position coordinates for node placement."""
    x: float
    y: float


class ModuleNode(BaseModel):
    """Represents a single module/node in the plant configuration."""
    id: str = Field(..., description="Unique identifier for the module")
    type: ModuleType = Field(..., description="Type of the module")
    position: Position = Field(..., description="Position in the designer canvas")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Module-specific parameters")
    name: Optional[str] = Field(None, description="Human-readable name for the module")


class FlowEdge(BaseModel):
    """Represents a connection/pipe between two modules."""
    id: str = Field(..., description="Unique identifier for the edge")
    source: str = Field(..., description="ID of the source module")
    target: str = Field(..., description="ID of the target module")
    sourcePort: str = Field(..., description="Output port name on source module")
    targetPort: str = Field(..., description="Input port name on target module")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Edge-specific parameters like flow rates")


class PlantConfiguration(BaseModel):
    """Complete plant layout configuration."""
    nodes: List[ModuleNode] = Field(..., description="List of modules in the plant")
    edges: List[FlowEdge] = Field(..., description="List of connections between modules")
    influent_data: Optional[Dict[str, Any]] = Field(None, description="Influent data configuration")


class SimulationParameters(BaseModel):
    """Parameters controlling the simulation execution."""
    timestep: float = Field(1/24/60, description="Timestep in days (default: 1 minute)")
    endtime: float = Field(7.0, description="Simulation end time in days")
    tempmodel: bool = Field(False, description="Enable temperature modeling")
    activate_dummy: bool = Field(False, description="Activate dummy states")
    update_frequency: int = Field(10, description="Update frequency for streaming data (every N timesteps)")


class SimulationRequest(BaseModel):
    """Request to start a new simulation."""
    plant_config: PlantConfiguration = Field(..., description="Plant configuration")
    simulation_params: SimulationParameters = Field(default_factory=SimulationParameters, description="Simulation parameters")


class SimulationStatus(BaseModel):
    """Current status of a simulation."""
    simulation_id: str
    status: str = Field(..., description="Status: 'running', 'completed', 'failed', 'cancelled'")
    progress: float = Field(..., description="Progress percentage (0-100)")
    current_time: float = Field(..., description="Current simulation time")
    started_at: str = Field(..., description="Start timestamp")
    message: Optional[str] = Field(None, description="Status message or error description")


class ComponentData(BaseModel):
    """Data for a single component at a timestep."""
    SI: float = Field(..., description="Soluble inert organic matter [g COD/m³]")
    SS: float = Field(..., description="Readily biodegradable substrate [g COD/m³]")
    XI: float = Field(..., description="Particulate inert organic matter [g COD/m³]")
    XS: float = Field(..., description="Slowly biodegradable substrate [g COD/m³]")
    XBH: float = Field(..., description="Active heterotrophic biomass [g COD/m³]")
    XBA: float = Field(..., description="Active autotrophic biomass [g COD/m³]")
    XP: float = Field(..., description="Particulate products arising from biomass decay [g COD/m³]")
    SO: float = Field(..., description="Oxygen [g O₂/m³]")
    SNO: float = Field(..., description="Nitrate and nitrite nitrogen [g N/m³]")
    SNH: float = Field(..., description="Ammonium nitrogen [g N/m³]")
    SND: float = Field(..., description="Soluble biodegradable organic nitrogen [g N/m³]")
    XND: float = Field(..., description="Particulate biodegradable organic nitrogen [g N/m³]")
    SALK: float = Field(..., description="Alkalinity [mol HCO₃⁻/m³]")
    TSS: float = Field(..., description="Total suspended solids [g/m³]")
    Q: float = Field(..., description="Flow rate [m³/d]")
    TEMP: float = Field(..., description="Temperature [°C]")


class EdgeFlowData(BaseModel):
    """Flow data for a specific edge at a timestep."""
    edge_id: str = Field(..., description="Edge identifier")
    timestep: int = Field(..., description="Current timestep")
    time: float = Field(..., description="Current simulation time [d]")
    components: ComponentData = Field(..., description="Component concentrations and flow")


class PerformanceMetrics(BaseModel):
    """Performance metrics for the plant."""
    IQI: float = Field(..., description="Influent Quality Index")
    EQI: float = Field(..., description="Effluent Quality Index") 
    OCI: float = Field(..., description="Overall Cost Index")
    aeration_energy: float = Field(..., description="Aeration energy consumption [kWh/d]")
    pumping_energy: float = Field(..., description="Pumping energy consumption [kWh/d]")
    mixing_energy: float = Field(..., description="Mixing energy consumption [kWh/d]")


class TimestepData(BaseModel):
    """Complete data for a single simulation timestep."""
    timestep: int = Field(..., description="Timestep number")
    time: float = Field(..., description="Simulation time [d]")
    edge_flows: List[EdgeFlowData] = Field(..., description="Flow data for all edges")
    performance: PerformanceMetrics = Field(..., description="Performance metrics")


class SimulationResult(BaseModel):
    """Complete simulation results."""
    simulation_id: str
    plant_config: PlantConfiguration
    simulation_params: SimulationParameters
    timesteps: List[TimestepData] = Field(..., description="Results for each timestep")
    final_performance: PerformanceMetrics = Field(..., description="Final performance metrics")
    completed_at: str = Field(..., description="Completion timestamp")


class ValidationResult(BaseModel):
    """Result of plant configuration validation."""
    is_valid: bool = Field(..., description="Whether the configuration is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")