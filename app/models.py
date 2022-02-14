from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Token(Base):

    token_idx = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_addr = Column(String, unique=True)
    amount = Column(Integer)
