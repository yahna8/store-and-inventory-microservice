from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import store, inventory  # Import your tasks router
from database import engine, Base
import uvicorn

app = FastAPI()

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Include the router
app.include_router(store.router)
app.include_router(inventory.router)

# Serve static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)
