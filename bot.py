import os
import discord
import logging
import random
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv

weather_emojis = {
    "clear sky": "☀️",
    "few clouds": "🌤️",
    "scattered clouds": "☁️",
    "broken clouds": "⛅",
    "shower rain": "🌧️",
    "rain": "🌦️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "mist": "🌫️",
    "haze": "🌫️",
    "overcast clouds": "☁️",
    "fog": "🌫️",
    "light rain": "🌧️",
    "moderate rain": "🌧️🌧️",
    "heavy rain": "🌧️🌧️🌧️",
}


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
        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_emoji = weather_emojis.get(weather_description.lower(), "🌍")
        
        weather_report = (
            f"**Weather in {city_name}, {country}:**\n"
            f"🌡️ Temperature: {temperature}°C\n"
            f"{weather_emojis} Condition: {weather_description.capitalize()} \n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬️ Wind Speed: {wind_speed} m/s"
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
        await ctx.send("Error : CommandNotFound")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Error : MissingRequiredArgument")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Error : BadArgument")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send("Error : CommandOnCooldown")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Error : MissingPermissions")
    else:
        # Other error
        logger.error(f"An error occurred: {error}")
        await ctx.send("Error : An error occurred")

# Run the bot with the token from the environment variable
client.run(tokencode)
