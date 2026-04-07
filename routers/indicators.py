from fastapi import APIRouter
from pydantic import BaseModel
from services.indicator_calculator import calculate_sma

router = APIRouter(prefix="/indicators", tags=["indicators"])

class SMAIn(BaseModel):
    values: list[float]
    window: int

@router.post("/sma")
def sma(data: SMAIn):
    return {"sma": calculate_sma(data.values, data.window)}
