from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.reviews import crud, schemas
from app.users.models import User
from app.auth.service import get_current_user_dep
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=schemas.ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_dep),
):
    return await crud.create_review(db=db, review_in=review, user_id=current_user.id)

@router.get("/{review_id}", response_model=schemas.ReviewRead)
async def read_review(review_id: UUID, db: AsyncSession = Depends(get_session)):
    db_review = await crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

@router.get("/product/{product_id}", response_model=list[schemas.ReviewRead])
async def read_reviews_by_product(product_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_reviews_by_product(db, product_id)

@router.put("/{review_id}", response_model=schemas.ReviewRead)
async def update_review(
    review_id: UUID,
    review_update: schemas.ReviewUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_dep),
):
    db_review = await crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await crud.update_review(db, review_id, review_update)

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_dep),
):
    db_review = await crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await crud.delete_review(db, review_id)