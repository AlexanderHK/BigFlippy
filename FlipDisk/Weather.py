import python_weather
from enum import Enum
import asyncio

class Weather:
    """
    A class to represent weather information.
    """
    
    #initializes the weather object with temperature and status
    # Uses OpenWeatherMap API to fetch current weather data for a specific city
    def __init__(self):
        self.high = 0
        self.low = 0  # Temperature in Fahrenheit
        self.status = ""             # Weather status (e.g., 'Sunny', 'Rainy', etc.)
        asyncio.run(self.getWeather())

    def __str__(self):
        return f"Weather(temperature={self.temperature}, status={self.status})"
    
    async def getWeather(self) -> None:

        #Declare the client. The measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:

            # Fetch a weather forecast from a city.
            #in the future this may need to be changed to a different city somehow
            weather = await client.get('Boston, MA')

            # Fetch the temperature for today.
            self.high = weather.daily_forecasts[0].highest_temperature
            self.low = weather.daily_forecasts[0].lowest_temperature
            self.status = weather.kind
            print(f"High: {self.high}°F, Low: {self.low}°F, Status: {self.status}")
    
          

