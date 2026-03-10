from sqlalchemy import Column, Integer, String, ForeignKey, Double, DateTime, Date, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

product_features = Table(
    'product_features',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('feature_id', Integer, ForeignKey('features.id'), primary_key=True)
)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    stock = Column(Integer, nullable=False)
    price = Column(Double,  nullable=False)
    average_rating = Column(Double,  nullable=False, default=0.0)
    discount_percentage = Column(Double,  nullable=True)
    discount_expiry = Column(Date,nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    category             = relationship("Category", back_populates="products")
    cart_items           = relationship("CartItem", back_populates="product")
    features     = relationship("Feature", secondary=product_features , back_populates="products")
    product_translations = relationship("ProductTranslation", back_populates="product")
    images               = relationship("ProductsImage", back_populates="product")
    wishlists            = relationship("Wishlist", back_populates="product")
    order_items          = relationship("OrderItem", back_populates="product")
