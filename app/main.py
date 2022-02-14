import uvicorn
from fastapi import FastAPI

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_asyncalchemy.models import *

app = FastAPI()

@app.get("/")
async def hello_world():
    return "hello_world"

if __name__ == '__main__':
    uvicorn.run("main:app", port=1111, host='127.0.0.1')
