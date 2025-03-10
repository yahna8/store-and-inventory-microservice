from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Inventory, StoreItem
from utils.auth import get_current_user
from typing import List

# Initialize router
router = APIRouter()

# Pydantic models for request validation
class InventoryResponse(BaseModel):
    item_id: int
    name: str
    description: str
    category: str

    class Config:
        orm_mode = True

class InventoryAddRequest(BaseModel):
    item_id: int

class EquipItemRequest(BaseModel):
    item_id: int

# Fetch user's inventory
@router.get("/inventory/{user_id}", response_model=List[InventoryResponse])
def get_inventory(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a list of items owned by the user.
    Joins inventory with store items for full details.
    """
    items = (
        db.query(StoreItem)
        .join(Inventory, StoreItem.id == Inventory.item_id)
        .filter(Inventory.user_id == user_id)
        .all()
    )

    return items

# Add an item to a user's inventory (used by Store Service)
@router.post("/inventory/add")
def add_item_to_inventory(
    request: InventoryAddRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Adds an item to the user's inventory if they don't already own it.
    Called by the store microservice after a purchase.
    """
    # Check if the item exists in the store
    store_item = db.query(StoreItem).filter(StoreItem.id == request.item_id).first()
    if not store_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Ensure the user doesn't already own this item
    existing_item = db.query(Inventory).filter(Inventory.user_id == user_id, Inventory.item_id == request.item_id).first()
    if existing_item:
        raise HTTPException(status_code=400, detail="User already owns this item")

    # Add item to inventory
    new_inventory_entry = Inventory(user_id=user_id, item_id=request.item_id)
    db.add(new_inventory_entry)
    db.commit()

    return {"message": "Item added to inventory", "item_id": request.item_id}

# Optional: Equip an item from inventory
@router.post("/inventory/equip")
def equip_item(
    request: EquipItemRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Equip an item (this does not remove it from inventory, just marks it as equipped).
    This endpoint can be expanded to track equipped items.
    """
    owned_item = db.query(Inventory).filter(Inventory.user_id == user_id, Inventory.item_id == request.item_id).first()
    if not owned_item:
        raise HTTPException(status_code=400, detail="User does not own this item")

    return {"message": f"Item {request.item_id} equipped!"}
