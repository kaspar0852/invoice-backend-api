from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.token_blacklist import TokenBlacklist


class TokenBlacklistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, token: TokenBlacklist) -> None:
        """Add a token to the blacklist."""
        self.db.add(token)
        await self.db.commit()

    async def is_blacklisted(self, token: str) -> bool:
        """Check if a token exists in the blacklist."""
        result = await self.db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token == token)
        )
        return result.scalars().first() is not None
