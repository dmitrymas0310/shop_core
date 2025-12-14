from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from uuid import UUID
from .models import Review
from .schemas import ReviewCreate, ReviewUpdate

async def create_review(db: AsyncSession, review_in: ReviewCreate, user_id: UUID) -> Review:
    db_review = Review(**review_in.model_dump(), user_id=user_id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

async def get_review(db: AsyncSession, review_id: UUID) -> Review | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()

async def get_reviews_by_product(db: AsyncSession, product_id: UUID, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Review)
        .where(Review.product_id == product_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_review(db: AsyncSession, review_id: UUID, review_in: ReviewUpdate) -> Review | None:
    db_review = await get_review(db, review_id)
    if not db_review:
        return None
    for key, value in review_in.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_review, key, value)
    await db.commit()
    await db.refresh(db_review)
    return db_review

async def delete_review(db: AsyncSession, review_id: UUID) -> bool:
    db_review = await get_review(db, review_id)
    if not db_review:
        return False
    await db.delete(db_review)
    await db.commit()
    return True