import uvicorn
import asyncpg

from typing import List
from starlette.status import HTTP_202_ACCEPTED
from starlite import Starlite, CORSConfig, MediaType, get

import conf
from log import logger

cors_config = CORSConfig(allow_origins=["*"])


@get(path="/ping", media_type=MediaType.TEXT)
async def ping() -> str:
    """health check"""
    return "pong"


@get(
    path="/associatedtokens/{contract_id:str}/{address:str}",
    status_code=HTTP_202_ACCEPTED,
    media_type=MediaType.JSON,
)
async def associatedtokens(contract_id: str, address: str) -> List:
    """query db for which token id's are associated with some address"""

    conn = await asyncpg.connect(
        user=conf.db_user, password=conf.db_pass, database=conf.db, host=conf.db_ip
    )

    query = await conn.fetch(
        f"""
        SELECT *
        FROM "{contract_id}"
        WHERE user_addr = '{address}';
    """
    )

    return [r['token_idx'] for r in query]


app = Starlite(route_handlers=[ping, associatedtokens], cors_config=cors_config)
