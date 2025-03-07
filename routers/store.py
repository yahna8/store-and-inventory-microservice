from fastapi import APIRouter, HTTPException, Depends
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
    price: float
    category: str
    available: bool

    class Config:
        orm_mode = True


class PurchaseRequest(BaseModel):
    item_id: int


@router.get("/store", response_model=List[StoreItemResponse])
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
    query = db.query(StoreItem).filter(StoreItem.available == True, StoreItem.id.not_in(owned_items))

    if category:
        query = query.filter(StoreItem.category == category)

    return query.all()


@router.post("/store/purchase")
def purchase_item(
    request: PurchaseRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Purchase an item from the store for the authenticated user.
    """

    # Fetch the store item (ensuring it's available)
    store_item = db.query(StoreItem).filter(StoreItem.id == request.item_id, StoreItem.available == True).first()
    if not store_item:
        raise HTTPException(status_code=404, detail="Item not found or unavailable")

    # Check if the user already owns the item
    already_owned = db.query(Inventory).filter(Inventory.user_id == user_id, Inventory.item_id == store_item.id).first()
    if already_owned:
        raise HTTPException(status_code=400, detail="You already own this item")

    # Deduct points via the points service
    points_service_url = "http://points-service:8002/points/deduct"
    points_payload = {"user_id": user_id, "amount": store_item.price}
    try:
        response = requests.post(points_service_url, json=points_payload)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail="Failed to deduct points") from e

    # Add item to user's inventory (only storing item_id)
    new_inventory_entry = Inventory(user_id=user_id, item_id=store_item.id)
    db.add(new_inventory_entry)
    db.commit()

    return {"message": "Item purchased successfully", "item_id": store_item.id}
