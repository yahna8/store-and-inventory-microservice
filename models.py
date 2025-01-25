from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class StoreItem(Base):
    __tablename__ = "store_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    available = Column(Boolean, default=True)
    owned = Column(Boolean, default=False)  # Marks if the item has been purchased
