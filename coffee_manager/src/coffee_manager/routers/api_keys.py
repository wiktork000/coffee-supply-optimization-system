from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from coffee_manager.auth import generate_api_key, get_current_user
from coffee_manager.database import get_db
from coffee_manager.models import ApiKey, Distributor, User
from coffee_manager.schemas import ApiKeyCreateRequest, ApiKeyResponse

router = APIRouter(tags=["API Keys"])


@router.get(
    "/distributors/{distributor_id}/api-keys", response_model=list[ApiKeyResponse]
)
def list_api_keys(
    distributor_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if not db.get(Distributor, distributor_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found"
        )
    keys = db.query(ApiKey).filter(ApiKey.distributor_id == distributor_id).all()
    return [
        ApiKeyResponse(
            id=k.id,
            label=k.label,
            distributor_id=k.distributor_id,
            active=k.active,
            revoked_at=k.revoked_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post(
    "/distributors/{distributor_id}/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    distributor_id: UUID,
    body: ApiKeyCreateRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if not db.get(Distributor, distributor_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found"
        )
    raw_key, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        distributor_id=distributor_id,
        key_prefix=prefix,
        key_hash=key_hash,
        label=body.label,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return ApiKeyResponse(
        id=api_key.id,
        key=raw_key,
        label=api_key.label,
        distributor_id=api_key.distributor_id,
        active=api_key.active,
        revoked_at=api_key.revoked_at,
        created_at=api_key.created_at,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    key = db.get(ApiKey, key_id)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
    key.active = False
    key.revoked_at = datetime.now(timezone.utc)
    db.commit()
