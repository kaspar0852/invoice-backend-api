from typing import List
import uuid
import bcrypt
from fastapi import HTTPException, status
from app.models.user import User
from app.repositories.user import UserRepositoryInterface
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepositoryInterface):
        self.repository = repository

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self.repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found",
            )
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return await self.repository.list_users(skip=skip, limit=limit)

    async def create_user(self, schema: UserCreate) -> User:
        existing = await self.repository.get_by_email(schema.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed = self.hash_password(schema.password)
        db_user = User(
            email=schema.email,
            hashed_password=hashed,
            is_active=schema.is_active,
        )
        return await self.repository.create(db_user)

    async def update_user(self, user_id: uuid.UUID, schema: UserUpdate) -> User:
        db_user = await self.get_user_by_id(user_id)

        if schema.email is not None and schema.email != db_user.email:
            existing = await self.repository.get_by_email(schema.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            db_user.email = schema.email

        if schema.password is not None:
            db_user.hashed_password = self.hash_password(schema.password)

        if schema.is_active is not None:
            db_user.is_active = schema.is_active

        return await self.repository.update(db_user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        db_user = await self.get_user_by_id(user_id)
        await self.repository.delete(db_user)
