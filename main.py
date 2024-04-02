from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def get_root():
    return "Welcome to Sortwise Weight Sensor go to /docs for endpoints" 

