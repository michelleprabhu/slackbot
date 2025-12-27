import httpx
import json
import os
import logging
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("slack_notifier")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Get Slack webhook URL from environment
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
MAX_RETRIES = 3

async def send_slack_alert_async(incident_title: str, impact_level: str, details: str, system_area: str = "General Planning", impact_value: float = 0):
    """Send formatted alert to Slack channel for EPM incidents"""
    
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured. Alert not sent.")
        return False
    
    # Format currency
    formatted_val = f"${impact_value:,.0f}" if impact_value > 0 else "N/A"

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"EPM Intelligence: {incident_title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Impact Level:*\n{impact_level}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Strategic $VAR:*\n{formatted_val}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*System Area:*\n{system_area}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Detection Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Incident Details:*\n{details}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Planning Model",
                            "emoji": True
                        },
                        "style": "primary",
                        "url": "https://planning-dashboard.aiops-platform.io/hub" # Generic EPM hub
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Rerun Integration",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": f"rerun_{system_area.lower().replace(' ', '_')}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "AIOps Platform | Strategic Decision Support"
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Sending Slack alert for {incident_title} (Attempt {attempt+1}/{MAX_RETRIES})")
                
                response = await client.post(
                    SLACK_WEBHOOK_URL,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                logger.info("Slack alert sent successfully.")
                return True

            except httpx.HTTPError as e:
                logger.error(f"Failed to send Slack alert (Attempt {attempt+1}): {str(e)}")
                backoff_time = (2 ** attempt) * 0.1
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                import asyncio
                await asyncio.sleep(backoff_time)

    logger.error(f"Failed to send Slack alert after {MAX_RETRIES} attempts")
    return False

def send_slack_alert(incident_title: str, impact_level: str, details: str):
    """Synchronous wrapper for send_slack_alert_async"""
    import asyncio
    return asyncio.run(send_slack_alert_async(incident_title, impact_level, details))

# For testing
if __name__ == "__main__":
    print("Testing EPM Slack notification...")
    result = send_slack_alert(
        incident_title="Data Integration: Platform Sync",
        impact_level="Critical",
        details="API timeout during nightly forecast refresh."
    )
    print(f"Result: {'Success' if result else 'Failed'}")
