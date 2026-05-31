"""
Exercise 1: Write 5 tools from scratch — no LLM calls yet.
 
Goal: Define tool functions + Pydantic schemas precisely enough
that an LLM could call them correctly from the schema alone.
 
Domains: weather, calculator, web_search stub, file_reader, db_query
"""
 
from pydantic import BaseModel, Field
from typing import Optional
import json


class WeatherInput(BaseModel):
    location: str = Field(description="The location that the weather information should be retrieve from.")
    unit: str = Field(default="celcious", description="Temperature units: 'Celcious' or 'Fahrenheit'")
    
class WeatherOutput(BaseModel):
    location: str
    unit: str
    temperature: float
    condition: str
    humidity_pct: int 

def get_weather(location: str, unit: str = "celcious"):
    return WeatherOutput(
        location= location,
        unit= unit,
        temperature= 22.2 if unit == "celcious" else 76,
        condition = "Windy",
        humidity_pct= 34
    )




class CalInput(BaseModel):
    expression: str = Field(description= 
                            "A safe arithmetic expression using +, -, *, /, **, ()."
                            "No variable names, no functions. Example: '(3 + 4) * 2'")

class CalOutput(BaseModel):
    expression: str
    result: float
    error: Optional[str] = None 

def cal_result(expression: CalInput) -> CalOutput:
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return CalOutput(
            expression = expression,
            result = 0.0, 
            error = "Expression contains disallowed arithmetic expression."
        )
    try: 
        result = float(eval(expression,{"__builtins__": {}}))
        return CalOutput(expression=expression, result=result)
    except Exception as e:
        return CalOutput(expression=expression, result=0, error= str(e))

    


class SearchInput(BaseModel):
    query: str = Field(description = "Natural Language Processing for Translation, Max character = 200")
    max_results: int = Field(
        default=5, 
        ge=1, 
        le=10,
        description="The number of results to return.")
    
class SearchResult(BaseModel):
    url: str
    title: str
    snippet: Optional[str] = None


class SearchOutput(BaseModel):
    query: str
    result: list[SearchResult]



def web_search(input: SearchInput) -> SearchOutput: 
    stud_results = [SearchResult(url= f"https://example.com/result-{i+1}",
                                title = f"Result {i+1} for '{input.query}'",
                                snippet =f"This is a stub snippet about '{input.query}' — result number {i+1}.",
    ) for i in input.max_results]
    return SearchOutput(query=input.query, result=stud_results)



class ReadFileInput(BaseModel):
    path: str = Field(description="Absolute or relative path to .txt, .md,...")
    max_char: int = Field(
        default=2000,
        le=50000,
        ge=100,
        description="Maximum characters to read. Use smaller values for previews.")


class ReadFileOutput(BaseModel):
    error: Optional[str] = None
    path: str
    truncated: bool
    char_count: int
    content: str


def filereading(path: str, max_char: int = 2000) -> ReadFileOutput:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        truncated = len(raw) > max_char
        return ReadFileOutput(
            error = None,
            path = path,
            truncated = truncated, 
            char_count = len(raw),
            content = raw[max_char:]
        )
    except FileNotFoundError:
        return ReadFileOutput(
            error = f"File is not found: {path}",
            path = path,
            content = "None",
            char_count= 0,
            truncated = False
            )
    except Exception as e:
        return ReadFileOutput(
            error = str[e],
            path = path,
            content = "None",
            char_count= 0,
            truncated = False
            )
    


class DataQueryInput(BaseModel):
    table: str = Field(description= "Table name to query. Available: 'users', 'orders', 'products'.")
    filter: dict[str:str] = Field(
        defautl={},
        description=
        "Column-value pairs to filter rows. "
        "Example: {'status': 'active', 'country': 'US'}")
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max rows to return.")
    
class DataQueryOutput(BaseModel):
    table: str
    rows: list[dict]
    total_returned: int
    error: Optional[str] = None

_FAKE_DB: dict[str, list[dict]] = {
    "users": [
        {"id": 1, "name": "Alice", "status": "active", "country": "US"},
        {"id": 2, "name": "Bob",   "status": "inactive", "country": "UK"},
        {"id": 3, "name": "Carol", "status": "active",   "country": "US"},
    ],
    "orders": [
        {"id": 101, "user_id": 1, "product": "Widget", "status": "shipped"},
        {"id": 102, "user_id": 3, "product": "Gadget", "status": "pending"},
    ],
    "products": [
        {"id": 10, "name": "Widget", "price": 9.99,  "stock": 150},
        {"id": 11, "name": "Gadget", "price": 29.99, "stock": 30},
    ],
}

def query_database(input: DataQueryInput) -> DataQueryOutput:
    table = input.table
    
    if table not in _FAKE_DB:
        return DataQueryOutput(
            error = f"Table is not found.",
            table = table,
            rows = [],
            total_returned=0
        )

    row = _FAKE_DB[table]
    if input.filters: 
        rows = [r for r in rows if all(str(r.get(k)) == v for k, v in input.filters.items())]
        rows = rows[:input.limit]
        return DataQueryOutput(table=table, rows=rows, total_returned=len(rows))
 
 
def print_schema(model: type[BaseModel], label: str) -> None:
    print(f"\n{'='*50}")
    print(f"  {label}")
    print('='*50)
    print(json.dumps(model.model_json_schema(), indent=2))
 
if __name__ == "__main__":
    print_schema(WeatherInput,     "Tool 1 — WeatherInput")
    print_schema(CalInput,  "Tool 2 — CalculatorInput")
    print_schema(SearchInput,      "Tool 3 — SearchInput")
    print_schema(ReadFileInput,  "Tool 4 — FileReaderInput")
    print_schema(DataQueryInput,     "Tool 5 — DBQueryInput")
 
    print("\n\n>>> Quick smoke tests <<<\n")
    print(get_weather("Paris, FR"))
    print(cal_result("(10 + 5) * 3 / 4.5"))
    print(cal_result("import os"))           # should error
    print(web_search("LLM agents 2024", max_results=2))
    print(query_database("users", filters={"status": "active"}))
 