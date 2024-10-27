"""SKYWATCHER"""
import os
import discord
import logging
import random
import datetime
import requests
from discord.ext import commands, tasks
from discord.ui import Button, View
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
    statuses = ["Watching the sky", "Tracking weather updates", "Observing☁️"]
    await client.change_presence(activity=discord.Game(random.choice(statuses)))

@client.event
async def on_ready():
    """status check"""
    print("Bot is Ready")
    status_task.start()

@client.command()
async def weather(ctx, *, city: str):
    """Fetches the weather forecast for the specified city."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"

    # Check if the city is in the custom cities dict
    if city.lower() in custom_cities:
        lat = custom_cities[city.lower()]["lat"]
        lon = custom_cities[city.lower()]["lon"]
        params = {
            'lat': lat,
            'lon': lon,
            'appid': weather_api_key,
            'units': 'metric'
        }
        city_name = city.title()  # Capitalize the city name for display
        country = "Custom Location"
    else:
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
        response = requests.get(base_url, params=params)
        data = response.json()

        if data['cod'] != 200:
            await ctx.send(f"Error: {data['message']}")
            return

        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_emoji = weather_emojis.get(weather_description.lower(), "🌍")
        feels_like = data['main']['feels_like']
        pressure = data['main']['pressure']
        last_updated = datetime.datetime.fromtimestamp(data['dt']).strftime("%Y-%m-%d %H:%M:%S")

        # Create an embed for better visual
        embed = discord.Embed(
            title=f"Weather in {city_name}, {country}",
            description=f"{weather_emoji} {weather_description.capitalize()}",
            color=0x1abc9c
        )

        embed.add_field(name="🌡️ Temperature", value=f"{temperature}°C", inline=True)
        embed.add_field(name="🌡️ Feels Like", value=f"{feels_like}°C", inline=True)
        embed.add_field(name="💧 Humidity", value=f"{humidity}%", inline=True)
        embed.add_field(name="🌬️ Wind Speed", value=f"{wind_speed} m/s", inline=True)
        embed.add_field(name="🌫️ Pressure", value=f"{pressure} hPa", inline=True)
        embed.set_footer(text=f"Last updated: {last_updated}, provided by OpenWeather")

        # Send the embed message
        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        await ctx.send("Sorry, I couldn't retrieve the weather at the moment.")

@client.command()
async def forecast(ctx, *, city: str):
    """Sends buttons for selecting hourly or 8-day forecast."""
    if city.lower() in custom_cities:
        lat = custom_cities[city.lower()]["lat"]
        lon = custom_cities[city.lower()]["lon"]
        city_name = city.title()
    else:
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
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

    button_hourly = Button(label="3-Hours", style=discord.ButtonStyle.primary)
    button_daily = Button(label="6-Days", style=discord.ButtonStyle.secondary)

    view = View()
    view.add_item(button_hourly)
    view.add_item(button_daily)

    async def hourly_callback(interaction):
        await send_hourly_forecast(interaction, city_name, lat, lon)

    async def daily_callback(interaction):
        await send_daily_forecast(interaction, city_name, lat, lon)

    button_hourly.callback = hourly_callback
    button_daily.callback = daily_callback

    await ctx.send(f"Choose the forecast type for {city_name}:", view=view)

async def send_hourly_forecast(interaction, city_name, lat, lon):
    """Sends a 3-hour weather forecast for the next 36 hours (12 intervals)."""
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': weather_api_key,
        'units': 'metric'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code != 200:
        await interaction.response.send_message(f"Error: {data.get('message', '')}")
        return

    forecast_list = data.get('list', [])[:12]  # Get the first 12 intervals (36 hours)
    if not forecast_list:
        await interaction.response.send_message("No forecast data available.")
        return

    forecast_message = f"**3-Hour Weather Forecast for {city_name}:**\n"
    for forecast in forecast_list:
        # Convert Unix timestamp to readable time format
        time = datetime.datetime.fromtimestamp(forecast['dt']).strftime("%I:%M %p")
        temp = forecast['main']['temp']
        humidity = forecast['main']['humidity']
        description = forecast['weather'][0]['description']
        weather_emoji = weather_emojis.get(description.lower(), "🌍")
        forecast_message += f"{time} - {temp}°C,  Humidity: {humidity}%, {description.capitalize()} {weather_emoji}\n"

    await interaction.response.send_message(forecast_message)


async def send_daily_forecast(interaction, city_name, lat, lon):
    """Simulates an 8-day weather forecast using aggregated 3-hour forecast data."""
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': weather_api_key,
        'units': 'metric'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code != 200:
        await interaction.response.send_message(f"Error: {data.get('message', '')}")
        return

    forecast_list = data.get('list', [])
    if not forecast_list:
        await interaction.response.send_message("No forecast data available.")
        return

    # Group data by day and calculate daily statistics
    daily_data = {}
    for forecast in forecast_list:
        # Convert Unix timestamp to date format
        date = datetime.datetime.fromtimestamp(forecast['dt']).strftime("%B %d, %Y")
        temp = forecast['main']['temp']
        humidity = forecast['main']['humidity']
        description = forecast['weather'][0]['description']

        if date not in daily_data:
            daily_data[date] = {'temps': [], 'humidities': [], 'description': description}

        daily_data[date]['temps'].append(temp)
        daily_data[date]['humidities'].append(humidity)

    forecast_message = f"**Simulated Daily Weather Forecast for {city_name}:**\n"
    for date, values in daily_data.items():
        min_temp = min(values['temps'])
        max_temp = max(values['temps'])
        avg_humidity = sum(values['humidities']) // len(values['humidities'])  # Average humidity
        description = values['description']
        weather_emoji = weather_emojis.get(description.lower(), "🌍")
        forecast_message += f"{date} - Day: {max_temp}°C, Night: {min_temp}°C, Humidity: {avg_humidity}%, \
{description.capitalize()} {weather_emoji}\n"

    await interaction.response.send_message(forecast_message)

# Error Handling
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Please check the command and try again.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments. Please provide all required inputs.")
    else:
        await ctx.send("An unexpected error occurred. Please try again later.")

# Bot shutdown command (Owner only)
@client.command()
@commands.is_owner()
async def shutdown(ctx):
    """Shutdown the bot"""
    await ctx.send("Shutting down...")
    await client.close()

client.run(tokencode)
