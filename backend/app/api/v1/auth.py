"""
Authentication API.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.response import ApiResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=dict,
    status_code=201,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):

    service = UserService(db)

    user = service.create_user(request)

    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="User registered successfully.",
    )


@router.post(
    "/login",
    response_model=dict,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):

    service = AuthService(db)

    token = service.login(
        request.email,
        request.password,
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    return ApiResponse.success(
        data=TokenResponse(**token),
        message="Login successful.",
    )


@router.get(
    "/me",
    response_model=dict,
)
def current_user(
    current_user=Depends(
        get_current_user,
    ),
):

    return ApiResponse.success(
        data=current_user,
        message="Current user fetched successfully.",
    )