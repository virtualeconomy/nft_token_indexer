# block parsing logic be here
import asyncio
import enum
from typing import Any, Dict, List

import base58
from sqlalchemy import insert

import py_v_sdk as pv
from py_v_sdk.data_entry import DataStack as PVDataStack

from log import logger
import conf
from base import engine, Base


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

    @property
    def send_func_idx(self) -> int:
        if self.is_nft_ctrt:
            return 2
        elif self == self.TOKEN_NO_SPLIT:
            return 3
        elif self in (
            self.TOKEN_WITH_SPLIT,
            self.TOKEN_V2_WHITELIST,
            self.TOKEN_V2_BLACKLIST,
        ):
            return 4
        else:
            raise Exception("Function index for send is unknown")
    
    @property
    def is_nft_ctrt(self) -> bool:
        return self in (
            self.NFT,
            self.NFT_V2_BLACKLIST,
            self.NFT_V2_WHITELIST,
        )
    
    @property
    def is_tok_ctrt(self) -> bool:
        return self in (
            self.TOKEN_NO_SPLIT,
            self.TOKEN_WITH_SPLIT,
            self.TOKEN_V2_WHITELIST,
            self.TOKEN_V2_BLACKLIST,
        )

    @classmethod
    def from_str(cls, s: str) -> "TokenContractType":
        return cls(s)
    
    @classmethod
    async def from_ctrt_id(cls, ctrt_id: str, api: pv.NodeAPI) -> "TokenContractType":
        ctrt_type_str = await get_ctrt_type(ctrt_id, api)
        return cls.from_str(ctrt_type_str)


async def get_ctrt_info(ctrt_id: str, api: pv.NodeAPI) -> Dict[str, Any]:
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
    edpt = f"/contract/info/{ctrt_id}"
    return await api.get(edpt)


async def get_init_block_height(ctrt_id: str, api: pv.NodeAPI) -> int:
    resp = await get_ctrt_info(ctrt_id, api)
    return resp["height"]


async def get_ctrt_type(ctrt_id: str, api: pv.NodeAPI) -> str:
    resp = await get_ctrt_info(ctrt_id, api)
    return resp["type"]


async def get_block_at(height: int, api: pv.NodeAPI) -> Dict[str, Any]:
    edpt = f"/blocks/at/{height}"
    resp = await api.get(edpt)
    return resp


async def get_blocks(start_height: int, end_height: int, api: pv.NodeAPI) -> List[Dict[str, Any]]:
    edpt = f"/blocks/seq/{start_height}/{end_height}"
    resp = await api.get(edpt)
    return resp


async def is_valid_send_token_tx(tx: Dict[str, Any], api: pv.NodeAPI) -> bool:
    try:
        has_success_status = tx["status"] == TX_STATUS_SUCCESS
        if not has_success_status:
            return False

        is_exec_ctrt_tx = tx["type"] == EXEC_CTRT_TX_TYPE
        if not is_exec_ctrt_tx:
            return False

        ctrt_id = tx["contractId"]
        ctrt_type = await TokenContractType.from_ctrt_id(ctrt_id, api)

        is_send_func = ctrt_type.send_func_idx == tx["functionIndex"]
        if not is_send_func:
            return False

    except (ValueError, KeyError):
        return False

    return True


async def main():
    host = f"http://{conf.node_ip}:{conf.node_port}"

    logger.info("Starting the main loop.")

    try:
        api = await pv.NodeAPI.new(host)
        chain = pv.Chain(api)

        for ctrt_id in conf.contract_ids:

            logger.info(f"Monitoring contract: {ctrt_id}")

            init_height = await get_init_block_height(ctrt_id, api)
            latest_height = await chain.height

            for h in range(init_height, latest_height + 1 - UNCONFIRMED_THRESHOLD, MAX_BLOCKS_PER_REQ):
                blocks = await get_blocks(h, h + MAX_BLOCKS_PER_REQ - 1, api)

                for b in blocks:
                    if b["transaction count"] <= 1:
                        continue
                    txs = b["transactions"]

                    for tx in txs:
                        if not await is_valid_send_token_tx(tx, api):
                            continue
                        if tx["contractId"] != ctrt_id:
                            continue
                        
                        func_data = tx["functionData"]
                        data_stack = PVDataStack.deserialize(
                            base58.b58decode(func_data)
                        )
                        recipient = data_stack.entries[0].data.data

                        ctrt_type = await TokenContractType.from_ctrt_id(ctrt_id, api)

                        tok_idx = 0
                        amount = 1

                        if ctrt_type.is_nft_ctrt:
                            tok_idx = data_stack.entries[1].data.data

                        if ctrt_type.is_tok_ctrt:
                            amount = data_stack.entries[1].data.data

                        logger.debug(f'''Found a relevant txn! \n
                                "recipient": {recipient},
                                "token_index": {tok_idx},
                                "amount": {amount}'''
                               )
                        
                        table = Base.metadata.tables[ctrt_id]

                        stmt = (
                            insert(table).
                            values(user_addr=recipient, token_idx=tok_idx, amount=amount)
                        )

                        print(stmt)

                        async with engine.begin() as conn:
                            conn.execute(stmt)

    finally:
        await api.sess.close()


if __name__ == "__main__":
    asyncio.run(main())
