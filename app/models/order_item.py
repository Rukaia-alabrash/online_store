from sqlalchemy import Column, Integer, String, ForeignKey,Double
from sqlalchemy.orm import relationship
from app.database import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"),  nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"),  nullable=True)
    price      = Column(Double,  nullable=True)
    quantity   = Column(Integer, nullable=True)

    # relationships
    receipt = relationship("Receipt", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")