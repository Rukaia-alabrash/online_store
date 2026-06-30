from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.shipping_address import ShippingAddress
from app.utils.upload_image import upload_to_cloudinary


class ProfileService:
    def __init__(self, db: Session):
        self.db = db


    def _get_latest_address(self, user_id: int) -> ShippingAddress | None:
        return (
            self.db.query(ShippingAddress)
            .filter(ShippingAddress.user_id == user_id)
            .order_by(ShippingAddress.id.desc())
            .first()
        )


    def _build_profile_dict(self, current_user: User) -> dict:
        """
        Builds a plain dict combining User fields with the latest
        ShippingAddress.address, without ever attaching new attributes
        to the User ORM instance and without touching the database schema.
        """
        latest_address = self._get_latest_address(current_user.id)
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "address": latest_address.address if latest_address else None,
            "city": latest_address.city if latest_address else None,
            "zipCode": latest_address.zip_code if latest_address else None,
            "created_at": current_user.created_at,
        }

    def get_profile(self, current_user: User) -> dict:
        return self._build_profile_dict(current_user)

    def update_profile(self, current_user: User, db: Session, name: str | None, address: str | None, city:str , zip_code:str) -> dict:
        if name is not None:
            current_user.name = name

        if address is not None:
            latest_address = self._get_latest_address(current_user.id)
            if latest_address is None:
                latest_address = ShippingAddress(
                user_id=current_user.id,
                full_name=name,
                address=address,
                city=city,
                zip_code=zip_code,
            )
            else:
                latest_address.address = address
                latest_address.city = city
                latest_address.zip_code = zip_code
                
                db.add(latest_address)
                db.flush()

        self.db.commit()
        self.db.refresh(current_user)

        return self._build_profile_dict(current_user)

    async def update_avatar(self, current_user: User, file: UploadFile) -> str:
        result = await upload_to_cloudinary(file, folder="avatars")
        current_user.avatar = result["url"]
        self.db.commit()
        self.db.refresh(current_user)
        return current_user.avatar