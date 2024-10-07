import os
import discord
import logging
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
