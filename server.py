from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import io
import json
import os
import sys
from datetime import datetime

# Add project root to path for cross-day module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from day30_ticket_classifier.ticket_classifier import classify_tickets, generate_stats
from day1_slack_alert.slack_notifier import send_slack_alert_async

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (simplified for demo)
state = {
    "results": None,
    "stats": None,
    "slack_enabled": False
}

@app.get("/api/config")
async def get_config():
    return {
        "slack_enabled": state["slack_enabled"],
        "slack_configured": bool(os.getenv("SLACK_WEBHOOK_URL")),
        "uptime": "100.00%",
        "last_sync": datetime.now().strftime("%H:%M:%S")
    }

@app.post("/api/config/slack")
async def toggle_slack(enabled: bool):
    state["slack_enabled"] = enabled
    return {"status": "success", "slack_enabled": enabled}

@app.post("/api/classify")
async def classify(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        results_df = classify_tickets(df)
        stats = generate_stats(results_df)
        
        results_list = results_df.to_dict(orient="records")
        state["results"] = results_list
        state["stats"] = stats
        
        # Handle Slack
        if state["slack_enabled"]:
            high_priority = [r for r in results_list if r["ai_urgency"] == "High"]
            for row in high_priority:
                await send_slack_alert_async(
                    incident_title=f"Critical Risk: {row['customer']}",
                    impact_level="Critical",
                    details=row['ai_summary'],
                    system_area=row['ai_category'],
                    impact_value=row.get('ai_impact_score', 0)
                )
        
        return {
            "status": "success",
            "results": results_list,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dispatch-slack")
async def dispatch_slack(row: dict):
    # Manual dispatch ignores the state["slack_enabled"] toggle
    # because the user explicitly clicked the button.
    success = await send_slack_alert_async(
        incident_title=f"Manual Dispatch: {row['customer']}",
        impact_level="Critical" if row['ai_urgency'] == "High" else "Warning",
        details=row['ai_summary'],
        system_area=row['ai_category'],
        impact_value=row.get('ai_impact_score', 0)
    )
    if not success:
        raise HTTPException(status_code=500, detail="Slack delivery failed")
    return {"status": "success"}

@app.post("/api/test-slack")
async def test_slack():
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return {"status": "error", "message": "Webhook not configured"}
    
    success = await send_slack_alert_async(
        incident_title="System Connectivity Test", 
        impact_level="Info", 
        details="Diagnostic ping from Portal hub.",
        system_area="Portal Infrastructure"
    )
    return {"status": "success" if success else "error"}

# Serve static files and frontend
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("dashboard/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
