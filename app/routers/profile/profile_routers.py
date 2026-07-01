from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers.profile.profile_schema import ProfileOut, ProfileUpdate, AvatarOut
from app.routers.profile.profile_serveice import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


# Get the authenticated user's profile (name, email, role, avatar, address, created_at).

@router.get("/", response_model=ProfileOut)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    profile = service.get_profile(current_user)
    return ProfileOut(**profile)


@router.put("/", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    profile = service.update_profile(current_user,db ,name=body.name, address=body.address, city=body.city, zip_code=body.zipCode)
    return ProfileOut(**profile)


@router.post("/avatar", response_model=AvatarOut)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    avatar_url = await service.update_avatar(current_user, file)
    return AvatarOut(avatar=avatar_url)