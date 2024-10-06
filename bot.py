import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
tokencode = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix='!')

@client.event
async def on_ready():
    """status"""
    print("Bot is Ready")
    print(":)")

@client.command()
async def hi(ctx):
    """testcommand"""
    await ctx.send("The One Piece, Is Real")

# Run the bot with the token from the environment variable
client.run(tokencode)