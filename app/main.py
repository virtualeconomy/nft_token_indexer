import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import conf

app = FastAPI()

@app.get("/")
async def hello_world():
    return "hello_world"

@app.get("/associatedtokens/{contract_id}/{address}")
async def associatedtokens(contract_id: str, address: str):

    conn = await asyncpg.connect(user=conf.db_user, password=conf.db_pass,
                                 database=conf.db, host=conf.db_ip)
    
    query = await conn.execute(f'''
        SELECT token_idx
        FROM {contract_id}
        WHERE user_addr = {address};
    ''')

    return [i['token_idx'] for i in query]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=['Access-Control-Allow-Origin'],
)

if __name__ == '__main__':
    uvicorn.run("main:app", port=1111, host='127.0.0.1')
