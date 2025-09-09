"""
FastAPI backend for BSM2 wastewater treatment plant simulation web application.

This backend provides:
- RESTful API for plant configuration
- Simulation orchestration using bsm2-python modules
- Real-time data streaming during simulation
- Node-edge connection logic for dynamic plant layouts
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
import uvicorn
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime
import uuid

from models import (
    PlantConfiguration,
    SimulationRequest,
    SimulationStatus,
    ModuleNode,
    FlowEdge,
    SimulationResult
)
from simulation_engine import SimulationEngine

app = FastAPI(
    title="BSM2 Wastewater Plant Simulator",
    description="Dynamic simulation of wastewater treatment plants using BSM2 models",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulation manager
simulation_engine = SimulationEngine()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "BSM2 Wastewater Plant Simulator API", "status": "running"}

@app.get("/api/modules")
async def get_available_modules():
    """Get list of available BSM2 modules for the plant designer."""
    return {
        "modules": [
            {
                "id": "primary_clarifier",
                "name": "Primary Clarifier",
                "type": "clarifier",
                "inputs": ["influent", "recycle_sludge"],
                "outputs": ["underflow", "overflow"],
                "parameters": ["volume", "area", "settling_velocity"],
                "description": "Removes settleable solids from raw wastewater"
            },
            {
                "id": "asm1_reactor",
                "name": "ASM1 Reactor",
                "type": "bioreactor",
                "inputs": ["influent"],
                "outputs": ["effluent"],
                "parameters": ["volume", "kla", "temperature"],
                "description": "Activated sludge biological treatment reactor"
            },
            {
                "id": "settler",
                "name": "Secondary Clarifier",
                "type": "clarifier", 
                "inputs": ["mixed_liquor"],
                "outputs": ["return_sludge", "waste_sludge", "effluent"],
                "parameters": ["area", "depth", "settling_parameters"],
                "description": "Separates treated water from activated sludge"
            },
            {
                "id": "thickener",
                "name": "Sludge Thickener",
                "type": "thickener",
                "inputs": ["waste_sludge"],
                "outputs": ["thickened_sludge"],
                "parameters": ["area", "solids_flux"],
                "description": "Concentrates waste sludge before further treatment"
            },
            {
                "id": "adm1_reactor",
                "name": "Anaerobic Digester",
                "type": "digester",
                "inputs": ["organic_sludge"],
                "outputs": ["biogas", "digested_sludge"],
                "parameters": ["volume", "temperature", "ph"],
                "description": "Anaerobic treatment of organic sludge with biogas production"
            },
            {
                "id": "dewatering",
                "name": "Dewatering Unit",
                "type": "dewatering",
                "inputs": ["digested_sludge"],
                "outputs": ["dewatered_cake", "filtrate"],
                "parameters": ["efficiency", "polymer_dose"],
                "description": "Removes water from digested sludge"
            },
            {
                "id": "splitter",
                "name": "Flow Splitter",
                "type": "utility",
                "inputs": ["inlet"],
                "outputs": ["outlet1", "outlet2"],
                "parameters": ["split_ratio"],
                "description": "Divides flow into multiple streams"
            },
            {
                "id": "combiner",
                "name": "Flow Combiner",
                "type": "utility",
                "inputs": ["inlet1", "inlet2"],
                "outputs": ["outlet"],
                "parameters": [],
                "description": "Combines multiple streams into one"
            }
        ]
    }

@app.post("/api/simulations")
async def create_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """Create and start a new simulation."""
    try:
        simulation_id = str(uuid.uuid4())
        
        # Validate plant configuration
        validation_result = simulation_engine.validate_plant_configuration(request.plant_config)
        if not validation_result.is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid plant configuration: {validation_result.errors}")
        
        # Start simulation in background
        background_tasks.add_task(
            simulation_engine.run_simulation,
            simulation_id,
            request.plant_config,
            request.simulation_params
        )
        
        return {
            "simulation_id": simulation_id,
            "status": "started",
            "message": "Simulation started successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")

@app.get("/api/simulations/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """Get the current status of a simulation."""
    try:
        status = simulation_engine.get_simulation_status(simulation_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get simulation status: {str(e)}")

@app.get("/api/simulations/{simulation_id}/stream")
async def stream_simulation_data(simulation_id: str):
    """Stream real-time simulation data."""
    
    async def generate_simulation_data():
        """Generator function for streaming simulation results."""
        while True:
            try:
                # Get latest simulation data
                data = simulation_engine.get_latest_data(simulation_id)
                if data is None:
                    break
                
                # Format as Server-Sent Events
                yield f"data: {json.dumps(data.dict())}\n\n"
                
                # Check if simulation is complete
                status = simulation_engine.get_simulation_status(simulation_id)
                if status and status.status in ["completed", "failed"]:
                    break
                    
                await asyncio.sleep(1)  # Update frequency
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        generate_simulation_data(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/api/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: str):
    """Get complete simulation results."""
    try:
        results = simulation_engine.get_simulation_results(simulation_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Simulation not found or not completed")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get simulation results: {str(e)}")

@app.delete("/api/simulations/{simulation_id}")
async def cancel_simulation(simulation_id: str):
    """Cancel a running simulation."""
    try:
        success = simulation_engine.cancel_simulation(simulation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")
        return {"message": "Simulation cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel simulation: {str(e)}")

@app.get("/api/templates")
async def get_plant_templates():
    """Get predefined plant configuration templates."""
    return {
        "templates": [
            {
                "id": "bsm2_standard",
                "name": "BSM2 Standard Layout",
                "description": "Standard BSM2 plant configuration with all components",
                "nodes": [
                    {"id": "pc1", "type": "primary_clarifier", "position": {"x": 100, "y": 200}},
                    {"id": "r1", "type": "asm1_reactor", "position": {"x": 300, "y": 200}},
                    {"id": "r2", "type": "asm1_reactor", "position": {"x": 400, "y": 200}},
                    {"id": "r3", "type": "asm1_reactor", "position": {"x": 500, "y": 200}},
                    {"id": "r4", "type": "asm1_reactor", "position": {"x": 600, "y": 200}},
                    {"id": "r5", "type": "asm1_reactor", "position": {"x": 700, "y": 200}},
                    {"id": "sc1", "type": "settler", "position": {"x": 850, "y": 200}},
                    {"id": "th1", "type": "thickener", "position": {"x": 850, "y": 400}},
                    {"id": "ad1", "type": "adm1_reactor", "position": {"x": 400, "y": 400}},
                    {"id": "dw1", "type": "dewatering", "position": {"x": 600, "y": 400}}
                ],
                "edges": [
                    {"id": "e1", "source": "pc1", "target": "r1", "sourcePort": "overflow", "targetPort": "influent"},
                    {"id": "e2", "source": "r1", "target": "r2", "sourcePort": "effluent", "targetPort": "influent"},
                    {"id": "e3", "source": "r2", "target": "r3", "sourcePort": "effluent", "targetPort": "influent"},
                    {"id": "e4", "source": "r3", "target": "r4", "sourcePort": "effluent", "targetPort": "influent"},
                    {"id": "e5", "source": "r4", "target": "r5", "sourcePort": "effluent", "targetPort": "influent"},
                    {"id": "e6", "source": "r5", "target": "sc1", "sourcePort": "effluent", "targetPort": "mixed_liquor"},
                    {"id": "e7", "source": "sc1", "target": "r1", "sourcePort": "return_sludge", "targetPort": "influent"},
                    {"id": "e8", "source": "sc1", "target": "th1", "sourcePort": "waste_sludge", "targetPort": "waste_sludge"},
                    {"id": "e9", "source": "th1", "target": "ad1", "sourcePort": "thickened_sludge", "targetPort": "organic_sludge"},
                    {"id": "e10", "source": "pc1", "target": "ad1", "sourcePort": "underflow", "targetPort": "organic_sludge"},
                    {"id": "e11", "source": "ad1", "target": "dw1", "sourcePort": "digested_sludge", "targetPort": "digested_sludge"}
                ]
            },
            {
                "id": "simple_as",
                "name": "Simple Activated Sludge",
                "description": "Basic activated sludge process with single reactor",
                "nodes": [
                    {"id": "r1", "type": "asm1_reactor", "position": {"x": 300, "y": 200}},
                    {"id": "sc1", "type": "settler", "position": {"x": 500, "y": 200}}
                ],
                "edges": [
                    {"id": "e1", "source": "r1", "target": "sc1", "sourcePort": "effluent", "targetPort": "mixed_liquor"},
                    {"id": "e2", "source": "sc1", "target": "r1", "sourcePort": "return_sludge", "targetPort": "influent"}
                ]
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)