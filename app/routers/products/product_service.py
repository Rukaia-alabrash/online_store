from fastapi import APIRouter, Depends, HTTPException, Header, status , UploadFile , File
from fastapi.params import  Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , desc 

from typing import Annotated, List
from datetime import datetime

from app.database import get_db

from app.dependencies import require_admin
from .product_schema import ProductIn, ProductListOut , PaginationOut, ProductOut, ProductUpdate

from app.models import Product , ProductTranslation ,Category, Feature , ProductImage , Feature
from app.utils.upload_image import upload_to_cloudinary


def filter_products(
  q : Query,
  lang: str,
  category: str = None,
  search: str = None,
  minPrice: float = None,
  maxPrice: float = None,
  rating: float = None      
):
    
    q = q.join(Product.product_translations).filter(ProductTranslation.lang_code == lang)

    if category:
        q = q.join(ProductTranslation.category) \
            .filter(
                Category.name.ilike(f"%{category}%")
            )
    if search:
        q = q.filter(
            or_(ProductTranslation.name.ilike(f"%{search}%"),
                 ProductTranslation.description.ilike(f"%{search}%"))
        )
    if minPrice is not None:
        q = q.filter(Product.price >= minPrice)
    if maxPrice is not None:
        q = q.filter(Product.price <= maxPrice)
    if rating is not None:
        q = q.filter(Product.average_rating >= rating)
    return q


def _serialize(product: Product, lang: str) -> ProductOut:
    """Convert ORM Product → ProductOut using the requested language."""

    # Translation: name + description
    translation = next(
        (t for t in product.product_translations if t.lang_code == lang), None
    )

    if not translation:
        raise HTTPException(status_code=404, detail="Product not found in the requested language")

    # Images
    primary_image = next((img.url for img in product.images if img.is_primary), "")
    all_images    = [img.url for img in product.images if not img.is_primary]
    if not primary_image and all_images:
        primary_image = all_images[0]

    # Features filtered by lang
    features = [f.name for f in product.features if f.lang_code == lang]

    return ProductOut(
        id=product.id,
        name=translation.name,
        description=translation.description,
        price=product.price,
        category=translation.category.name,
        image=primary_image,
        images=all_images,
        rating=product.average_rating,
        reviews=product.reviews_count,
        stock=product.stock,
        features=features,
        discountPercentage=product.discount_percentage or 0,
        discountExpiry=product.discount_expiry,
        createdAt=product.created_at,
        updatedAt=product.updated_at,
    )


def _eager_query(db: Session):
    """Base query with all relationships eager-loaded."""
    return db.query(Product).options(
        joinedload(Product.product_translations),
        joinedload(Product.images),
        joinedload(Product.features),
        joinedload(Product.reviews)
    )


