import os
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DiscordBot")

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MassDMBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("--> SYNCING SLASH COMMANDS...")
        await self.tree.sync()
        print("--> SLASH COMMANDS SYNCED SUCCESSFULLY!")

    async def on_ready(self):
        print("==========================================")
        print(f"SUCCESS: Logged in as {self.user} (ID: {self.user.id})")
        print("==========================================")
        
        # Updated Rich Presence Status: Listening to Anna The Nuker
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="Anna The Nuker"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        print("--> STATUS UPDATED TO: Listening to Anna The Nuker")

bot = MassDMBot()

@bot.tree.command(name="dmall", description="Send a direct message to all members in the server (Owner Only).")
@app_commands.describe(
    message="The normal text message to send to all server members.",
    delay="Delay between each message in seconds (default: 3 seconds)."
)
async def dmall(interaction: discord.Interaction, message: str, delay: float = 3.0):
    # Strict Owner Check
    if interaction.user.id != interaction.guild.owner_id:
        embed = discord.Embed(
            title="⛔ Access Denied",
            description="Only the **Server Owner** can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Acknowledge command privately to owner
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    members = [m for m in guild.members if not m.bot]
    total_members = len(members)

    init_embed = discord.Embed(
        title="📢 Mass Direct Message Operation Started",
        description=f"Sending message to **{total_members}** members with a delay of **{delay}s** per user.",
        color=discord.Color.blue()
    )
    init_embed.add_field(name="Server", value=guild.name, inline=True)
    init_embed.add_field(name="Total Target Users", value=str(total_members), inline=True)
    await interaction.followup.send(embed=init_embed, ephemeral=True)

    successful = 0
    failed = 0

    for member in members:
        try:
            # Plain normal text message (No Embed)
            await member.send(message)
            successful += 1
            print(f"Sent normal DM to {member}")
        except Exception as e:
            failed += 1
            print(f"Failed to send DM to {member}: {e}")

        await asyncio.sleep(delay)

    # Final Summary Embed for Owner
    summary_embed = discord.Embed(
        title="✅ Mass DM Operation Completed",
        color=discord.Color.green()
    )
    summary_embed.add_field(name="Targeted Members", value=str(total_members), inline=False)
    summary_embed.add_field(name="Successfully Sent", value=f"```yaml\n{successful}\n```", inline=True)
    summary_embed.add_field(name="Failed / DMs Closed", value=f"```yaml\n{failed}\n```", inline=True)
    
    await interaction.followup.send(embed=summary_embed, ephemeral=True)

if __name__ == "__main__":
    print("--> BOT STARTING UP...")
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("CRITICAL ERROR: DISCORD_TOKEN IS MISSING!")
        exit(1)
    
    bot.run(token)
