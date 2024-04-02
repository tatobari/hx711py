from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def get_root():
    return {"Hello": "World"}

