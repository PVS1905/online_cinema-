import os
from fastapi.security import OAuth2PasswordBearer
from database import get_db, UserGroupEnum, User
from security.token_manager import JWTAuthManager
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select


jwt_manage = JWTAuthManager(
    secret_key_access=os.getenv("SECRET_KEY_ACCESS"),
    secret_key_refresh=os.getenv("SECRET_KEY_REFRESH"),
    algorithm=os.getenv("JWT_SIGNING_ALGORITHM"),
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(token, jwt_manage._secret_key_access, algorithms=[jwt_manage._algorithm])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    print("SECRET_KEY_ACCESS:", os.getenv("SECRET_KEY_ACCESS"))

    return user


def require_group(allowed: list[UserGroupEnum]):
    async def checker(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        user_with_group = await db.scalar(
            select(User)
            .options(selectinload(User.group))
            .where(User.id == user.id)
        )

        if user_with_group.group.name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient access rights"
            )

        return user_with_group
    return checker


require_admin = require_group([UserGroupEnum.ADMIN])
require_moderator = require_group([UserGroupEnum.MODERATOR])
require_staff = require_group([UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR])
