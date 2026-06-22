from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..services.user_service import UserService
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/users", tags=["用户服务"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordUpdate(BaseModel):
    new_password: str


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from jose import JWTError, jwt

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_service = UserService(db)
    user = user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)

    if user_service.get_user_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if user_service.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = user_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = user_service.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_info(
    email: Optional[EmailStr] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    update_data = {}
    if email:
        update_data["email"] = email

    user = user_service.update_user(current_user.id, **update_data)
    return user


@router.get("/list", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    user_service = UserService(db)
    return user_service.get_users(skip=skip, limit=limit)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = {}
    if user_data.email is not None:
        update_data["email"] = user_data.email
    if user_data.role is not None:
        if user_data.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="无效的角色")
        update_data["role"] = user_data.role
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active

    user = user_service.update_user(user_id, **update_data)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_service.delete_user(user_id)
    return {"message": "用户已删除"}


@router.put("/{user_id}/password")
async def update_user_password(
    user_id: int,
    password_data: PasswordUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_service.update_user_password(user_id, password_data.new_password)
    return {"message": "密码已更新"}
