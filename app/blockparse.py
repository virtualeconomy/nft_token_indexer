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


class TokenOwnership:
    """
    Represents the token ownership table in db.
    """
    @staticmethod
    def get_create_ownership_stmt(table: str) -> str:
        return f"""
            INSERT INTO "{table}"
            (user_addr, token_idx)
            VALUES
            ($1, $2)
            ON CONFLICT DO NOTHING;
        """
    
    @staticmethod
    def get_remove_ownership_stmt(table: str) -> str:
        return f"""
            DELETE FROM "{table}"
            WHERE user_addr = $1
            AND token_idx = $2
        """
    
    @staticmethod
    def get_create_table_stmt(table: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS "{table}" (
            user_addr VARCHAR(255) NOT NULL,
            token_idx INTEGER NOT NULL,
            UNIQUE (user_addr, token_idx)
        );
        CREATE INDEX IF NOT EXISTS idx_token_idx ON "{table}"(token_idx);
        """


@dataclasses.dataclass
class NFTSendRecord:
   sender: str
   recipient: str
   ctrt_id: str
   tok_idx: str


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
        self.records: List["NFTSendRecord"] = []

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
                await self._update_db()

            start_height = end_height + 1
            await asyncio.sleep(conf.block_time)

    async def _prepare_table(self) -> None:
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                TokenOwnership.get_create_table_stmt(table=self.ctrt.ctrt_id),
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

        r = NFTSendRecord(
            sender=tx["proofs"][0]["address"],
            recipient=data_stack.entries[0].data.data,
            ctrt_id=tx["contractId"],
            tok_idx=data_stack.entries[1].data.data,
        )

        logger.debug(f"Found a NFT send record: {r}")
        self.records.append(r)
    
    async def _update_db(self) -> None:
        async with self.db_pool.acquire() as conn:

            for r in self.records:
                async with conn.transaction():
                    await conn.execute(
                        TokenOwnership.get_remove_ownership_stmt(table=r.ctrt_id),
                        r.sender,
                        r.tok_idx,
                    )
                    await conn.execute(
                        TokenOwnership.get_create_ownership_stmt(table=r.ctrt_id),
                        r.recipient,
                        r.tok_idx,
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

    logger.info(f"Connected to node: {host}")

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
