from sqlalchemy import Column, Integer, String, Float
from config.database import Base

class Jagath(Base):
    __tablename__ = "jagath"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    job= Column(String, nullable=False)
    
