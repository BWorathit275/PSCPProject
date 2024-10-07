import os
import discord
import logging
import random
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
tokencode = os.getenv('DISCORD_TOKEN')

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

intents = discord.Intents.default()
intents.messages = True
client = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(minutes=1.0)
async def status_task():
    statuses = ["tbd", "tbd!", "tbd"]
    await client.change_presence(activity=discord.Game(random.choice(statuses)))

@client.event
async def on_ready():
    """status"""
    print("Bot is Ready")
    print(":)")

@client.command()
async def hi(ctx):
    """test command"""
    await ctx.send("The One Piece, Is Real")

# Run the bot with the token from the environment variable
client.run(tokencode)
