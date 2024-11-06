# SKYWATCHER

**SKYWATCHER** is a Discord bot that provides real-time weather updates, air quality information, and hurricane tracking data. It is powered by OpenWeather API, and includes visual features for weather forecasts and storm tracks.

## Features

- **Real-time Weather Information**: Get up-to-date weather details for any city.
- **Air Quality Index (AQI)**: Displays AQI with warnings when necessary.
- **Custom City Support**: Add and manage custom cities for weather update in place with no location data.
- **Hourly and 6-Day Forecasts**: View temperature trends, humidity, wind speed, and rain chances over the next several hours or days.
- **Hurricane Tracking**: Track tropical cyclones in the North Atlantic basin with historical data and visual storm paths[PRE 2024].

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/SKYWATCHER.git
   cd SKYWATCHER
   ```

2. **Set up a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:

4. **Set up environment variables**:
   - Create a `.env` file in the project directory to store your bot token and weather API key.
   - Format:
     ```
     token=YOUR_DISCORD_BOT_TOKEN
     weatherapi=YOUR_OPENWEATHER_API_KEY
     ```

5. **Configure settings**:
   - Edit `config.json` to customize settings like weather emojis, custom cities, warning thresholds, etc.

## Usage

- **Run the bot**

- **Basic Commands**:
  - `/weather [city]`: Get the current weather for a specified city.
  - `/custom_city`: View available custom cities.
  - `/main_forecast [city]`: Choose between 3-hour or 6-day forecasts.
  - `/hurricane [storm name] [year]`: Retrieve data on a specific storm (e.g., `/hurricane Dorian 2019`)[PRE 2024].
  - `/cmds`: View a list of all available commands.

## Requirements

- Python 3.8+
- Libraries: `discord`, `requests`, `matplotlib`, `tropycal`, `dotenv`
- Discord bot token and OpenWeather API key


## Customization

You can customize several aspects of SKYWATCHER by modifying the `config.json` file:
- **Weather Emojis**: Set custom emojis for different weather descriptions.
- **Warning Levels**: Adjust thresholds for temperature, wind speed, humidity, and UV index warnings.
- **Custom Cities**: Add or edit locations to quickly access weather data for commonly monitored areas.


## Acknowledgments

- **OpenWeather API** for providing the weather data.
- **Discord.py** for the bot functionality.
- **Tropycal** for hurricane tracking capabilities.

