from fastapi import APIRouter

from schemas import UserPublic
from dependencies import CurretUserDep

router = APIRouter(
    prefix = "/users",
    tags = ["users"]
)

@router.get(
    "/me",
    response_model = UserPublic
)
def get_me(
    current_user: CurretUserDep
):
    return current_user