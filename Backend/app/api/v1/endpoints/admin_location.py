"""Admin API สำหรับ location และ QR ประจำห้อง."""

from collections.abc import Awaitable
from io import BytesIO
from typing import Annotated, Literal, TypeVar
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import AdminStaff, DbSession
from app.schemas.admin_location import (
    AdminLocationCreate,
    AdminLocationResponse,
    AdminLocationStatusUpdate,
    AdminLocationUpdate,
)
from app.services.admin_location import (
    DuplicateLocationError,
    LocationInactiveError,
    LocationNotFoundError,
    QrNotGeneratedError,
    QrTokenCollisionError,
    build_qr_url,
    create_location,
    generate_qr,
    get_location_for_qr,
    get_location_or_raise,
    list_locations,
    regenerate_qr,
    set_location_active,
    to_admin_response,
    update_location,
)
from app.services.qr_image import render_qr

router = APIRouter()
_T = TypeVar("_T")


async def _call(operation: Awaitable[_T]) -> _T:
    try:
        return await operation
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        DuplicateLocationError,
        LocationInactiveError,
        QrNotGeneratedError,
        QrTokenCollisionError,
    ) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[AdminLocationResponse])
async def read_locations(
    session: DbSession, _admin: AdminStaff, include_inactive: bool = False
) -> list[AdminLocationResponse]:
    return await list_locations(session, include_inactive=include_inactive)


@router.post("", response_model=AdminLocationResponse, status_code=status.HTTP_201_CREATED)
async def add_location(
    payload: AdminLocationCreate, session: DbSession, _admin: AdminStaff
) -> AdminLocationResponse:
    return await _call(create_location(session, payload))


@router.get("/qr-bundle")
async def download_qr_bundle(
    session: DbSession,
    _admin: AdminStaff,
    ids: Annotated[list[int], Query(min_length=1, max_length=100)],
) -> Response:
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as bundle:
        for location_id in dict.fromkeys(ids):
            location = await _call(get_location_for_qr(session, location_id=location_id))
            data, _ = render_qr(build_qr_url(location.qr_token), "png")
            bundle.writestr(f"location-{location_id}-qr.png", data)
    return Response(
        content=output.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="location-qr-bundle.zip"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/{location_id}", response_model=AdminLocationResponse)
async def read_location(
    location_id: int, session: DbSession, _admin: AdminStaff
) -> AdminLocationResponse:
    location = await _call(get_location_or_raise(session, location_id))
    return to_admin_response(location)


@router.patch("/{location_id}", response_model=AdminLocationResponse)
async def edit_location(
    location_id: int, payload: AdminLocationUpdate, session: DbSession, _admin: AdminStaff
) -> AdminLocationResponse:
    return await _call(update_location(session, location_id=location_id, payload=payload))


@router.patch("/{location_id}/status", response_model=AdminLocationResponse)
async def change_location_status(
    location_id: int,
    payload: AdminLocationStatusUpdate,
    session: DbSession,
    _admin: AdminStaff,
) -> AdminLocationResponse:
    return await _call(
        set_location_active(session, location_id=location_id, is_active=payload.is_active)
    )


@router.post("/{location_id}/qr/generate", response_model=AdminLocationResponse)
async def generate_location_qr(
    location_id: int, session: DbSession, _admin: AdminStaff
) -> AdminLocationResponse:
    return await _call(generate_qr(session, location_id=location_id))


@router.post("/{location_id}/qr/regenerate", response_model=AdminLocationResponse)
async def regenerate_location_qr(
    location_id: int, session: DbSession, _admin: AdminStaff
) -> AdminLocationResponse:
    return await _call(regenerate_qr(session, location_id=location_id))


@router.get("/{location_id}/qr")
async def download_location_qr(
    location_id: int,
    session: DbSession,
    _admin: AdminStaff,
    format: Literal["png", "svg"] = "png",
    download: bool = True,
) -> Response:
    location = await _call(get_location_for_qr(session, location_id=location_id))
    content, media_type = render_qr(build_qr_url(location.qr_token), format)
    disposition = "attachment" if download else "inline"
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="location-{location_id}-qr.{format}"',
            "Cache-Control": "no-store",
        },
    )
