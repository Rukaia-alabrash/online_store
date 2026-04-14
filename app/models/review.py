from sqlalchemy import Column, Integer, String, ForeignKey, Double, DateTime, Date, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    comment = Column(String, nullable=True)
    rating = Column(Double, nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

# relationships
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
