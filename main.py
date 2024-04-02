from typing import Union
from sensor import get_current_weight

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def get_root():
  return "Welcome to Sortwise Weight Sensor go to /docs for endpoints" 

@app.get("/weight")
def get_weight():
  return {"weight": get_current_weight()}

