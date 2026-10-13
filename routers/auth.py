from fastapi import APIRouter, status

from schemas import UserCreate, UserPublic
from dependencies import SessionDep

from services import users

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    session: SessionDep
):
    return users.create_user(
        user_data,
        session
    )