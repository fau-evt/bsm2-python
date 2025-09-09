#!/bin/bash

# Backend startup script for BSM2 Web Application

echo "Starting BSM2 Wastewater Plant Simulator Backend..."

# Install backend dependencies
echo "Installing Python dependencies..."
cd /home/runner/work/bsm2-python/bsm2-python/webapp/backend
pip install -r requirements.txt

# Add the main bsm2-python package to Python path
export PYTHONPATH="/home/runner/work/bsm2-python/bsm2-python:$PYTHONPATH"

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8000..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload