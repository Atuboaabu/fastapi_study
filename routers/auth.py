from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from schemas import UserCreate, UserPublic, Token
from dependencies import SessionDep, SessionFactoryDep

from services import users, transaction
from services.result import UserResult
from security import create_access_token

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
    session_factory: SessionFactoryDep
):
    args = [user_data]

    user_result: UserResult | None = transaction.run_transaction_with_retry(
        session_factory,
        users.create_user_operation,
        args,
        3
    )
    assert user_result is not None
    return UserPublic(
        id = user_result.id,
        username = user_result.username,
        is_active = user_result.is_active,
        role = user_result.role
    )

@router.post(
    "/token",
    response_model=Token
)
def login_for_access_token(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    session: SessionDep
):
    user = users.authenticate_user(
        form_data.username,
        form_data.password,
        session
    )
    assert user.id is not None

    access_token = create_access_token(str(user.id))
    return Token(
        access_token = access_token,
        token_type = "bearer"
    )