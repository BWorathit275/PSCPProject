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

custom_cities = {
    "bang phli": {"lat": 13.6059, "lon": 100.7061},
    "kmitl": {"lat": 13.7289, "lon": 100.7780}
    # Add more custom cities here
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
intents.messages = True
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(minutes=1.0)
async def status_task():
    """status task"""
    statuses = ["tbd", "tbd!", "tbd"]
    await client.change_presence(activity=discord.Game(random.choice(statuses)))

@client.event
async def on_ready():
    """status check"""
    print("Bot is Ready")
    print(":)")
    status_task.start()

@client.command()
async def weather(ctx, *, city: str):
    """Fetches the weather forecast for the specified city."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"

    # Check if the city is in the custom cities dict
    if city.lower() in custom_cities:
        # Use the custom latitude and longitude for the request
        lat = custom_cities[city.lower()]["lat"]
        lon = custom_cities[city.lower()]["lon"]
        params = {
            'lat': lat,
            'lon': lon,
            'appid': weather_api_key,
            'units': 'metric'
        }
        # Set the city_name to the custom city name
        city_name = city.title()  # Capitalize the city name for display
        country = "Custom Location"  # Optional: Set a placeholder country name
    else:
        # Use the Geocoding API if the city isn't in the custom cities dictionary
        geocode_params = {
            'q': city,
            'appid': weather_api_key,
            'limit': 1
        }
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_data = geocode_response.json()

        if not geocode_data:
            await ctx.send("City not found. Please check the spelling or try a different city.")
            return

        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        city_name = geocode_data[0]['name']
        country = geocode_data[0].get('country', 'Unknown')
        params = {
            'lat': lat,
            'lon': lon,
            'appid': weather_api_key,
            'units': 'metric'
        }

    try:
        # Make the request to the weather API
        response = requests.get(base_url, params=params)
        data = response.json()

        if data['cod'] != 200:
            await ctx.send(f"Error: {data['message']}")
            return

        # Extract weather details
        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        # Get the corresponding emoji for the weather description
        weather_emoji = weather_emojis.get(weather_description.lower(), "🌍")

        # Create an embed for better visual
        embed = discord.Embed(
            title=f"Weather in {city_name}, {country}",
            description=f"{weather_emoji} {weather_description.capitalize()}",
            color=0x1abc9c
        )
        embed.add_field(name="🌡️ Temperature", value=f"{temperature}°C", inline=True)
        embed.add_field(name="💧 Humidity", value=f"{humidity}%", inline=True)
        embed.add_field(name="🌬️ Wind Speed", value=f"{wind_speed} m/s", inline=True)
        embed.set_footer(text="Weather data provided by OpenWeather")

        # Send the embed message
        await ctx.send(embed=embed)

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
