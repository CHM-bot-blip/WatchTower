import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

PLAYBOOKS = [
    "restart-grafana", "restart-prometheus",
    "restart-elasticsearch", "clear-disk-cache", "restart-pihole"
]

async def _get(api: str, path: str) -> dict:
    async with httpx.AsyncClient(timeout=8.0) as c:
        r = await c.get(f"{api}/api/v1{path}")
        r.raise_for_status()
        return r.json()

# ─── /ping ───────────────────────────────────────────────
async def cmd_ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    api = ctx.bot_data["api"]
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{api}/api/v1/metrics/all")
        icon = "🟢" if r.status_code == 200 else "🔴"
        status = "Online" if r.status_code == 200 else "Error"
    except:
        icon, status = "🔴", "Unreachable"
    await update.message.reply_text(
        f"{icon} *WatchTower API* — {status}\n`{api}`",
        parse_mode="Markdown")

# ─── /status ─────────────────────────────────────────────
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 All Services", callback_data="status:all")],
        [
            InlineKeyboardButton("pfSense", callback_data="status:pfsense"),
            InlineKeyboardButton("Grafana", callback_data="status:monitoring"),
        ],
        [
            InlineKeyboardButton("ELK", callback_data="status:elk"),
            InlineKeyboardButton("Ansible", callback_data="status:ansible"),
        ],
        [
            InlineKeyboardButton("FastAPI", callback_data="status:fastapi"),
            InlineKeyboardButton("Pi-hole", callback_data="status:pihole"),
        ],
        [
            InlineKeyboardButton("Backup", callback_data="status:backup"),
        ],
    ]
    await update.message.reply_text(
        "🖥️ *Which service do you want to check?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── Status callback ──────────────────────────────────────
async def handle_status_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target = query.data.split(":", 1)[1]
    try:
        data = await _get(ctx.bot_data["api"], "/metrics/all")
        lines = []

        if target == "all":
            lines.append("📊 *WatchTower — All Services*\n━━━━━━━━━━━━━━")
            for name, svc in data.items():
                if not isinstance(svc, dict):
                    continue
                icon = "🔴" if svc.get("error") else "🟢"
                lines.append(
                    f"{icon} *{name}*\n"
                    f"  CPU: {svc.get('cpu','—')}%  RAM: {svc.get('ram','—')}%  Disk: {svc.get('disk','—')}%"
                )
        else:
            svc = data.get(target)
            if not svc or not isinstance(svc, dict):
                await query.edit_message_text(f"❌ Service `{target}` not found in metrics.")
                return
            icon = "🔴" if svc.get("error") else "🟢"
            lines.append(f"📊 *{target.upper()} — Status*\n━━━━━━━━━━━━━━")
            lines.append(f"{icon} *Online:* {'No' if svc.get('error') else 'Yes'}")
            lines.append(f"⚙️ *CPU:*  {svc.get('cpu','—')}%")
            lines.append(f"🧠 *RAM:*  {svc.get('ram','—')}%")
            lines.append(f"💾 *Disk:* {svc.get('disk','—')}%")

        await query.edit_message_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

# ─── Alert timestamp tracker ──────────────────────────────
_alert_first_seen: dict[str, str] = {}

def _get_alert_ts(key: str) -> str:
    from datetime import datetime
    if key not in _alert_first_seen:
        _alert_first_seen[key] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return _alert_first_seen[key]

# ─── /alerts ─────────────────────────────────────────────
async def cmd_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        data = await _get(ctx.bot_data["api"], "/metrics/alerts")
        alerts_list = data.get("alerts", [])

        if not alerts_list:
            await update.message.reply_text("✅ No active alerts — all systems normal!")
            return

        # Clear resolved alerts from tracker
        current_keys = {
            f"{a.get('name','')}:{a.get('summary','')}"
            for a in alerts_list
        }
        for old_key in list(_alert_first_seen.keys()):
            if old_key not in current_keys:
                del _alert_first_seen[old_key]

        # Deduplicate by alert name + summary
        seen = set()
        unique = []
        for a in alerts_list:
            key = (a.get("name", ""), a.get("summary", ""))
            if key not in seen:
                seen.add(key)
                unique.append(a)

        # Group by alert name, store full alert objects
        groups = {}
        for a in unique:
            name = a.get("name", "Unknown")
            groups.setdefault(name, []).append(a)

        # Build message
        lines = ["🚨 *Active Alerts — " + str(len(unique)) + " unique*", "━━━━━━━━━━━━━━"]
        for name, alert_group in list(groups.items())[:8]:
            safe_name = name.replace("*", "").replace("_", "").replace("`", "")
            lines.append("")
            lines.append(f"🔴 *{safe_name}* ({len(alert_group)}x)")
            for a in alert_group[:2]:
                summary = a.get("summary", a.get("message", "—"))
                summary_safe = summary.replace("_", "\\_").replace("*", "")
                tracker_key = f"{name}:{summary}"
                ts = _get_alert_ts(tracker_key)
                lines.append(f"  `{summary_safe[:55]}`")
                lines.append(f"  🕐 Since: `{ts}`")

        if len(groups) > 8:
            lines.append("")
            lines.append(f"_...and {len(groups) - 8} more alert types_")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


# ─── /backup ─────────────────────────────────────────────
async def cmd_backup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        data = await _get(ctx.bot_data["api"], "/metrics/activity")
        text = (
            "💾 *Backup Status*\n━━━━━━━━━━━━━━\n"
            f"📅 Last: `{data.get('last_backup','Unknown')}`\n"
            f"✅ Status: {data.get('backup_status','Unknown')}\n"
            "☁️ Dest: `gdrive:WatchTower-Backups`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ─── /trigger ────────────────────────────────────────────
async def cmd_trigger(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ctx.bot_data["admin_id"]:
        await update.message.reply_text("❌ Admin only command.")
        return
    keyboard = [[InlineKeyboardButton(p, callback_data=f"playbook:{p}")] for p in PLAYBOOKS]
    await update.message.reply_text(
        "⚙️ *Choose a playbook to run:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── Button callback ─────────────────────────────────────
async def handle_trigger_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    playbook = query.data.split(":", 1)[1]
    try:
        async with httpx.AsyncClient(timeout=30.0) as c:
            await c.post(
                f"{ctx.bot_data['api']}/api/v1/ansible/trigger",
                json={"playbook": playbook, "triggered_by": "telegram"}
            )
        await query.edit_message_text(
            f"✅ *Playbook triggered!*\n`{playbook}`\nRunning on Ansible VM `192.168.40.10`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Failed: {e}")
