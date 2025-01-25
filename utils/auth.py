import requests
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

auth_service_url = "http://localhost:8001/"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{auth_service_url}/login")

# Load the internal secret from the environment variables
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Add the internal secret to the request headers
    headers = {"X-Internal-Secret": INTERNAL_SECRET}
    response = requests.get(f"{auth_service_url}/validate", params={"token": token}, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    return response.json()["user_id"]