from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.integrations.tmdb.client import (
    get_media_details,
)
from app.models.library import LibraryItem, LibraryStatus
from app.models.media import Media
from app.schemas.library import (
    LibraryItemCreate,
    LibraryItemRead,
    LibraryItemUpdate,
)
from app.services.catalog import (
    upsert_media_from_tmdb,
)


router = APIRouter()


async def fetch_tmdb_item(
    payload: LibraryItemCreate,
) -> dict[str, Any]:
    try:
        return await get_media_details(
            payload.media_type.value,
            payload.tmdb_id,
        )
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="TMDB tardó demasiado en responder.",
        ) from error
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contenido no encontrado.",
            ) from error

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TMDB respondió con un error.",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No fue posible conectar con TMDB.",
        ) from error

@router.get(
    "",
    response_model=list[LibraryItemRead],
)
def list_library_items(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[LibraryItem]:
    items = session.scalars(
        select(LibraryItem)
        .where(
            LibraryItem.user_id == current_user.id,
        )
        .options(
            selectinload(LibraryItem.media),
        )
        .order_by(
            LibraryItem.updated_at.desc(),
        )
    ).all()

    return list(items)

@router.post(
    "",
    response_model=LibraryItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_library_item(
    payload: LibraryItemCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> LibraryItem:
    existing_item = session.scalar(
        select(LibraryItem)
        .join(Media)
        .where(
            LibraryItem.user_id == current_user.id,
            Media.tmdb_id == payload.tmdb_id,
            Media.media_type == payload.media_type,
        )
    )

    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El contenido ya está en tu biblioteca.",
        )

    tmdb_item = await fetch_tmdb_item(payload)

    media = upsert_media_from_tmdb(
        session,
        tmdb_item,
        payload.media_type,
    )

    library_item = LibraryItem(
        user_id=current_user.id,
        media=media,
        status=payload.status,
    )

    session.add(library_item)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El contenido ya está en tu biblioteca.",
        ) from error

    session.refresh(library_item)

    return library_item

@router.patch(
    "/{item_id}",
    response_model=LibraryItemRead,
)
def update_library_item(
    item_id: UUID,
    payload: LibraryItemUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> LibraryItem:
    library_item = session.scalar(
        select(LibraryItem)
        .where(
            LibraryItem.id == item_id,
            LibraryItem.user_id == current_user.id,
        )
        .options(
            selectinload(LibraryItem.media),
        )
    )

    if library_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Elemento no encontrado "
                "en tu biblioteca."
            ),
        )

    if payload.status is not None:
        now = datetime.now(timezone.utc)

        library_item.status = payload.status

        if (
            payload.status
            in {
                LibraryStatus.WATCHING,
                LibraryStatus.COMPLETED,
            }
            and library_item.started_at is None
        ):
            library_item.started_at = now

        if payload.status == LibraryStatus.COMPLETED:
            library_item.completed_at = (
                library_item.completed_at or now
            )
        else:
            library_item.completed_at = None

    if "user_rating" in payload.model_fields_set:
        library_item.user_rating = payload.user_rating

    if payload.is_favorite is not None:
        library_item.is_favorite = (
            payload.is_favorite
        )

    if "notes" in payload.model_fields_set:
        library_item.notes = payload.notes

    session.commit()
    session.refresh(library_item)

    return library_item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_library_item(
    item_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    library_item = session.scalar(
        select(LibraryItem).where(
            LibraryItem.id == item_id,
            LibraryItem.user_id == current_user.id,
        )
    )

    if library_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Elemento no encontrado "
                "en tu biblioteca."
            ),
        )

    session.delete(library_item)
    session.commit()