"""Guest claim tracking with code and claimant email."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr

from app.api.dependencies import DbSession
from app.schemas.lost_found_item import GuestClaimAdditionalInfo, GuestClaimStatusResponse
from app.services.lost_found_claim import (
    ClaimNotFoundError,
    DuplicateClaimError,
    ItemNotClaimableError,
    submit_claim_additional_info,
    track_guest_claim,
)

router = APIRouter()


@router.get("/{claim_code}", response_model=GuestClaimStatusResponse)
async def track_claim(
    claim_code: str, session: DbSession, claimant_email: Annotated[EmailStr, Query()]
):
    try:
        return await track_guest_claim(
            session, claim_code=claim_code, claimant_email=str(claimant_email)
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(404, detail="ไม่พบคำขอนี้") from exc


@router.post("/{claim_code}/additional-info", response_model=GuestClaimStatusResponse)
async def additional_info(claim_code: str, payload: GuestClaimAdditionalInfo, session: DbSession):
    try:
        return await submit_claim_additional_info(session, claim_code=claim_code, payload=payload)
    except ClaimNotFoundError as exc:
        raise HTTPException(404, detail="ไม่พบคำขอนี้") from exc
    except (ItemNotClaimableError, DuplicateClaimError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc
