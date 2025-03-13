from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Inventory, StoreItem, EquippedItem
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


@router.get("/inventory")
def get_inventory(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)  # Use authenticated user
):
    """
    Retrieve a list of items owned by the authenticated user, including images.
    """
    items = (
        db.query(StoreItem)
        .join(Inventory, StoreItem.id == Inventory.item_id)
        .filter(Inventory.user_id == user_id)
        .all()
    )

    if not items:
        raise HTTPException(status_code=404, detail="No items found in inventory")

    # Ensure image URLs are set
    for item in items:
        if not item.image:
            if "cat" in item.name.lower():
                item.image = "/static/cat.png"
            elif "dog" in item.name.lower():
                item.image = "/static/dog.png"
            else:
                item.image = "/static/default.png"

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


@router.post("/inventory/equip")
def equip_item(
    request: EquipItemRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Equip an item (marks it as equipped in the database).
    This replaces any previously equipped item.
    """
    owned_item = db.query(Inventory).filter(
        Inventory.user_id == user_id, Inventory.item_id == request.item_id
    ).first()

    if not owned_item:
        raise HTTPException(status_code=400, detail="User does not own this item")

    # Remove any previously equipped item
    db.query(EquippedItem).filter(EquippedItem.user_id == user_id).delete()

    # Equip the new item
    new_equipped = EquippedItem(user_id=user_id, item_id=request.item_id)
    db.add(new_equipped)
    db.commit()  # ✅ Ensure data is saved

    equipped_item = db.query(StoreItem).filter(StoreItem.id == request.item_id).first()

    return {
        "message": f"Item {equipped_item.name} equipped!",
        "item_id": equipped_item.id,
        "name": equipped_item.name,
        "image": equipped_item.image or "/static/default.png"
    }


@router.get("/inventory/equipped")
def get_equipped_item(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Get the currently equipped item for the user.
    """
    equipped_item = db.query(EquippedItem).filter(EquippedItem.user_id == user_id).first()

    if not equipped_item:
        return {"message": "No item equipped", "image": "/static/default.png"}

    item = db.query(StoreItem).filter(StoreItem.id == equipped_item.item_id).first()

    return {
        "item_id": item.id,
        "name": item.name,
        "image": item.image or "/static/default.png"
    }
