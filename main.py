from fastapi import FastAPI
import os
from fastapi.concurrency import asynccontextmanager
from app.database import engine, Base, get_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth.auth_routers import router as auth_router
from app.routers.products.product_routers import router as product_router
from app.seed_data import seed_user

from fastapi.openapi.utils import get_openapi


# main.py
app = FastAPI() 

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(product_router)