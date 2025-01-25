from fastapi import FastAPI
from routers import store  # Import your tasks router
from database import engine, Base
import uvicorn

app = FastAPI()

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Include the router
app.include_router(store.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)
