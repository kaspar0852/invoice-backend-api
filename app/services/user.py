import uuid
from typing import List
from app.models.user import User
from fastapi import HTTPException, status
import bcrypt
from app.repositories import UserRepositoryInterface
from app.schemas import UserRead, UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepositoryInterface):
        self.repository = repository

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(
            password.encode("utf-8"),
            salt
        ).decode("utf-8")

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8")
        )

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserRead:
        user = await self.repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserRead.model_validate(user)

    async def get_user_by_email(self, email: str) -> User:
        user = await self.repository.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserRead]:
        users = await self.repository.list_users(skip=skip, limit=limit)

        return [
            UserRead.model_validate(user)
            for user in users
        ]

    async def create_user(self, schema: UserCreate) -> UserRead:
        existing = await self.repository.get_by_email(schema.email)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        db_user = User(
            email=schema.email,
            full_name=schema.full_name,
            phone=schema.phone,
            is_active=schema.is_active,
            password_hash=self.hash_password(schema.password)
        )

        created_user = await self.repository.create(db_user)

        return UserRead.model_validate(created_user)

    async def update_user(
        self,
        user_id: uuid.UUID,
        schema: UserUpdate
    ) -> UserRead:

        db_user = await self.repository.get_by_id(user_id)

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = schema.model_dump(exclude_unset=True)

        # email uniqueness check
        if "email" in update_data:
            existing = await self.repository.get_by_email(update_data["email"])

            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # apply updates
        if "password" in update_data:
            update_data["password_hash"] = self.hash_password(update_data.pop("password"))

        if "email" in update_data:
            db_user.email = update_data["email"]

        if "full_name" in update_data:
            db_user.full_name = update_data["full_name"]

        if "phone" in update_data:
            db_user.phone = update_data["phone"]

        if "is_active" in update_data:
            db_user.is_active = update_data["is_active"]

        if "password_hash" in update_data:
            db_user.password_hash = update_data["password_hash"]

        updated_user = await self.repository.update(db_user)

        return UserRead.model_validate(updated_user)


    async def delete_user(self, user_id: uuid.UUID) -> None:
        db_user = await self.repository.get_by_id(user_id)

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await self.repository.delete(db_user)