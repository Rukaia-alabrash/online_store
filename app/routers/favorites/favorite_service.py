from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.favorite import Favorite
from app.models.product import Product
from app.models.user import User
from app.routers.favorites.favorite_schema import FavoriteProduct


class FavoriteService:

    @staticmethod
    def get_user_favorites(user: User, db: Session):
        favorites = (
            db.query(Favorite)
            .filter(Favorite.user_id == user.id)
            .all()
        )

        favorite_products = []

        for favorite in favorites:
            product = db.query(Product).filter(Product.id == favorite.product_id).first()
            if product:
                active_discount = (
                    product.discount_percentage
                    if product.discount_percentage is not None
                    and product.discount_expiry is not None
                    and product.discount_expiry > datetime.now(timezone.utc)
                    else None
                )

                favorite_products.append(FavoriteProduct(**{
                    "ProductId": product.id,
                    "name": product.product_translations[0].name,
                    "price": product.price,
                    "image": product.images[0].url,
                    "rating": product.average_rating,
                    "discountPercentage": active_discount
                }))
                    

        return {
            "products": favorite_products
        }
    @staticmethod
    def add_favorite(product_id: int, current_user: User, db: Session) -> Favorite:
        
        # 1. Make sure the product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        # 2. Guard against duplicates (the DB also has a UniqueConstraint)
        existing = (
            db.query(Favorite)
            .filter(
                Favorite.user_id == current_user.id,
                Favorite.product_id == product_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product is already in favorites",
            )

        # 3. Persist
        favorite = Favorite(user_id=current_user.id, product_id=product_id)
        db.add(favorite)
        db.commit()
        db.refresh(favorite)

        return favorite

    @staticmethod
    def remove_favorite(product_id: int, current_user: User, db: Session) -> bool:
       
        # 1. Make sure the product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        # 2. Find the favorite record
        favorite = (
            db.query(Favorite)
            .filter(
                Favorite.user_id == current_user.id,
                Favorite.product_id == product_id,
            )
            .first()
        )
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in favorites",
            )

        # 3. Delete
        db.delete(favorite)
        db.commit()

        return True