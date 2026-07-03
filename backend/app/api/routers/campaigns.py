from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignRead])
def list_campaigns(db: Session = Depends(get_db)) -> list[Campaign]:
    return list(db.scalars(select(Campaign).order_by(Campaign.id)))


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> Campaign:
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignRead)
def update_campaign(campaign_id: int, payload: CampaignUpdate, db: Session = Depends(get_db)) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field_name, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)) -> None:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    has_leads = db.scalar(select(Lead.id).where(Lead.campaign_id == campaign_id))
    if has_leads:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Campaign has leads; set is_active=false instead of deleting.",
        )
    db.delete(campaign)
    db.commit()
