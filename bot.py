import os
import discord
from discord.ext import commands
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
tokencode = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True  # Allows bot to receive message events

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
