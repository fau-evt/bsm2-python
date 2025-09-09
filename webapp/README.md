# BSM2 Wastewater Treatment Plant Web Application

A modern web-based application for designing and simulating wastewater treatment plants using the BSM2 (Benchmark Simulation Model No. 2) standard. Built with Next.js, React Flow, and FastAPI, integrating with the `bsm2-python` library for accurate process modeling.

![BSM2 Web App Screenshot](screenshots/bsm2_webapp_initial.png)

## 🌟 Features

### Visual Plant Designer
- **Drag-and-drop interface** for creating wastewater treatment plant layouts
- **8 BSM2 module types**: Primary clarifier, ASM1 reactors, settler, thickener, ADM1 reactor, dewatering, splitter, combiner
- **Visual connections** between modules with proper port mapping
- **Parameter configuration** for each module with realistic defaults
- **Plant templates** including full BSM2 standard layout and simple activated sludge

### Real-time Simulation
- **Dynamic simulation engine** using actual BSM2 mathematical models
- **Live data streaming** with Server-Sent Events
- **Real-time visualization** of simulation progress and results
- **Performance monitoring** with IQI, EQI, and OCI indices
- **Energy consumption tracking** (aeration, pumping, mixing)

### Advanced Visualization
- **Multiple chart types**: Line charts, area charts, performance metrics
- **Water quality tracking**: COD, nitrogen compounds, flow rates
- **Time-series data** showing plant behavior over simulation period
- **Summary statistics** and current operational status

## 🏗️ Architecture

```
webapp/
├── backend/           # FastAPI server
│   ├── main.py           # API endpoints and CORS configuration
│   ├── models.py         # Pydantic data models
│   ├── simulation_engine.py  # BSM2 simulation orchestration
│   └── requirements.txt  # Python dependencies
└── frontend/          # Next.js application
    ├── src/
    │   ├── app/             # Next.js 13+ app directory
    │   ├── components/      # React components
    │   │   ├── PlantDesigner.tsx    # Main drag-drop interface
    │   │   ├── ModuleNode.tsx       # BSM2 module components
    │   │   ├── Sidebar.tsx          # Module palette and parameters
    │   │   ├── SimulationPanel.tsx  # Simulation control
    │   │   └── SimulationChart.tsx  # Data visualization
    │   └── types/           # TypeScript definitions
    └── package.json
```

### Technology Stack

**Backend:**
- **FastAPI** - Modern, fast Python web framework
- **Pydantic** - Data validation and serialization
- **NumPy** - Numerical computations
- **bsm2-python** - BSM2 process models integration

**Frontend:**
- **Next.js 15** - React framework with TypeScript
- **React Flow** - Interactive node-based UI
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization library
- **Lucide React** - Icon library

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ with `bsm2-python` installed
- Node.js 18+ and npm
- Modern web browser

### Installation

1. **Clone and install bsm2-python** (if not already done):
   ```bash
   git clone https://github.com/fau-evt/bsm2-python
   cd bsm2-python
   pip install -e .
   ```

