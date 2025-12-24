# Strategy Intelligence Platform

Adaptive automation tools for Strategic Planning and Enterprise Performance Management (EPM), designed with a "Simplicity-First" philosophy.

## Overview

This repository features advanced automation modules optimized for high-stakes planning environments:

1.  **EPM Intelligence Alerts**
    *   **Purpose**: Real-time strategic incident monitoring (e.g., Budget Forecast Variance, Data Integration Failures).
    *   **Technology**: FastAPI (Secure Webhooks), Async Slack notifications.
    *   **Location**: `day1_slack_alert/`

2.  **Strategic Ticket Classifier**
    *   **Purpose**: AI-powered synthesis and categorization of support tickets specializing in Data Integration and Planning Logic.
    *   **Philosophy**: Simplicity-focused UI for executive decision support.
    *   **Technology**: Streamlit, OpenAI, Interactive Plotly Visualizations.
    *   **Location**: `day30_ticket_classifier/`

## Getting Started

### Prerequisites

*   Python 3.8+
*   Virtual environment (recommended)

### Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure environment variables in `day1_slack_alert/.env`:
    *   `SLACK_WEBHOOK_URL`: Your Slack App Webhook URL.
    *   `OPENAI_API_KEY`: Your OpenAI API Key (optional, defaults to mock AI).

### How to Test

### 1. The Strategic Dashboard
Run `./run.sh dashboard` and upload `day30_ticket_classifier/sample_tickets.csv` in the **Ingestion Hub** tab.

### 2. The Intelligence Alerts
Run `./run.sh webhook` and, in another terminal, run `./venv/bin/python tests/test_webhook.py`.

### 3. Automated Tests
Run `./run.sh tests` to execute the full test suite.

## Directory Structure
- `day1_slack_alert/`: Webhook receiver and Slack integration logic.
- `day30_ticket_classifier/`: AI classification logic and Streamlit UI.
- `tests/`: Automated test suite.
- `run.sh`: Unified execution script for the entire platform.
- `requirements.txt`: Python dependencies.

---
*Built for Strategic Planning Excellence*
