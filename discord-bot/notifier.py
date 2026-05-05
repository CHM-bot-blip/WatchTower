import httpx
import asyncio
from datetime import datetime

# Called from FastAPI when Grafana webhook arrives
async def send_alert_to_discord(webhook_url: str, alert_data: dict):
    """Convert Grafana alert payload to a Discord embed and POST to webhook URL."""
    state = alert_data.get("state", "alerting")
    is_firing = state == "alerting"

    color  = 0xed4245 if is_firing else 0x57f287
    icon   = "🚨 ALERT FIRING" if is_firing else "✅ ALERT RESOLVED"
    title  = alert_data.get("title", "Unknown Alert")
    msg    = alert_data.get("message", "No description")
    rule   = alert_data.get("ruleName", "—")

    payload = {
        "embeds": [{
            "title": f"{icon} — {title}",
            "description": msg,
            "color": color,
            "fields": [
                {"name": "Rule",      "value": rule,              "inline": True},
                {"name": "State",     "value": state.upper(),     "inline": True},
                {"name": "Time",      "value": datetime.utcnow().strftime("%H:%M UTC"), "inline": True},
            ],
            "footer": {"text": "WatchTower · Grafana → FastAPI → Discord"}
        }]
    }
    if is_firing:
        payload["content"] = "@here"  # pings everyone for critical alerts

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
