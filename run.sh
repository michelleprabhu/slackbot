#!/bin/bash

# Strategic Planning Intelligence - Execution Script
# This script ensures the correct environment is activated and the app runs from the project root.

# Get the directory where the script is located
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment (venv) not found."
    echo "Please create it first using: python3 -m venv venv"
    exit 1
fi

# Function to display usage
usage() {
    echo "Usage: ./run.sh [webhook|dashboard|tests]"
    echo ""
    echo "Commands:"
    echo "  webhook    Start the FastAPI Webhook Receiver"
    echo "  dashboard  Start the Streamlit AI Classifier Dashboard"
    echo "  tests      Run the test suite using pytest"
    echo ""
}

# Process command
case "$1" in
    webhook)
        echo "Starting EPM Webhook Receiver..."
        ./venv/bin/python day1_slack_alert/webhook_receiver.py
        ;;
    dashboard)
        echo "Starting Strategic Classifier Dashboard..."
        ./venv/bin/python -m streamlit run day30_ticket_classifier/app.py
        ;;
    tests)
        echo "Running Test Suite..."
        ./venv/bin/python -m pytest
        ;;
    *)
        usage
        exit 1
        ;;
esac
