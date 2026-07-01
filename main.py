from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
import os
from fastapi.concurrency import asynccontextmanager
from app.database import engine, Base, get_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth.auth_routers import router as auth_router
from app.routers.products.product_routers import router as product_router
from app.routers.payments.payment_routers import router as payment_router
from app.seed_data import seed_user
from app.routers.users.user_routers import router as user_router
from app.routers.order.router import router as order_router
from app.routers.cart.cart_routers import router as cart_routers
from app.routers.profile.profile_routers import router as profile_router
from app.routers.favorites.favorite_routers import router as favorite_router
from app.routers.dashboard.dashboard_routers import router as dashboard_router


from fastapi.openapi.utils import get_openapi


# main.py
app = FastAPI(
    title="E-commerce API",
    version="1.0.0",
    servers=[
        {
            "url": "https://online-store-0jq7.onrender.com",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development"
        }
    ]
) 

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ecommerce-front-dusky-three.vercel.app"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(product_router)
app.include_router(payment_router)
app.include_router(order_router)
app.include_router(cart_routers)
app.include_router(profile_router)
app.include_router(favorite_router)
app.include_router(dashboard_router)
