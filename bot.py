"""SKYWATCHER"""
import os
import logging
import random
import datetime
import json
import discord
import requests
import matplotlib.pyplot as plt
import tropycal.tracks as tracks
from discord.ext import commands, tasks
from discord.ui import Button, View
from dotenv import load_dotenv

# Load configuration
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

weather_emojis = config["weather_emojis"]
custom_cities = config["custom_cities"]
statuses = config["statuses"]

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

# API call helper with error handling
def get_weather_data(url, params):
    """Fetch data from a weather API endpoint with given params and error handling."""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred: %s", http_err)
    except requests.exceptions.RequestException as req_err:
        logger.error("Request error occurred: %s", req_err)
    return None

def get_level(value, levels):
    """Determine level based on configuration thresholds."""
    for _, bounds in levels.items():
        min_val = bounds.get('min', float('-inf'))
        max_val = bounds.get('max', float('inf'))
        if min_val <= value <= max_val:
            return bounds['description']
    return "Unknown"

def get_humidity_level(humidity):
    """Determine humidity level based on configuration."""
    levels = config["humidity_levels"]
    if humidity <= levels["dry"]["max"]:
        return levels["dry"]["description"]
    elif humidity <= levels["comfortable"]["max"]:
        return levels["comfortable"]["description"]
    elif humidity <= levels["humid"]["max"]:
        return levels["humid"]["description"]
    else:
        return levels["very_humid"]["description"]

def get_wind_level(wind_speed):
    """Determine wind level based on configuration."""
    return get_level(wind_speed, config["wind_levels"])

def get_uv_level(uv_index):
    """Determine UV level based on configuration."""
    return get_level(uv_index, config["uv_levels"])

def get_rain_level(rain_amount):
    """Determine rain level based on configuration."""
    return get_level(rain_amount, config["rain_levels"])

@tasks.loop(minutes=1.0)
async def status_task():
    """Update bot status randomly from a list of statuses."""
    await client.change_presence(activity=discord.Game(random.choice(statuses)))

@client.event
async def on_ready():
    """Bot ready event handler."""
    logger.info("Bot is ready.")
    await client.tree.sync()
    status_task.start()

@client.tree.command()
async def custom_city(interaction):
    """Displays available custom cities."""
    cities_list = "\n".join([city.title() for city in config["custom_cities"]])
    embed = discord.Embed(
        title="Available Custom Cities",
        description=cities_list,
        color=0x1abc9c
    )
    await interaction.response.send_message(embed=embed)

@client.tree.command()
async def cmds(interaction):
    """Displays available bot commands."""
    commands_list = "\n".join([f"!{command} - {desc}" for command, desc in \
config["commands"].items()])
    embed = discord.Embed(
        title="Available Commands",
        description=commands_list,
        color=0x1abc9c
    )
    await interaction.response.send_message(embed=embed)

