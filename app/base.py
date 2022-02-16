import asyncio
import asyncpg

import conf
from log import logger


async def init_table(ctrt_id: str):
    """initiate all token tables"""

    conn = await asyncpg.connect(user=conf.db_user, password=conf.db_pass,
                             database=conf.db, host=conf.db_ip)

    # Execute a statement to create a new table.
    await conn.execute(f'''
        CREATE TABLE {ctrt_id}(
        user_addr      VARCHAR(100) NOT NULL,
        token_idx      INT          NOT NULL,
        amount 		   INT          NOT NULL
        );
    ''')

    await conn.close()


async def test_insert():

    conn = await asyncpg.connect(user=conf.db_user, password=conf.db_pass,
                             database=conf.db, host=conf.db_ip)
    
    await conn.execute(
        """INSERT INTO cf2pag83harcsmp9s9m2xegajupqwkfarxr VALUES('ATytsw58Q1PBUcduYnA6iwT8S8jHZcLTz5i', 1, 1);"""
    )

    await conn.close()


async def test_read():

    conn = await asyncpg.connect(user=conf.db_user, password=conf.db_pass,
                            database=conf.db, host=conf.db_ip)

    q = await conn.fetch(
        """SELECT token_idx
           FROM cf2pag83harcsmp9s9m2xegajupqwkfarxr
           WHERE user_addr = 'ATytsw58Q1PBUcduYnA6iwT8S8jHZcLTz5i';
        """)

    logger.info(q[0]['token_idx'])

    await conn.close()

    return q

#asyncio.run(init_table())
asyncio.run(test_read())
