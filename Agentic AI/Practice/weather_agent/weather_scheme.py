from pydantic import Field, BaseModel
from typing import Optional


class WeatherRequest(BaseModel):
    city: str = Field(description="The city to get the temperature from.")
    country_code: Optional[str] = Field(default=None, description="ISO 3166 country code, e.g. 'US', 'GB', 'KH'")
    unit: str = Field(default="Celcious", description="Temperature unit: Celcious or Fahrenheit")

class WeatherData(BaseModel):
    """Structure the response"""
    city: str
    country: Optional[str]
    temperature: float
    feels_like: float
    humidy: int 
    wind_speed: float
    unit: str
    description: str

    

weather_tool_schema = {
     "name": "get_data",
     "description": "get the information about the weather in the given city",
     "input_schema": WeatherData.model_json_schema(),
 }