class ProductService:
    @staticmethod
    def list_products(lang:str,
        page : int ,limit: int , category: str ,
        search : str ,
        minPrice: float,
        maxPrice: float,
        rating: float,
        sortBy: str,
        sortOrder:str,
        db:Session
    )-> ProductListOut:
        
        q = _eager_query(db)

        q = filter_products(q,lang ,category, search, minPrice, 
        maxPrice, rating)

        # sorting
        if sortBy in ['price','rating']:
            sortBy = 'average_rating' if sortBy == 'rating' else sortBy
            sort_column = getattr(Product, sortBy)
            if sortOrder == 'desc':
                q = q.order_by(desc(sort_column))
            else:
                q = q.order_by(sort_column)
        elif sortBy == 'name':
            if sortOrder == 'desc':
                q = q.join(Product.product_translations).order_by(desc(ProductTranslation.name))
            else:
                q = q.join(Product.product_translations).order_by(ProductTranslation.name)

        # pagination
        total = q.distinct().count()
        skip = (page - 1) * limit
        products = q.offset(skip).limit(limit).all()

        serialized = [_serialize(p, lang) for p in products if _serialize(p, lang) is not None]

        # all categories
        all_categories = db.query(Category).filter(Category.lang_code == lang).all()   
        categories = list({c.name for c in all_categories})

        return {
            'products': serialized,
            'categories': categories,
            'pagination': PaginationOut(
                page=page,
                limit=limit,
                total=total,
                totalPages=(total + limit - 1) // limit
            )
        }
    

    @staticmethod
    def list_discounted_products(lang:str, db:Session)-> List[ProductOut]:
         products = _eager_query(db).filter(Product.discount_percentage > 0.0 , Product.discount_expiry > datetime.now()).all()
         return [_serialize(p, lang) for p in products]
    

    @staticmethod
    def get_product(product_id:int, lang:str, db:Session)-> ProductOut:
        product = _eager_query(db).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return _serialize(product, lang)
    

    @staticmethod
    def create_product(data: ProductIn, lang:str, db:Session)-> ProductOut:
        features = data.features or []
        if features:
            # get the existing features
            existing_features = db.query(Feature).filter(Feature.name.in_(features), Feature.lang_code == lang).all()
            existing_names = {f.name for f in existing_features}
            # create new features
            new_features = [Feature(name = name, lang_code =lang) for name in features if name not in existing_names]
            # combine the features
            all_features = existing_features + new_features

        category = db.query(Category).filter(Category.name == data.category, Category.lang_code == lang).first()
        if not category:
            category = Category(name = data.category, lang_code = lang)
            db.add(category)
            db.commit()
            db.refresh(category)

        product = Product(
            price=data.price,
            stock=data.stock,
            discount_percentage=data.discountPercentage,
            discount_expiry = data.discountExpiry,
        )
        product.features = all_features
        db.add(product)
        db.flush()

        translation = ProductTranslation(
            product_id=product.id,
            category_id=category.id,
            lang_code=lang,
            name=data.name,
            description=data.description
        )
        db.add(translation)
        db.commit()
        db.refresh(product)

        return _serialize(product, lang)
    

    @staticmethod
    async def upload_product_images(product_id:int, files: List[UploadFile], db:Session)-> dict:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Product not found")
        
        for index , file in enumerate(files):
            result = await upload_to_cloudinary(file, folder="products", max_size_mb= 5)

            db.add(ProductImage(
                product_id  = product_id,
                url = result['url'],
                is_primary = (index == 0)
            ))
        db.commit()
        return {"message": "Images uploaded successfully"}
    

    @staticmethod
    def update_product(product_id:int, data:ProductUpdate, lang:str, db:Session)-> ProductOut:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        if data.price is not None:
            product.price = data.price
        if data.stock is not None:
            product.stock = data.stock
        if data.discountPercentage is not None:
            product.discount_percentage = data.discountPercentage
        if data.discountExpiry is not None:
            product.discount_expiry = data.discountExpiry

        if data.name or data.description:
            translation = db.query(ProductTranslation).filter(
                ProductTranslation.product_id == product_id,
                ProductTranslation.lang_code == lang
            ).first()

            if not translation:
                category_id = db.query(Category.id).filter(
                    Category.name == data.category,
                    Category.lang_code == lang
                ).scalar()
                translation = ProductTranslation(
                    product_id=product_id,
                    lang_code=lang,
                    name=data.name,
                    description=data.description,
                    category_id=category_id
                )
                db.add(translation)
            else:
                if data.name:
                    translation.name = data.name
                if data.description:
                    translation.description = data.description
                if data.category:
                    category_id = db.query(Category.id).filter(
                        Category.name == data.category,
                        Category.lang_code == lang
                    ).scalar()
                    if category_id:
                        translation.category_id = category_id

        if data.features is not None:
            existing_features = db.query(Feature).filter(
                Feature.name.in_(data.features),
                Feature.lang_code == lang
            ).all()
            existing_names = {f.name for f in existing_features}

            new_features = [Feature(name=name, lang_code=lang) for name in data.features if name not in existing_names]

            # create new features
            if new_features:
                db.add_all(new_features)
                db.flush() 

            product.features = existing_features + new_features

        db.commit()
        db.refresh(product)

        return _serialize(product,lang)
    

    @staticmethod
    def delete_product(product_id:int, db:Session)-> dict:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        db.delete(product)
        db.commit()
        return {"message": "Product deleted successfully"}