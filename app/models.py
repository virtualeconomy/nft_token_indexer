from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TokenOwnership(Base):
    """
    CREATE TABLE [CONTRACT_ID] (
        user_addr VARCHAR(255) NOT NULL,
        token_idx INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        CONSTRAINT unique_user_addr_token_idx (user_addr, token_idx),
        INDEX idx_token_idx (token_idx),
    );
    """    
    user_addr = Column(String)
    token_idx = Column(Integer, index=True)
    amount = Column(Integer)

    __table_args__ = (
        UniqueConstraint("user_addr", "token_idx", name="unique_user_addr_token_idx"),
    )
