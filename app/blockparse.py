# block parsing logic be here
import asyncio
import asyncpg
import dataclasses
import enum
from typing import Any, Dict, List, Optional

import base58
import py_v_sdk as pv
from py_v_sdk.data_entry import DataStack as PVDataStack

from log import logger
import conf


MAX_BLOCKS_PER_REQ = 100
EXEC_CTRT_TX_TYPE = 9
TX_STATUS_SUCCESS = "Success"
# The number of blocks traced back from the latest block to be considered unconfirmed
UNCONFIRMED_THRESHOLD = 15


class TokenContractType(enum.Enum):
    NFT = "NonFungibleContract"
    NFT_V2_BLACKLIST = "NFTContractWithBlacklist"
    NFT_V2_WHITELIST = "NFTContractWithWhitelist"

    TOKEN_NO_SPLIT = "TokenContract"
    TOKEN_WITH_SPLIT = "TokenContractWithSplit"
    TOKEN_V2_WHITELIST = "TokenContractWithWhitelist"
    TOKEN_V2_BLACKLIST = "TokenCtrtWithoutSplitV2BlackList"


@dataclasses.dataclass
class TokenOwnershipRecord:
    user_addr: str
    token_idx: int = 0
    amount: int = 0

    @classmethod
    def get_insert_stmt(cls, table: str) -> str:
        return f"""
            INSERT INTO "{table}"
            (user_addr, token_idx, amount)
            VALUES
            ($1, $2, $3);
        """
    
    @classmethod
    def get_create_table_stmt(cls, table: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS "{table}" (
            user_addr VARCHAR(255) NOT NULL,
            token_idx INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            UNIQUE (user_addr, token_idx)
        );
        CREATE INDEX idx_token_idx ON "{table}"(token_idx);
        """

    @property 
    def insert_arg(self) -> tuple:
        return (self.user_addr, self.token_idx, self.amount)


class TokenContract:

    def __init__(self, ctrt_id: str, api: pv.NodeAPI) -> None:
        self.ctrt_id = ctrt_id
        self.api = api
        self._info: Dict[str, Any] = {}
        self._type: Optional["TokenContractType"] = None

    @property
    async def info(self) -> Dict[str, Any]:
        """
        Example response.
        {
            "contractId": "CF5HTwYNrZDFBG371jfTiKpNPfRpEHdgj6B",
            "transactionId": "DwySUmHwTbaRBMBXjk6PmXKvow1wLi6bhpxteK2Smrph",
            "type": "TokenContractWithWhitelist",
            ...
            "height": 1009393
        }
        """    
        if not self._info:
            edpt = f"/contract/info/{self.ctrt_id}"
            self._info = await self.api.get(edpt)

        return self._info
    
    @property
    async def init_height(self) -> int:
        info = await self.info
        return info["height"]
    
    @property
    async def type(self) -> "TokenContractType":
        if not self._type:
            info = await self.info
            self._type = TokenContractType(info["type"])

        return self._type

    @property
    async def is_nft_ctrt(self) -> bool:
        return (await self.type) in (
            TokenContractType.NFT,
            TokenContractType.NFT_V2_BLACKLIST,
            TokenContractType.NFT_V2_WHITELIST,
        )
    
    @property
    async def is_tok_ctrt(self) -> bool:
        return (await self.type) in (
            TokenContractType.TOKEN_NO_SPLIT,
            TokenContractType.TOKEN_WITH_SPLIT,
            TokenContractType.TOKEN_V2_WHITELIST,
            TokenContractType.TOKEN_V2_BLACKLIST,
        )
    
    @property
    async def send_func_idx(self) -> int:
        if (await self.is_nft_ctrt):
            return 2
        elif (await self.type) == TokenContractType.TOKEN_NO_SPLIT:
            return 3
        elif (await self.type) in (
            TokenContractType.TOKEN_WITH_SPLIT,
            TokenContractType.TOKEN_V2_WHITELIST,
            TokenContractType.TOKEN_V2_BLACKLIST,
        ):
            return 4
        else:
            raise Exception("Function index for send is unknown")


class SendTokenTxMonitor:

    def __init__(self, ctrt_id: str, chain: pv.Chain, db_pool: asyncpg.Pool) -> None:
        self.chain = chain
        self.ctrt = TokenContract(ctrt_id, chain.api)
        self.db_pool = db_pool
        self.records: List["TokenOwnershipRecord"] = []

    async def start(self):
        logger.info(f"Preparing table: {self.ctrt.ctrt_id}")
        await self._prepare_table()

        logger.info(f"Start monitoring contract: {self.ctrt.ctrt_id}")

        start_height = await self.ctrt.init_height

        while True:
            latest_height = await self.chain.height
            end_height = latest_height - UNCONFIRMED_THRESHOLD

            for h in range(start_height, end_height + 1, MAX_BLOCKS_PER_REQ):
                blocks = await self.chain.get_blocks_within(h, h + MAX_BLOCKS_PER_REQ - 1)
                await self._parse_blocks(blocks)
                await self._insert_records()

            start_height = end_height + 1
            await asyncio.sleep(conf.block_time)

    async def _prepare_table(self) -> None:
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                TokenOwnershipRecord.get_create_table_stmt(table=self.ctrt.ctrt_id),
            )

    async def _parse_blocks(self, blocks: List[Dict[str, Any]]) -> None:
        for b in blocks:
            if b["transaction count"] <= 1:
                continue
            await self._parse_txs(b["transactions"])
    
    async def _parse_txs(self, txs: List[Dict[str, Any]]) -> None:
        for tx in txs:
            if not await self._is_desired_tx(tx):
                continue
            await self._parse_tx(tx)

    async def _parse_tx(self, tx: Dict[str, Any]) -> None:
        func_data = tx["functionData"]
        data_stack = PVDataStack.deserialize(
            base58.b58decode(func_data)
        )
        recipient = data_stack.entries[0].data.data

        r = TokenOwnershipRecord(
            user_addr=recipient
        )

        if (await self.ctrt.is_nft_ctrt):
            r.token_idx = data_stack.entries[1].data.data
        if (await self.ctrt.is_tok_ctrt):
            r.amount = data_stack.entries[1].data.data

        logger.debug(f"Found a user token ownership record: {r}")
        self.records.append(r)
    
    async def _insert_records(self) -> None:
        async with self.db_pool.acquire() as conn:
            await conn.executemany(
                TokenOwnershipRecord.get_insert_stmt(table=self.ctrt.ctrt_id),
                [
                    r.insert_arg
                    for r in self.records
                ]
            )

        self.records.clear()
    
    async def _is_desired_tx(self, tx: Dict[str, Any]) -> bool:
        if not tx["status"] == TX_STATUS_SUCCESS:
            return False

        if not tx["type"] == EXEC_CTRT_TX_TYPE:
            return False

        if not tx["contractId"] == self.ctrt.ctrt_id:
            return False
        
        if not tx["functionIndex"] == (await self.ctrt.send_func_idx):
            return False

        return True


async def main():
    host = f"http://{conf.node_ip}:{conf.node_port}"
    api = await pv.NodeAPI.new(host)
    chain = pv.Chain(api)
    db_pool = await asyncpg.create_pool(
        user=conf.db_user,
        password=conf.db_pass,
        database=conf.db,
        host=conf.db_ip,
    )

    try:
        await asyncio.gather(*[
            SendTokenTxMonitor(ctrt_id, chain, db_pool).start()
            for ctrt_id in conf.contract_ids
        ])        

    finally:
        await api.sess.close()


if __name__ == "__main__":
    asyncio.run(main())