@client.tree.command()
async def weather(interaction, *, city: str):
    """Fetches and displays weather for the specified city."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    aqi_url = "http://api.openweathermap.org/data/2.5/air_pollution"
    uvi_url = "http://api.openweathermap.org/data/2.5/uvi"
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"

    # Check if city is in custom cities
    if city.lower() in custom_cities:
        lat = custom_cities[city.lower()]["lat"]
        lon = custom_cities[city.lower()]["lon"]
        city_name = city.title()
        country = "Custom Location"
    else:
        geocode_params = {'q': city, 'appid': weather_api_key, 'limit': 1}
        geocode_data = get_weather_data(geocode_url, geocode_params)

        if not geocode_data:
            await interaction.response.send_message("City not found. Please check the\
                spelling or try a different city.")
            return

        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        city_name = geocode_data[0]['name']
        country = geocode_data[0].get('country', 'Unknown')

    params = {'lat': lat, 'lon': lon, 'appid': weather_api_key, 'units': 'metric'}
    data = get_weather_data(base_url, params)
    if not data or data.get('cod') != 200:
        await interaction.response.send_message\
            (f"Error: {data.get('message', 'Could not retrieve weather data.')}")
        return

    # Process data
    temperature = data['main']['temp']
    weather_description = data['weather'][0]['description']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    visibility = data.get('visibility', 0) / 1000
    feels_like = data['main']['feels_like']
    pressure = data['main']['pressure']
    sunrise = datetime.datetime.fromtimestamp(data['sys']['sunrise']).strftime("%H:%M")
    sunset = datetime.datetime.fromtimestamp(data['sys']['sunset']).strftime("%H:%M")
    weather_emoji = weather_emojis.get(weather_description.lower(), "🌍")
    cloud_cover = data.get('clouds', {}).get('all', 0)
    rain_amount = data.get('rain', {}).get('1h', 0)
    last_updated = datetime.datetime.fromtimestamp(data['dt']).strftime("%Y-%m-%d %H:%M:%S")

    uvi_data = get_weather_data(uvi_url, {'lat': lat, 'lon': lon, 'appid': weather_api_key})
    uv_index = uvi_data.get('value', "N/A") if uvi_data else "N/A"

    aqi_data = get_weather_data(aqi_url, {'lat': lat, 'lon': lon, 'appid': weather_api_key})
    aqi = aqi_data.get('list', [{}])[0].get('main', {}).get('aqi', "N/A") if aqi_data else "N/A"

    aqi_levels = config["aqi_levels"]
    aqi_colors = config["aqi_colors"]
    aqi_level = aqi_levels[int(aqi) - 1] if isinstance(aqi, int) and 1 <= aqi <= 5 else "N/A"
    aqi_color = aqi_colors[int(aqi) - 1] if isinstance(aqi, int) and 1 <= aqi <= 5 else 0x1abc9c

    icon_code = data['weather'][0]['icon']  # e.g., '01d' for a sunny day
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    # Warnings
    warnings = []
    if temperature < config["temperature_levels"]["cold"]["max"]:
        warnings.append(config["warnings"]["tempcold"])
    elif temperature > config["temperature_levels"]["hot"]["min"]:
        warnings.append(config["warnings"]["temphot"])

    if humidity > config["humidity_levels"]["humid"]["max"]:
        warnings.append(config["warnings"]["humidity"])

    if wind_speed > config["wind_levels"]["strong_wind"]["min"]:
        warnings.append(config["warnings"]["wind_speed"])

    if uv_index != "N/A" and uv_index > config["uv_levels"]["high"]["min"]:
        warnings.append(config["warnings"]["uv_index"])

    if isinstance(aqi, int) and 1 <= aqi <= 5:
        aqi_level_key = config["aqi_levels"][aqi - 1].lower().replace(" ", "_")
        aqi_warning = config.get("aqi_warnings", {}).get(aqi_level_key, None)
        if aqi_warning:
            warnings.append(aqi_warning)

    # Embed for weather data
    embed = discord.Embed(
        title=f"Weather in {city_name}, {country}",
        description=f"{weather_emoji} **{weather_description.capitalize()}**",
        color=aqi_color
    )
    embed.set_thumbnail(url=icon_url)
    embed.add_field(name="🌡️ Temperature", value=f"{temperature}°C (Feels like\
{feels_like}°C)\nLevel: {get_level(temperature, config['temperature_levels'])}", inline=True)
    embed.add_field(name="💧 Humidity", value=f"{humidity}% \
({get_humidity_level(humidity)})", inline=True)
    embed.add_field(name="🌬️ Wind Speed", value=f"{wind_speed} m/s \
({get_wind_level(wind_speed)})", inline=True)
    embed.add_field(name="🌞 UV Index", value=f"{uv_index} \
({get_uv_level(uv_index)})", inline=True)
    embed.add_field(name="🌧️ Rain Amount", value=f"{rain_amount} mm \
({get_rain_level(rain_amount)})", inline=True)
    embed.add_field(name="🌫️ Visibility", value=f"{visibility:.1f} km", inline=True)
    embed.add_field(name="📉 Pressure", value=f"{pressure} hPa", inline=True)
    embed.add_field(name="☁️ Cloud Cover", value=f"{cloud_cover}%", inline=True)
    embed.add_field(name="🏭 AQI", value=f"{aqi} ({aqi_level})", inline=True)
    embed.add_field(name="🌄 Sunrise", value=sunrise, inline=True)
    embed.add_field(name="🌇 Sunset", value=sunset, inline=True)

    if warnings:
        embed.add_field(name="⚠️ Warnings", value="\n".join([f"• {warning}" \
            for warning in warnings]), inline=False)

    embed.set_footer(text=f"Last updated: {last_updated}, provided by OpenWeather")
    await interaction.response.send_message(embed=embed)

@client.tree.command()
async def main_forecast(interaction, *, city: str):
    """Provides buttons for hourly or 6-day forecast."""
    if city.lower() in custom_cities:
        lat = custom_cities[city.lower()]["lat"]
        lon = custom_cities[city.lower()]["lon"]
        city_name = city.title()
    else:
        # Geocode the city if it's not in custom cities
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        geocode_params = {'q': city, 'appid': weather_api_key, 'limit': 1}
        geocode_data = get_weather_data(geocode_url, geocode_params)

        if not geocode_data:
            await interaction.response.send_message("City not found. \
                Please check the spelling or try a different city.")
            return

        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        city_name = geocode_data[0]['name']

    # Create buttons for hourly or daily forecasts
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

    await interaction.response.send_message(f"Choose the forecast type for {city_name}:", view=view)

async def send_hourly_forecast(interaction, city_name, lat=None, lon=None):
    """Displays 3-hour weather forecast for the next 36 hours."""
    base_url = "http://api.openweathermap.org/data/2.5/forecast"

    if lat is None or lon is None:
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        geocode_params = {'q': city_name, 'appid': weather_api_key, 'limit': 1}
        geocode_data = get_weather_data(geocode_url, geocode_params)

        if not geocode_data:
            await interaction.response.send_message("City not found. \
                Please check the spelling or try a different city.")
            return

        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        city_name = geocode_data[0]['name']

    params = {'lat': lat, 'lon': lon, 'appid': weather_api_key, 'units': 'metric'}

    data = get_weather_data(base_url, params)
    if not data:
        await interaction.response.send_message("Error fetching forecast data.")
        return

    forecast_list = data.get('list', [])[:12]

    times = []
    temps = []
    feels_like_temps = []
    humidities = []
    wind_speeds = []
    rain_amounts = []
    pops = []

    embed = discord.Embed(
        title=f"**Hourly Weather Forecast for {city_name}:**",
        description="Here is the detailed weather forecast for the next 36 hours.",
        color=0x1abc9c
    )

    for forecast in forecast_list:
        dt = datetime.datetime.fromtimestamp(forecast['dt']).strftime("%b %d, %H:%M")
        temp = forecast['main']['temp']
        feels_like = forecast['main']['feels_like']
        humidity = forecast['main']['humidity']
        wind_speed = forecast['wind']['speed']
        cloud_cover = forecast.get('clouds', {}).get('all', 0)
        pop = int(forecast.get('pop', 0) * 100)
        rain_amount = forecast.get('rain', {}).get('3h', 0)
        description = forecast['weather'][0]['description']
        weather_emoji = weather_emojis.get(description.lower(), "🌍")

        # Store data for plotting
        times.append(dt)
        temps.append(temp)
        feels_like_temps.append(feels_like)
        humidities.append(humidity)
        wind_speeds.append(wind_speed)
        rain_amounts.append(rain_amount)
        pops.append(pop)

        embed.add_field(
            name=f"{dt} - {weather_emoji} {description.title()}",
            value=(
                f"🌡️ **Temp**: {temp:.2f}°C (Feels like **{feels_like:.2f}°C**)\n"
                f"💧 **Humidity**: {humidity}%\n"
                f"🌬️ **Wind Speed**: {wind_speed:.2f} m/s\n"
                f"☁️ **Cloud Cover**: {cloud_cover}%\n"
                f"🌧️ **Precipitation**: {pop}%\n"
                f"🌧️ **Rain Amount**: {rain_amount} mm\n"
                f"---"
            ),
            inline=False
        )

    # Generate the graph for the forecast
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot temperature and feels-like temperature
    ax1.plot(times, temps, marker='o', color='red', label='Temperature (°C)')
    ax1.plot(times, feels_like_temps, marker='x', color='orange', linestyle='--', \
        label='Feels Like (°C)')
    ax1.set_ylabel('Temperature (°C)', color='red')
    ax1.tick_params(axis='y', labelcolor='red')

    # Plot rain probability and rain amount as bars
    ax1.bar(times, pops, alpha=0.2, color='cyan', label='Rain Probability (%)', width=0.5)
    ax1.bar(times, rain_amounts, alpha=0.4, color='blue', label='Rain Amount (mm)', width=0.3)

    # Create a secondary axis for humidity and wind speed
    ax2 = ax1.twinx()
    ax2.plot(times, humidities, marker='^', linestyle='--', color='blue', label='Humidity (%)')
    ax2.plot(times, wind_speeds, marker='s', linestyle='-', color='green', label='Wind Speed (m/s)')
    ax2.set_ylabel('Humidity (%) / Wind Speed (m/s)', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')

    # Adjust x-axis labels to avoid overlapping
    plt.xticks(rotation=45, ha="right", fontsize=10)

    # Title and legend adjustments for better visibility
    plt.title(f"Hourly Weather Forecast for the Next 36 Hours in {city_name}", fontsize=16)
    fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), fontsize=10, ncol=3)

    # Add a grid for better readability
    ax1.grid(visible=True, which='both', linestyle='--', linewidth=0.5)

    image_path = f"{city_name}_hourly_forecast.png"
    plt.tight_layout()
    plt.savefig(image_path, bbox_inches='tight')
    plt.close()

    embed.set_image(url="attachment://" + image_path)

    await interaction.response.send_message(embed=embed, file=discord.File(image_path))

    # Clean up the saved image
    if os.path.exists(image_path):
        os.remove(image_path)


async def send_daily_forecast(interaction, city_name, lat=None, lon=None):
    """Displays a 6-day weather forecast with enhanced visualization for better readability."""
    base_url = "http://api.openweathermap.org/data/2.5/forecast"

    if lat is None or lon is None:
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        geocode_params = {'q': city_name, 'appid': weather_api_key, 'limit': 1}
        geocode_data = get_weather_data(geocode_url, geocode_params)

        if not geocode_data:
            await interaction.response.send_message("City not found. \
                Please check the spelling or try a different city.")
            return

        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        city_name = geocode_data[0]['name']

    params = {'lat': lat, 'lon': lon, 'appid': weather_api_key, 'units': 'metric'}
    data = get_weather_data(base_url, params)

    if not data:
        await interaction.response.send_message("Error fetching forecast data.")
        return

    # Extract daily data
    daily_data = {}
    for forecast in data.get('list', []):
        date = datetime.datetime.fromtimestamp(forecast['dt']).strftime("%B %d, %Y")
        temp = forecast['main']['temp']
        feels_like = forecast['main']['feels_like']
        humidity = forecast['main']['humidity']
        wind_speed = forecast['wind']['speed']
        rain_amount = forecast.get('rain', {}).get('3h', 0)
        pop = forecast.get('pop', 0) * 100

        if date not in daily_data:
            daily_data[date] = {'temps': [], 'feels_like': [], \
                'humidities': [], 'wind_speeds': [], 'rain': [], 'pop': []}

        daily_data[date]['temps'].append(temp)
        daily_data[date]['feels_like'].append(feels_like)
        daily_data[date]['humidities'].append(humidity)
        daily_data[date]['wind_speeds'].append(wind_speed)
        daily_data[date]['rain'].append(rain_amount)
        daily_data[date]['pop'].append(pop)

    # Prepare data for the next 6 days
    dates = list(daily_data.keys())[:6]
    min_temps = [min(daily_data[day]['temps']) for day in dates]
    max_temps = [max(daily_data[day]['temps']) for day in dates]
    avg_feels_like = [sum(daily_data[day]['feels_like']) / \
        len(daily_data[day]['feels_like']) for day in dates]
    avg_humidity = [sum(daily_data[day]['humidities']) / \
        len(daily_data[day]['humidities']) for day in dates]
    avg_wind_speed = [sum(daily_data[day]['wind_speeds']) / \
        len(daily_data[day]['wind_speeds']) for day in dates]
    total_rain = [sum(daily_data[day]['rain']) for day in dates]
    avg_pop = [sum(daily_data[day]['pop']) / \
        len(daily_data[day]['pop']) for day in dates]

    # Create the figure with subplots to separate temperature and rain data
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Subplot 1: Temperature (Min, Max, Feels-Like)
    ax1.bar(dates, max_temps, color='#FF4500', alpha=0.7, label='Max Temperature (°C)', width=0.4)
    ax1.bar(dates, min_temps, color='#FFA500', alpha=0.7, label='Min Temperature (°C)', width=0.4)
    ax1.plot(dates, avg_feels_like, marker='o', linestyle='--', \
        color='darkred', label='Feels Like Avg (°C)', linewidth=2)
    ax1.set_ylabel('Temperature (°C)', color='red')
    ax1.tick_params(axis='y', labelcolor='red')
    ax1.legend(loc='upper left', fontsize=9)

    # Subplot 2: Rain Probability, Rain Amount, Humidity, Wind Speed
    x_indices = range(len(dates))
    ax2.bar([x - 0.2 for x in x_indices], avg_pop, alpha=0.2, \
        color='cyan', label='Rain Probability (%)', width=0.4, hatch='//')
    ax2.bar([x + 0.2 for x in x_indices], total_rain, alpha=0.4, \
        color='navy', label='Total Rain Amount (mm)', width=0.4)
    ax2.plot(dates, avg_humidity, marker='^', linestyle='--', \
        color='blue', label='Humidity (%)', linewidth=1.5)
    ax2.plot(dates, avg_wind_speed, marker='s', linestyle='-', \
        color='green', label='Wind Speed (m/s)', linewidth=2)
    ax2.set_ylabel('Rainfall (mm)\nHumidity (%) / Wind Speed (m/s)', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    ax2.legend(loc='upper left', fontsize=9)

    # Set the x-axis label for the entire figure
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.xlabel('Date', fontsize=12)

    # Title for the entire figure
    plt.suptitle(f"6-Day Weather Forecast - {city_name}", fontsize=16)

    # Adjust layout for better readability
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Add a grid for better readability
    ax1.grid(visible=True, which='both', linestyle='--', linewidth=0.5)
    ax2.grid(visible=True, which='both', linestyle='--', linewidth=0.5)

    image_path = f"{city_name}_daily_forecast.png"
    plt.savefig(image_path, bbox_inches='tight')
    plt.close()

    embed = discord.Embed(
        title=f"**6-Day Weather Forecast for {city_name}:**",
        description="Here is the detailed weather forecast for the next 6 days.",
        color=0x1abc9c
    )

    embed.set_image(url="attachment://" + image_path)

    for day in dates:
        min_temp = min(daily_data[day]['temps'])
        max_temp = max(daily_data[day]['temps'])
        avg_feel = sum(daily_data[day]['feels_like']) / len(daily_data[day]['feels_like'])
        avg_hum = sum(daily_data[day]['humidities']) / len(daily_data[day]['humidities'])
        avg_wind = sum(daily_data[day]['wind_speeds']) / len(daily_data[day]['wind_speeds'])
        total_rain = sum(daily_data[day]['rain'])
        avg_pop = sum(daily_data[day]['pop']) / len(daily_data[day]['pop'])

        embed.add_field(
            name=f"{day}",
            value=(
                f"🌡️ Max Temp: {max_temp}°C\n"
                f"🌡️ Min Temp: {min_temp}°C\n"
                f"🔥 Feels Like Avg: {avg_feel:.2f}°C\n"
                f"💧 Humidity Avg: {avg_hum:.2f}%\n"
                f"🌬️ Wind Speed Avg: {avg_wind:.2f} m/s\n"
                f"🌧️ Rain Probability Avg: {avg_pop:.2f}%\n"
                f"🌧️ Total Rain Amount: {total_rain} mm"
            ),
            inline=False
        )

    await interaction.response.send_message(embed=embed, file=discord.File(image_path))

    if os.path.exists(image_path):
        os.remove(image_path)

basin = tracks.TrackDataset(basin='north_atlantic')

@client.tree.command()
async def hurricane(interaction, *, stormname_year: str):
    """
    Command to retrieve and display information about a tropical cyclone.
    Usage: !hurricane [Storm Name] [Year]
    Example: !hurricane Dorian 2019
    """
    try:
        storm_name, year = stormname_year.split()
        year = int(year)
        
        # Retrieve specific storm by name and year
        storm = basin.get_storm((storm_name, year))

        # Check if storm data was found
        if not storm:
            await interaction.response.send_message(f"Storm '{storm_name}\
                {year}' not found in the data.")
            return

        # Get basic storm information from the dictionary structure
        max_wind = max(storm.dict['vmax'])  # Max wind speed in knots
        min_pressure = min(storm.dict['mslp'])  # Min pressure in hPa
        start_date = storm.dict['time'][0].strftime("%Y-%m-%d")
        end_date = storm.dict['time'][-1].strftime("%Y-%m-%d")
        # Calculate storm duration
        duration_days = (storm.dict['time'][-1] - storm.dict['time'][0]).days

        # Calculate ACE
        ace = storm.dict.get('ace', "N/A")

        # Determine storm category based on max wind speed
        category = "Tropical Depression" if max_wind < 39 else \
                "Tropical Storm" if max_wind < 74 else \
                "Hurricane" if max_wind < 113 else \
                "Major Hurricane"

        # Format the storm track information
        track_message = "\n".join([
            f"Time: {time.strftime('%Y-%m-%d %H:%M')}, Lat: {lat}, Lon: {lon}, Wind: {vmax} knots"
            for time, lat, lon, vmax in zip(storm.dict['time'], storm.dict['lat']\
, storm.dict['lon'], storm.dict['vmax'])
        ])

        # Create an embed to display storm information
        embed = discord.Embed(
            title=f"🌀 Hurricane Info: {storm_name.capitalize()} {year}",
            description=f"Start Date: {start_date}\nEnd Date: {end_date}",
            color=0x3498db
        )
        embed.add_field(name="Category", value=category, inline=True)
        embed.add_field(name="Duration", value=f"{duration_days} days", inline=True)
        embed.add_field(name="Accumulated Cyclone Energy (ACE)", value=f"{ace}", inline=True)
        embed.add_field(name="Max Wind Speed", value=f"{max_wind} knots", inline=True)
        embed.add_field(name="Min Pressure", value=f"{min_pressure} hPa", inline=True)
        embed.add_field(name="Storm Track", value=track_message[:0], inline=False)

        # Plot the storm track and save the image
        plt.figure()
        storm.plot(
        domain="dynamic",
        title=f"Track of {storm_name.capitalize()} ({year})",
        plot_all_dots=True,
        color="category"
        )
        image_path = f"{storm_name}_{year}_track.png"
        plt.savefig(image_path, bbox_inches='tight')  # Save the plot to a file
        plt.close()  # Close the plot to free up memory

        # Send the embed
        await interaction.response.send_message(embed=embed)
        await interaction.followup.send(file=discord.File(image_path))

    except ValueError:
        await interaction.response.send_message("Provide the storm name and year in the format:\
            /hurricane [Storm Name] [Year]")
    except KeyError as e:
        logger.error("Error retrieving cyclone data: %s", e)
        await interaction.response.send_message("An error occurred")
    finally:
        # Clean up image file
        if os.path.exists(image_path):
            os.remove(image_path)

# Error handling
@client.event
async def on_command_error(ctx, error):
    '''Error handling function'''
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Please check the command and try again.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments. Please provide all required inputs.")
    else:
        logger.exception("Unexpected error:", exc_info=error)
        await ctx.send("An unexpected error occurred. Please try again later.")

client.run(tokencode)
