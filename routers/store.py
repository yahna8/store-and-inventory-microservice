from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from models import StoreItem
from utils.auth import get_current_user
from models import StoreItem, Inventory
import requests


# Initialize router
router = APIRouter()

# Pydantic models for request/response validation
class StoreItemResponse(BaseModel):
    id: int
    name: str
    description: str
    image: str
    price: float
    category: str
    available: int

    class Config:
        orm_mode = True


class PurchaseRequest(BaseModel):
    item_id: int


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import StoreItem, Inventory
from utils.auth import get_current_user
from typing import List

router = APIRouter()

@router.get("/store")
def get_store_items(
    category: str = None, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Retrieve available store items, filtering out those the user already owns.
    """

    # Get the list of item IDs the user already owns
    owned_items = db.query(Inventory.item_id).filter(Inventory.user_id == user_id).subquery()

    # Query only items NOT in the user's inventory
    query = db.query(StoreItem).filter(StoreItem.available == 1, StoreItem.id.not_in(owned_items))

    if category:
        query = query.filter(StoreItem.category == category)

    store_items = query.all()

    # Ensure each store item has an image URL pointing to the static folder
    for item in store_items:
        if not item.image:
            if "cat" in item.name.lower():
                item.image = "/static/cat.png"
            elif "dog" in item.name.lower():
                item.image = "/static/dog.png"
            else:
                item.image = "/static/default.png"

    return store_items


@router.post("/store/purchase")
def purchase_item(
    request: PurchaseRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """
    Purchase an item from the store for the authenticated user.
    """

    # Fetch the store item (ensuring it's available)
    store_item = db.query(StoreItem).filter(StoreItem.id == request.item_id, StoreItem.available == 1).first()
    if not store_item:
        raise HTTPException(status_code=404, detail="Item not found or unavailable")

    # Check if the user already owns the item
    already_owned = db.query(Inventory).filter(Inventory.user_id == user_id, Inventory.item_id == store_item.id).first()
    if already_owned:
        raise HTTPException(status_code=400, detail="You already own this item")

    # ✅ NO POINTS DEDUCTION IN BACKEND

    # Add item to user's inventory
    new_inventory_entry = Inventory(user_id=user_id, item_id=store_item.id)
    db.add(new_inventory_entry)
    db.commit()

    return {"message": "Item purchased successfully", "item_id": store_item.id}



@router.post("/store/add")
def add_store_item(
    name: str,
    description: str,
    price: float,
    category: str,
    db: Session = Depends(get_db),
):
    """
    Adds a new item to the store.
    """
    new_item = StoreItem(
        name=name,
        description=description,
        price=price,
        category=category,
        available=True
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"message": "Item added successfully", "item_id": new_item.id}
