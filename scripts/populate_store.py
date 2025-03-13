from database import SessionLocal
from models import StoreItem

db = SessionLocal()

items = [
    {"name": "Cat",
        "description": "A study buddy guaranteed to be lazier than you.",
        "image": "/static/cat.png",
        "price": 100,
        "category": "pets"},
    {"name": "Dog",
        "description": "Nothing could be more motivating than a puppy waiting for you to finish up your tasks for the day.",
        "image": "/static/dog.png",
        "price": 100,
        "category": "pets"},
    {"name": "Frog hat",
        "description": "What if... your cat could be a frog? Or your dog could be a frog? Now you can find out.",
        "image": "/static/frog-hat.png",
        "price": 200,
        "category": "accessory"}
]

for item in items:
    # Check if the item already exists
    existing_item = db.query(StoreItem).filter(StoreItem.name == item["name"]).first()
    if not existing_item:
        new_item = StoreItem(**item)
        db.add(new_item)
        print(f"Added: {item['name']}")
    else:
        print(f"Skipped (Already Exists): {item['name']}")

db.commit()
db.close()
print("Store items updated successfully!")
