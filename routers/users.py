from fastapi import APIRouter

from schemas import UserPublic
from dependencies import ActiveUserDep, AdminUserDep

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

@router.get(
    "/admin-check",
    response_model = UserPublic
)
def get_admin(
    admin_user: AdminUserDep
):
    return admin_user