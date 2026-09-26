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
        # Sync slash commands globally across all servers
        logger.info("Syncing slash commands...")
        await self.tree.sync()
        logger.info("Slash commands synced successfully.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Set custom Rich Presence / Bot Status showing "/dmall"
        activity = discord.Activity(
            type=discord.ActivityType.listening, # e.g. "Listening to /dmall"
            name="/dmall"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        logger.info("Bot status updated to: Listening to /dmall")

bot = MassDMBot()

@bot.tree.command(name="dmall", description="Send a direct message to all members in the server (Owner Only).")
@app_commands.describe(
    message="The message content to send to all server members.",
    delay="Delay between each message in seconds (default: 3 seconds to avoid rate limits)."
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

    # Acknowledge the command immediately to avoid timeout
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    members = [m for m in guild.members if not m.bot]
    total_members = len(members)

    # Initial Progress Embed
    init_embed = discord.Embed(
        title="📢 Mass Direct Message Operation Initiated",
        description=f"Sending message to **{total_members}** members with a delay of **{delay}s** per user.",
        color=discord.Color.blue()
    )
    init_embed.add_field(name="Server", value=guild.name, inline=True)
    init_embed.add_field(name="Total Target Users", value=str(total_members), inline=True)
    await interaction.followup.send(embed=init_embed, ephemeral=True)

    successful = 0
    failed = 0

    # User-facing DM Embed Template
    dm_embed = discord.Embed(
        title=f"Message from {guild.name}",
        description=message,
        color=discord.Color.gold()
    )
    if guild.icon:
        dm_embed.set_thumbnail(url=guild.icon.url)
    dm_embed.set_footer(text=f"Sent via {bot.user.name} | Server Owner Announcement")

    for member in members:
        try:
            await member.send(embed=dm_embed)
            successful += 1
            logger.info(f"Successfully delivered DM to {member} ({member.id})")
        except discord.Forbidden:
            failed += 1
            logger.warning(f"Failed to DM {member} ({member.id}): DMs closed or bot blocked.")
        except discord.HTTPException as e:
            failed += 1
            logger.error(f"HTTP error sending to {member} ({member.id}): {e}")
        except Exception as e:
            failed += 1
            logger.error(f"Unexpected error sending to {member} ({member.id}): {e}")

        # Rate Limit / Anti-Ban Delay
        await asyncio.sleep(delay)

    # Final Summary Embed
    summary_embed = discord.Embed(
        title="✅ Mass DM Operation Completed",
        color=discord.Color.green()
    )
    summary_embed.add_field(name="Targeted Members", value=str(total_members), inline=False)
    summary_embed.add_field(name="Successfully Sent", value=f"```yaml\n{successful}\n```", inline=True)
    summary_embed.add_field(name="Failed / DMs Closed", value=f"```yaml\n{failed}\n```", inline=True)
    
    await interaction.followup.send(embed=summary_embed, ephemeral=True)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN environment variable is not set!")
