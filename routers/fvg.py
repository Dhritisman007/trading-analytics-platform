from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/fvg", tags=["fvg"])

class FVGIn(BaseModel):
    highs: list[float]
    lows: list[float]

@router.post("/compute")
def compute_fvg(data: FVGIn):
    # simple placeholder: gaps where high > low by threshold
    gaps = [h - l for h, l in zip(data.highs, data.lows)]
    return {"gaps": gaps}
