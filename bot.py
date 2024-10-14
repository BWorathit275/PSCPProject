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

@client.command()
async def weather(ctx, *, city: str):
    """fetches the weather forecast for specified city."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': weather_api_key,
        'units': 'metric'
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if data['cod'] != 200:
            await ctx.send(f"Error: {data['message']}")
            return

        city_name = data['name']
        country = data['sys']['country']
        
        weather_report = (
            f"**Weather in {city_name}, {country}:**\n"
        )
        await ctx.send(weather_report)

    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        await ctx.send("Sorry, I couldn't retrieve the weather at the moment.")



# Error Handling
@client.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("no")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("uhh")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("placeholder")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send("placeholder")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("placeholder")
    else:
        # Other error
        logger.error(f"An error occurred: {error}")
        await ctx.send("placeholder")

# Run the bot with the token from the environment variable
client.run(tokencode)
