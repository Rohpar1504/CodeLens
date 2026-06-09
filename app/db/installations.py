from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Installation, RepoSettings
from app.db.database import AsyncSessionLocal


async def save_installation(
    installation_id: int,
    account_login: str,
    account_type: str,
) -> None:
    """Save a new installation to the database."""
    async with AsyncSessionLocal() as session:
        # Check if already exists
        result = await session.execute(
            select(Installation).where(
                Installation.installation_id == installation_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = True
        else:
            session.add(Installation(
                installation_id=installation_id,
                account_login=account_login,
                account_type=account_type,
            ))

        await session.commit()
        print(f"[db] Saved installation {installation_id} for {account_login}")


async def deactivate_installation(installation_id: int) -> None:
    """Mark an installation as inactive when the app is uninstalled."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Installation).where(
                Installation.installation_id == installation_id
            )
        )
        installation = result.scalar_one_or_none()
        if installation:
            installation.is_active = False
            await session.commit()
            print(f"[db] Deactivated installation {installation_id}")


async def get_installation(installation_id: int) -> Installation | None:
    """Look up an installation by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Installation).where(
                Installation.installation_id == installation_id
            )
        )
        return result.scalar_one_or_none()


async def get_or_create_repo_settings(
    repo_full_name: str,
    installation_id: int,
) -> RepoSettings:
    """Get settings for a repo, creating defaults if none exist."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RepoSettings).where(
                RepoSettings.repo_full_name == repo_full_name
            )
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = RepoSettings(
                repo_full_name=repo_full_name,
                installation_id=installation_id,
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        return settings