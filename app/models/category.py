from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    __tablename__ = 'categories'

    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(255),    nullable=False)
    lang_code = Column(String(3),    nullable=False)
    parent_id = Column(Integer, ForeignKey("category.id"), nullable=True)

    # relationships
    products  = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")