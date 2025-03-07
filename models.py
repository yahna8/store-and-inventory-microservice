from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base

class StoreItem(Base):
    __tablename__ = "store_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    available = Column(Integer, default=True)

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Assuming user_id is stored as email or a UUID
    item_id = Column(Integer, ForeignKey("store_items.id"), nullable=False)

    # Relationship (optional, for easy joins)
    item = relationship("StoreItem", backref="inventory_entries")
