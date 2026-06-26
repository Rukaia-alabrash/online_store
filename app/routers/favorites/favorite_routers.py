from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers.favorites.favorite_schema import FavoriteListOut, FavoriteOut 
from app.routers.favorites.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.get("/", response_model=FavoriteListOut, summary="Get current user's favorites")
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FavoriteService.get_user_favorites(current_user, db)

@router.post(
    "/{product_id}",
    response_model=FavoriteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to favorites",
)
def add_favorite(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    return FavoriteService.add_favorite(product_id, current_user, db)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a product from favorites",
)
def remove_favorite(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    return FavoriteService.remove_favorite(product_id, current_user, db)