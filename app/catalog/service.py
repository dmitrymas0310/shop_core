from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.catalog.repository import (
    ProductRepository, CategoryRepository,
    get_product_repository, get_category_repository
)
from app.catalog.schemas import (
    ProductCreate, ProductUpdate, ProductRead,
    CategoryCreate, CategoryUpdate, CategoryRead
)


class ProductService:
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo

    async def create_product(self, data: ProductCreate) -> ProductRead:
        if data.category_id:
            category = await self.category_repo.get_category_by_id(data.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )

        if data.rating is not None and (data.rating < 0 or data.rating > 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 0 and 5"
            )

        product = await self.product_repo.create_product(
            name=data.name,
            description=data.description,
            price=data.price,
            category_id=data.category_id,
            rating=data.rating
        )

        return ProductRead.model_validate(product)

    async def get_product(self, product_id: UUID) -> ProductRead:
        product = await self.product_repo.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        return ProductRead.model_validate(product)

    async def get_products(
            self,
            limit: int = 100,
            skip: int = 0
    ) -> List[ProductRead]:
        products = await self.product_repo.get_all_products(limit, skip)
        return [ProductRead.model_validate(p) for p in products]

    async def update_product(
            self,
            product_id: UUID,
            data: ProductUpdate
    ) -> ProductRead:
        product = await self.product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        update_data = data.model_dump(exclude_unset=True)

        if 'category_id' in update_data and update_data['category_id']:
            category = await self.category_repo.get_category_by_id(update_data['category_id'])
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )

        if 'rating' in update_data and update_data['rating'] is not None:
            if update_data['rating'] < 0 or update_data['rating'] > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rating must be between 0 and 5"
                )

        updated_product = await self.product_repo.update_product(
            product_id=product_id,
            data=update_data
        )

        return ProductRead.model_validate(updated_product)

    async def delete_product(self, product_id: UUID) -> bool:
        product = await self.product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        return await self.product_repo.delete_product(product_id)


class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    async def create_category(self, data: CategoryCreate) -> CategoryRead:
        if await self.category_repo.exists_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists"
            )

        category = await self.category_repo.create_category(name=data.name)
        return CategoryRead.model_validate(category)

    async def get_category(self, category_id: UUID) -> CategoryRead:
        category = await self.category_repo.get_category_by_id(category_id)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        return CategoryRead.model_validate(category)

    async def get_all_categories(
            self,
            limit: int = 100,
            skip: int = 0
    ) -> List[CategoryRead]:
        categories = await self.category_repo.get_all_categories(
            limit=limit,
            skip=skip
        )

        return [CategoryRead.model_validate(c) for c in categories]

    async def update_category(
            self,
            category_id: UUID,
            data: CategoryUpdate
    ) -> CategoryRead:
        category = await self.category_repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        if data.name != category.name:
            if await self.category_repo.exists_by_name(data.name, exclude_id=category_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Category with this name already exists"
                )

        updated_category = await self.category_repo.update_category(
            category_id=category_id,
            name=data.name
        )

        return CategoryRead.model_validate(updated_category)

    async def delete_category(self, category_id: UUID) -> bool:
        category = await self.category_repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        if category.products and len(category.products) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with products. Move or delete products first."
            )

        return await self.category_repo.delete_category(category_id)


async def get_product_service(
        product_repo: ProductRepository = Depends(get_product_repository),
        category_repo: CategoryRepository = Depends(get_category_repository)
) -> ProductService:
    return ProductService(product_repo, category_repo)


async def get_category_service(
        category_repo: CategoryRepository = Depends(get_category_repository)
) -> CategoryService:
    return CategoryService(category_repo)
