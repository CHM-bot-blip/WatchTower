import httpx, os
from datetime import datetime

BOT_TOKEN   = os.getenv("BOT_TOKEN")
ADMIN_ID    = os.getenv("ADMIN_CHAT_ID")
TG_API      = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

async def send_alert_to_telegram(alert_data: dict):
    """Convert Grafana alert payload → Telegram message and push to admin."""
    state     = alert_data.get("state", "alerting")
    is_firing = state == "alerting"
    icon      = "🚨 ALERT FIRING" if is_firing else "✅ ALERT RESOLVED"
    title     = alert_data.get("title", "Unknown Alert")
    rule      = alert_data.get("ruleName", "—")
    msg       = alert_data.get("message", "No description")
    now       = datetime.utcnow().strftime("%H:%M UTC")

    text = (
        f"{icon}\n"
        "━━━━━━━━━━━━━━\n"
        f"📋 *Rule:* {rule}\n"
        f"💬 *Message:* {msg}\n"
        f"⏰ *Time:* {now}\n"
    )
    if is_firing:
        text += "\nUse /trigger to auto-remediate via Ansible"

    payload = {
        "chat_id":    ADMIN_ID,
        "text":       text,
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient() as client:
        await client.post(TG_API, json=payload)
