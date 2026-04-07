# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import market

app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets (Nifty 50 & Sensex)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allows your React frontend to call this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(market.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "version": "0.1.0",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}