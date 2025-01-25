from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import StoreItem
from utils.auth import get_current_user
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
    owned: bool

    class Config:
        orm_mode = True

class PurchaseRequest(BaseModel):
    item_id: int

# Routes

@router.get("/store", response_model=List[StoreItemResponse])
def get_store_items(category: str = None, db: Session = Depends(get_db)):
    """
    Retrieve available store items, optionally filtered by category.
    """
    query = db.query(StoreItem).filter(StoreItem.available == True)
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
    # Fetch the store item
    store_item = db.query(StoreItem).filter(StoreItem.id == request.item_id, StoreItem.available == True, StoreItem.owned == False).first()
    if not store_item:
        raise HTTPException(status_code=404, detail="Item not found or unavailable")

    # Deduct points via the points service
    points_service_url = "http://points-service:8002/points/deduct"
    points_payload = {"user_id": user_id, "amount": store_item.price}
    try:
        response = requests.post(points_service_url, json=points_payload)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail="Failed to deduct points") from e

    # Update the store item to mark it as owned
    store_item.owned = True
    db.commit()

    # Notify the inventory service
    inventory_service_url = "http://inventory-service:8001/inventory/add"
    inventory_payload = {
        "user_id": user_id,
        "item_id": store_item.id,
        "name": store_item.name,
        "description": store_item.description,
        "category": store_item.category,
    }
    try:
        inventory_response = requests.post(inventory_service_url, json=inventory_payload)
        inventory_response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to add item to inventory") from e

    return {"message": "Item purchased successfully", "item_id": store_item.id}