import os
import discord
import logging
import random
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv('token.env')
tokencode = os.getenv('token')
weather_api_key = os.getenv('weatherapi')

# Set up logger
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Set up intents
intents = discord.Intents.default()
intents.messages = True  # Allows bot to receive message events
intents.message_content = True  # Allows bot to read the message content (for prefix commands)
client = commands.Bot(command_prefix='!', intents=intents)

# Status task
@tasks.loop(minutes=1.0)
async def status_task():
    """misc"""
    statuses = ["tbd", "tbd!", "tbd"]
    await client.change_presence(activity=discord.Game(random.choice(statuses)))

@client.event
async def on_ready():
    """status"""
    print("Bot is Ready")
    print(":)")
    status_task.start()

# Test command
@client.command()
async def hi(ctx):
    """test command"""
    await ctx.send("The One Piece, Is Real")

# Help command
@client.command()
async def cmds(ctx):
    """lists all available commands."""
    help_text = """
    **Available Commands:**
    - `!hi`: test command
    """
    await ctx.send(help_text)



# Run the bot with the token from the environment variable
client.run(tokencode)
