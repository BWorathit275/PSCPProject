import discord
from discord.ext import commands

client = commands.Bot(commands_prefix = '!')

@client.event
async def on_ready():
    print("Bot is Ready")
    print(":)")

