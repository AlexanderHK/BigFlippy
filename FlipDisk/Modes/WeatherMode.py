from PIL import Image
import python_weather
from enum import Enum
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Board.BoardFont import BoardFont
from Board.FDProcessing import SimpleBW
from constants import boardSize
from Board.PixelBoard import board
from .ModeBase import ModeBase
#==================================================================
#                   Weather mode Variables
#==================================================================
WEATHER_START_TIME = "06:30"  # Start time for weather mode
WEATHER_END_TIME = "9:30"  # End time for weather mode
WEATHER_IMAGE_DIRECTORY = "WeatherImages/"  # Directory where images are stored

#==================================================================
#                   Weather Class
#==================================================================
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
        return f"Weather(high={self.high}, low={self.low}, status={self.status})"

    async def getWeather(self) -> None:

        #Declare the client. The measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:

            # Fetch a weather forecast from a city.
            #in the future this may need to be changed to a different city somehow
            weather = await client.get('Boston, MA')

            # Fetch the temperature for today.
            self.high = weather.daily_forecasts[0].highest_temperature
            self.low = weather.daily_forecasts[0].lowest_temperature
            print(weather.kind.name)
            self.status = weather.kind
            print(f"High: {self.high}°F, Low: {self.low}°F, Status: {self.status}")

#=======================================================================
#                   Mode Override Functions
#=======================================================================
class WeatherMode(ModeBase):
    def __init__(self):
        self.state = "READY"
        pass

    def run(self, run_in_plot=False):

        while self.state!="SHUTDOWN":
            if self.state=="READY":
                weather = Weather()  # Initialize the weather object
                print(weather)  # Print the current weather information

                self.LoadWeather(weather)  # Load weather onto board
                if not run_in_plot:
                    board.publishImage()
                    board.refreshDisplay()
                else:
                    board.PlotLocal()
                self.state="DISPLAYED"
            
    def shutdown(self):
        self.state = "SHUTDOWN"

    def receive_data(self, data):
        pass

    def LoadWeather(self, weather):
        """
        Loads weather data onto the board.
        :param weather: Weather object containing high, low, and status attributes.
        """
        board.clear()
        img = Image.open(f"WeatherImages/{weather.status}.png")  # Load the weather image
        img = SimpleBW(img, board.getSize(), invert=True)  # Convert to black and white
        board.loadImage(img)
        board.WriteOnTop(f"LO   HI", y_offset=0,font=BoardFont(), x_offset=0, spacing=1)
        board.WriteOnTop(f"{weather.low}   {weather.high}", y_offset=6,font=BoardFont(), x_offset=0, spacing=1)



