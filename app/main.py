import uvicorn
from fastapi import FastAPI

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/")
async def hello_world():
    return "hello_world"


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=['Access-Control-Allow-Origin'],
)

if __name__ == '__main__':
    uvicorn.run("main:app", port=1111, host='127.0.0.1')
