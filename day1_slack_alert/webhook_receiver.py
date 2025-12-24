from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from slack_notifier import send_slack_alert_async as send_slack_alert

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook_receiver")

# Security configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Initialize FastAPI app
app = FastAPI(
    title="AIOps EPM Incident Webhook",
    description="Webhook receiver for high-priority EPM and Strategic Planning alerts",
    version="2.0.0"
)

class EPMIncident(BaseModel):
    incident_title: str
    impact_level: str
    details: str

@app.post("/webhook/epm_incident")
async def handle_epm_incident(request: Request, incident: EPMIncident):
    """Handle incoming EPM planning incidents"""
    
    # Simple security check
    if WEBHOOK_SECRET:
        token = request.headers.get("X-Webhook-Token")
        if token != WEBHOOK_SECRET:
            logger.warning("Unauthorized webhook attempt detected")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Received EPM incident: {incident.incident_title}")
        
        # Log the incident
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "epm_incident",
            "title": incident.incident_title,
            "impact": incident.impact_level,
            "details": incident.details
        }
        
        logger.info(f"EPM incident details: {json.dumps(log_entry)}")
        
        # Send Slack alert
        success = await send_slack_alert(
            incident.incident_title,
            incident.impact_level,
            incident.details
        )
        
        if success:
            return {
                "status": "success",
                "message": "EPM Strategy Alert sent to Slack",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("Failed to send Slack alert")
            raise HTTPException(status_code=500, detail="Failed to send Slack alert")
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# For local testing
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting webhook receiver service")
    uvicorn.run("webhook_receiver:app", host="0.0.0.0", port=8000, reload=True)