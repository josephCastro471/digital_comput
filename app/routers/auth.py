from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import get_settings
from app.core.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != settings.admin_username or not verify_password(
        form_data.password, settings.admin_password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasena incorrectos",
        )

    access_token = create_access_token(subject=settings.admin_username)
    return {"access_token": access_token, "token_type": "bearer"}
