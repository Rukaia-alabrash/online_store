from sqlalchemy import Column, Integer, String, ForeignKey,Text
from sqlalchemy.orm import relationship
from app.database import Base

class ProductTranslation(Base):
    __tablename__ = "product_translations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    lang_code = Column(String(3), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text,nullable=False)

    # relationships
    product = relationship("Product", back_populates="product_translations")