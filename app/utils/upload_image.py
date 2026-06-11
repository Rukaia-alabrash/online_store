from fastapi import UploadFile, HTTPException , status
import cloudinary
import cloudinary.uploader
import os


cloudinary.config(
    cloud_name = os.getenv("CLOUD_NAME"),
    api_key = os.getenv("CLOUD_API_KEY"),   
    api_secret = os.getenv("CLOUD_API_SECRET")
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

async def upload_to_cloudinary(
    file: UploadFile,
    folder: str,
    max_size_mb: int = 5,
) -> dict:
    # Validate type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP images are allowed."
        )

    # Validate size
    contents =  await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size must not exceed {max_size_mb}MB."
        )

    # Upload
    result = cloudinary.uploader.upload(
        contents,
        folder=f"online_store/{folder}",
        resource_type="image",
    )

    return {
        "url": result["secure_url"]
    }