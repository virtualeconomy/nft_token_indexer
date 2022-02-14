from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from fastapi_asyncalchemy.db.base import Base


class Token(Base):
    __tablename__ = "CF2PaG83haRCSMP9s9M2XegaJUPqwkfarxr"

    token_idx = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_addr = Column(String, unique=True)
    amount = Column(Integer)
