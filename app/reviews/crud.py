from sqlalchemy.orm import Session
from .models import Review
from .schemas import ReviewCreate, ReviewUpdate

def create_review(db: Session, review_in: ReviewCreate, user_id: int) -> Review:
    db_review = Review(**review_in.model_dump(), user_id=user_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_review(db: Session, review_id: int) -> Review | None:
    return db.query(Review).filter(Review.id == review_id).first()

def get_reviews_by_product(db: Session, product_id: int, skip: int = 0, limit: int = 100):
    return db.query(Review).filter(Review.product_id == product_id).offset(skip).limit(limit).all()

def update_review(db: Session, review_id: int, review_in: ReviewUpdate) -> Review | None:
    db_review = get_review(db, review_id)
    if not db_review:
        return None
    for key, value in review_in.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_review, key, value)
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int) -> bool:
    db_review = get_review(db, review_id)
    if not db_review:
        return False
    db.delete(db_review)
    db.commit()
    return True