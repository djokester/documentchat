from pydantic import BaseModel, Field
from typing import Literal

class ChartFlag(BaseModel):
    visualisation_necessary: bool

class ChartType(BaseModel):
    Type: str
    Method: str
    Description: str

class SQLQuery(BaseModel):
    query: str

class Explanation(BaseModel):
    explanation: str