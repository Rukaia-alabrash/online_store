from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from .product import product_features

class Feature(Base):
    __tablename__ = "features"

    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(255),    nullable=False)
    lang_code = Column(String(3),    nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    products = relationship("Product", secondary=product_features ,back_populates="features")