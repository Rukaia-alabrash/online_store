from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Wishlist(Base):
    __tablename__ = "wishlists"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"),    nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # relationships
    user    = relationship("User",    back_populates="wishlist")
    product = relationship("Product", back_populates="wishlists")