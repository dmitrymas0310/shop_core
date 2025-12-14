from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_session
from . import crud, schemas
from app.auth.service import get_current_user_dep #???
from app.users.models import User

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=schemas.ReviewRead, status_code=status.HTTP_201_CREATED)
def create_new_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_dep)
):
    return crud.create_review(db=db, review_in=review, user_id=current_user.id)

@router.get("/{review_id}", response_model=schemas.ReviewRead)
def read_review(review_id: int, db: Session = Depends(get_session)):
    db_review = crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

@router.get("/product/{product_id}", response_model=list[schemas.ReviewRead])
def read_reviews_by_product(product_id: int, db: Session = Depends(get_session)):
    return crud.get_reviews_by_product(db, product_id)

@router.put("/{review_id}", response_model=schemas.ReviewRead)
def update_existing_review(
    review_id: int,
    review_update: schemas.ReviewUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_dep)
):
    db_review = crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this review")
    return crud.update_review(db, review_id, review_update)

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_review(
    review_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_dep)
):
    db_review = crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    crud.delete_review(db, review_id)