2. **Start the backend server**:
   ```bash
   cd webapp/backend
   pip install -r requirements.txt
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the frontend** (in a new terminal):
   ```bash
   cd webapp/frontend
   npm install
   npm run dev
   ```

4. **Open your browser** to http://localhost:3000

### Alternative: Quick Start Script
```bash
chmod +x webapp/start_backend.sh
./webapp/start_backend.sh  # Terminal 1
cd webapp/frontend && npm run dev  # Terminal 2
```

## 🎯 How to Use

### 1. Design Your Plant
1. **Drag modules** from the left sidebar onto the canvas
2. **Connect modules** by dragging from output ports to input ports
3. **Configure parameters** by selecting a module and editing in the sidebar
4. **Use templates** for quick setup of standard layouts

### 2. Run Simulation
1. Click **"Run Simulation"** in the top toolbar
2. **Configure parameters**: timestep, duration, model options
3. **Monitor progress** with real-time status and progress bar
4. **View live results** in charts showing flow data and performance

### 3. Analyze Results
- **Flow rates** and component concentrations over time
- **Water quality indicators** (COD, nitrogen compounds)
- **Performance indices** (IQI, EQI, OCI)
- **Energy consumption** breakdown by type

## 📊 Available Modules

| Module | Description | Key Parameters |
|--------|-------------|----------------|
| **Primary Clarifier** | Removes settleable solids from raw wastewater | Volume, Area, Settling velocity |
| **ASM1 Reactor** | Activated sludge biological treatment | Volume, KLA (aeration), Temperature |
| **Secondary Clarifier** | Separates treated water from activated sludge | Area, Depth, Settling parameters |
| **Sludge Thickener** | Concentrates waste sludge | Area, Solids flux |
| **Anaerobic Digester** | Biogas production from organic sludge | Volume, Temperature, pH |
| **Dewatering Unit** | Removes water from digested sludge | Efficiency, Polymer dose |
| **Flow Splitter** | Divides flow into multiple streams | Split ratio |
| **Flow Combiner** | Combines multiple streams | - |

## 🔧 API Endpoints

### Plant Configuration
- `GET /api/modules` - Available module types and specifications
- `GET /api/templates` - Predefined plant layout templates

### Simulation Management
- `POST /api/simulations` - Start a new simulation
- `GET /api/simulations/{id}/status` - Get simulation status and progress
- `GET /api/simulations/{id}/stream` - Real-time data streaming (SSE)
- `GET /api/simulations/{id}/results` - Complete simulation results
- `DELETE /api/simulations/{id}` - Cancel running simulation

## 🧪 Example Plant Configurations

### Simple Activated Sludge Process
```json
{
  "nodes": [
    {"id": "r1", "type": "asm1_reactor", "position": {"x": 300, "y": 200}},
    {"id": "sc1", "type": "settler", "position": {"x": 500, "y": 200}}
  ],
  "edges": [
    {"id": "e1", "source": "r1", "target": "sc1", "sourcePort": "effluent", "targetPort": "mixed_liquor"},
    {"id": "e2", "source": "sc1", "target": "r1", "sourcePort": "return_sludge", "targetPort": "influent"}
  ]
}
```

### Full BSM2 Standard Layout
Complete plant with primary treatment, 5-reactor activated sludge, anaerobic digestion, and sludge handling (see template in app).

## 🔬 Simulation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Timestep** | 1 minute | Simulation time resolution |
| **Duration** | 7 days | Total simulation time |
| **Temperature Model** | False | Enable temperature-dependent kinetics |
| **Dummy States** | False | Activate additional state variables |
| **Update Frequency** | 10 steps | How often to stream data to frontend |

## 🚧 Development

### Backend Development
```bash
cd webapp/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload  # Auto-reload on changes
```

### Frontend Development
```bash
cd webapp/frontend
npm run dev    # Development server
npm run build  # Production build
npm run lint   # Code linting
```

### Adding New Modules
1. **Backend**: Add module type to `models.py` and implement in `simulation_engine.py`
2. **Frontend**: Add module definition to `Sidebar.tsx` and update `ModuleNode.tsx`
3. **Update** module color scheme and port configurations

## 📈 Performance Metrics

The application tracks several key performance indicators:

- **IQI** (Influent Quality Index) - Characterizes influent load
- **EQI** (Effluent Quality Index) - Measures treatment efficiency  
- **OCI** (Overall Cost Index) - Combines quality and operating costs
- **Energy consumption** - Aeration, pumping, and mixing energy
- **Flow rates** - Volumetric flow through each connection
- **Component concentrations** - All 21 BSM2 state variables

## 🛠️ Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure `bsm2-python` is installed: `pip install bsm2-python`
- Check Python version (3.10+ required)
- Verify all dependencies: `pip install -r requirements.txt`

**Frontend won't connect to backend:**
- Confirm backend is running on port 8000
- Check CORS configuration in `main.py`
- Verify API endpoints with `curl http://localhost:8000/api/modules`

**Simulation fails:**
- Ensure plant has at least one module
- Check for circular dependencies in connections
- Verify module parameters are within valid ranges

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript best practices in frontend
- Use Pydantic models for all API data structures
- Add tests for new simulation modules
- Update documentation for new features

## 📜 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](../LICENSE) file for details.

## 🔗 Related Projects

- **[bsm2-python](https://github.com/fau-evt/bsm2-python)** - Core BSM2 simulation library
- **[React Flow](https://reactflow.dev/)** - Node-based UI library
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework

## 📧 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the main bsm2-python documentation
- Contact the development team

---

**Built with ❤️ for the wastewater treatment community**