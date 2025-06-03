import os

from fastapi.security import OAuth2PasswordBearer
from database import get_db
from security.token_manager import JWTAuthManager
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from database import (
    User,
)
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
    # print("Token received:", token)
    # print("Secret key used:", jwt_manage._secret_key_access)
    # print("Algorithm:", jwt_manage._algorithm)
    # print("SECRET_KEY_ACCESS:", os.getenv("SECRET_KEY_ACCESS"))
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

# async def get_current_user(
#                        token: str = Depends(oauth2_scheme),
#                        db: AsyncSession = Depends(get_db)):
#     try:
#         payload = jwt.decode(token, _secret_key_access, algorithms=[_algorithm])
#         user_id = payload.get("user_id")
#         if user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#     except Exception:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#
#     user = await db.get(User, user_id)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#
#     return user

# async def get_current_user(
#         token: str = Depends(jwt_manager.oauth2_scheme),
#         db: AsyncSession = Depends(get_db)
# ):
#     return await jwt_manager.current_user(token, db)
