import os, asyncio
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from commands import cmd_ping, cmd_status, cmd_alerts, cmd_backup, cmd_trigger, handle_trigger_callback, handle_status_callback

load_dotenv()

BOT_TOKEN    = os.getenv("BOT_TOKEN")
ADMIN_ID     = int(os.getenv("ADMIN_CHAT_ID", "0"))
API_URL      = os.getenv("WATCHTOWER_API", "http://backend:8000")

async def post_init(app):
    # Send startup message to admin
    await app.bot.send_message(
        chat_id=ADMIN_ID,
        text="🟢 *WatchTower Bot Online*\n"
             f"API: `{API_URL}`\n"
             "Commands: /ping /status /alerts /vms /backup /trigger",
        parse_mode="Markdown"
    )

def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Inject shared config via bot_data
    app.bot_data["api"]      = API_URL
    app.bot_data["admin_id"] = ADMIN_ID

    # Register command handlers
    app.add_handler(CommandHandler("ping",    cmd_ping))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("alerts",  cmd_alerts))
    app.add_handler(CommandHandler("backup",  cmd_backup))
    app.add_handler(CommandHandler("trigger", cmd_trigger))

    # Inline keyboard button callback
    app.add_handler(CallbackQueryHandler(handle_trigger_callback, pattern=r"^playbook:"))
    app.add_handler(CallbackQueryHandler(handle_status_callback, pattern=r"^status:"))  
    print("✅ WatchTower Telegram Bot started (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
