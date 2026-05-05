import discord
from discord import app_commands
from discord.ext import commands
import httpx

PLAYBOOKS = ["restart-grafana", "restart-elasticsearch", "restart-prometheus",
              "clear-disk-cache", "restart-pihole"]

class WatchTowerCog(commands.Cog):
    def __init__(self, bot, api_url, admin_id, channel_id):
        self.bot = bot
        self.api = api_url
        self.admin_id = admin_id
        self.channel_id = channel_id

    async def _get(self, path: str):
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(f"{self.api}{path}")
            r.raise_for_status()
            return r.json()

    # ─── /ping ───────────────────────────────────────────────
    @app_commands.command(name="ping", description="Check if WatchTower API is reachable")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(f"{self.api}/health")
            color = 0x57f287 if r.status_code == 200 else 0xed4245
            status = "🟢 Online" if r.status_code == 200 else "🔴 Error"
        except:
            color, status = 0xed4245, "🔴 Unreachable"
        embed = discord.Embed(title="WatchTower API Status", color=color)
        embed.add_field(name="API", value=self.api, inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        await interaction.followup.send(embed=embed)

    # ─── /status ─────────────────────────────────────────────
    @app_commands.command(name="status", description="Show CPU/RAM/disk for all WatchTower VMs")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            data = await self._get("/metrics/all")
            embed = discord.Embed(title="📊 WatchTower — System Status", color=0x5865F2)
            for svc in data.get("services", []):
                icon = "🟢" if svc.get("online") else "🔴"
                val = (f"CPU: {svc.get('cpu','—')}% | "
                       f"RAM: {svc.get('ram','—')}% | "
                       f"Disk: {svc.get('disk','—')}%")
                embed.add_field(name=f"{icon} {svc['name']}", value=val, inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error fetching metrics: {e}")

    # ─── /alerts ─────────────────────────────────────────────
    @app_commands.command(name="alerts", description="List active Grafana alerts")
    async def alerts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            data = await self._get("/metrics/alerts")
            alerts_list = data.get("alerts", [])
            if not alerts_list:
                await interaction.followup.send("✅ No active alerts — all systems normal!")
                return
            embed = discord.Embed(title=f"🚨 Active Alerts ({len(alerts_list)})", color=0xed4245)
            for a in alerts_list[:10]:
                embed.add_field(name=a.get("name","Unknown"),
                                value=f"State: {a.get('state','?')} | {a.get('summary','')}",
                                inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ {e}")

    # ─── /vms ────────────────────────────────────────────────
    @app_commands.command(name="vms", description="Show Proxmox VM registry status")
    async def vms(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            data = await self._get("/metrics/vms")
            embed = discord.Embed(title="🖥️ Proxmox VM Registry", color=0x5865F2)
            for vm in data.get("vms", []):
                icon = "🟢" if vm.get("online") else "🔴"
                embed.add_field(name=f"{icon} {vm['name']}",
                                value=f"IP: {vm.get('ip','?')} | VLAN: {vm.get('vlan','?')}",
                                inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ {e}")

    # ─── /backup ─────────────────────────────────────────────
    @app_commands.command(name="backup", description="Show last backup status and timestamp")
    async def backup(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            data = await self._get("/metrics/activity")
            embed = discord.Embed(title="💾 Backup Status", color=0xfee75c)
            embed.add_field(name="Last Backup", value=data.get("last_backup", "Unknown"), inline=True)
            embed.add_field(name="Status", value=data.get("backup_status", "Unknown"), inline=True)
            embed.add_field(name="Destination", value="Google Drive (gdrive:WatchTower-Backups)", inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ {e}")

    # ─── /trigger ────────────────────────────────────────────
    @app_commands.command(name="trigger", description="[ADMIN] Run an Ansible playbook via WatchTower")
    @app_commands.describe(playbook="Choose a playbook to run")
    @app_commands.choices(playbook=[app_commands.Choice(name=p, value=p) for p in PLAYBOOKS])
    async def trigger(self, interaction: discord.Interaction, playbook: str):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Admin only command.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            async with httpx.AsyncClient(timeout=30.0) as c:
                r = await c.post(f"{self.api}/ansible/trigger",
                                  json={"playbook": playbook, "triggered_by": "discord"})
            embed = discord.Embed(title="⚙️ Ansible Playbook Triggered", color=0x57f287)
            embed.add_field(name="Playbook", value=f"```{playbook}```", inline=False)
            embed.add_field(name="Triggered by", value=str(interaction.user), inline=True)
            embed.add_field(name="Status", value="🚀 Running on Ansible VM (192.168.40.10)", inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to trigger playbook: {e}")
