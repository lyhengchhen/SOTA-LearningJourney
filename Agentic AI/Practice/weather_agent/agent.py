import anthropic, json
from weather_scheme import WeatherRequest, WeatherData, weather_tool_schema
from weather_tools import get_data

client = anthropic.Anthropic()


messages = [{"role": "user", "content": "What's the weather like in Paris?"}]


response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[weather_tool_schema],
    messages=messages,
)
for block in response.content:
    if block.type == "tool_use" and block.name == "get_data":
        tool_input = WeatherRequest(**block.input)
        result = get_data(tool_input)
        print(result.model_dump_json(indent=2))