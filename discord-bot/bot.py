import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_ID  = int(os.getenv("CHANNEL_ID"))
API_URL     = os.getenv("WATCHTOWER_API", "http://192.168.40.100:8000")
ADMIN_ID    = int(os.getenv("ADMIN_DISCORD_ID", 0))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()  # register slash commands globally
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🟢 WatchTower Bot Online",
            description=f"Monitoring **{len(bot.guilds)}** server(s)",
            color=0x57f287
        )
        embed.add_field(name="API", value=API_URL, inline=True)
        embed.add_field(name="Commands", value="/status /alerts /vms /trigger /backup /ping", inline=False)
        await channel.send(embed=embed)
    print(f"✅ WatchTower Bot ready as {bot.user}")

# Load commands cog
async def main():
    async with bot:
        from commands import WatchTowerCog
        await bot.add_cog(WatchTowerCog(bot, API_URL, ADMIN_ID, CHANNEL_ID))
        await bot.start(BOT_TOKEN)

import asyncio
asyncio.run(main())
