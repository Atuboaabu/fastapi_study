from fastapi import APIRouter

from schemas import UserPublic
from dependencies import ActiveUserDep

router = APIRouter(
    prefix = "/users",
    tags = ["users"]
)

@router.get(
    "/me",
    response_model = UserPublic
)
def get_me(
    current_user: ActiveUserDep
):
    return current_user