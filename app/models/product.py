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
    stock = Column(Integer, nullable=False)
    price = Column(Double,  nullable=False)
    average_rating = Column(Double,  nullable=False, default=0.0)
    reviews_count = Column(Integer,  nullable=False, default=0)
    discount_percentage = Column(Double,  nullable=True)
    discount_expiry = Column(DateTime(timezone=True),nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    cart_items           = relationship("CartItem", back_populates="product")
    features             = relationship("Feature", secondary=product_features , back_populates="products")
    product_translations = relationship("ProductTranslation", back_populates="product", cascade="all, delete-orphan")
    images               = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    favorites            = relationship("Favorite", back_populates="product")
    order_items          = relationship("OrderItem", back_populates="product")
    reviews              = relationship("Review", back_populates="product")

