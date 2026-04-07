from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginIn):
    # stubbed authentication
    if data.username == "admin" and data.password == "password":
        token = create_access_token({"sub": data.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
