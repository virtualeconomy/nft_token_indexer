import asyncio
import asyncpg

import conf


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

#asyncio.run(init_table())
