from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_unsubscribe_token
from app.db.session import get_db
from app.models.lead import Lead, LeadStatus
from app.models.suppression import Suppression

router = APIRouter(tags=["unsubscribe"])

_INVALID_HTML = "<html><body><h1>Link non valido o scaduto</h1></body></html>"
_SUCCESS_HTML = (
    "<html><body><h1>Disiscrizione confermata</h1>"
    "<p>{email} non ricevera' piu' comunicazioni da parte nostra.</p></body></html>"
)


@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
def unsubscribe(token: str, db: Session = Depends(get_db)) -> HTMLResponse:
    lead_id = verify_unsubscribe_token(token)
    if lead_id is None:
        return HTMLResponse(_INVALID_HTML, status_code=400)

    lead = db.get(Lead, lead_id)
    if lead is None:
        return HTMLResponse(_INVALID_HTML, status_code=400)

    if lead.email and not db.scalar(select(Suppression.id).where(Suppression.email == lead.email)):
        db.add(Suppression(email=lead.email, reason="opt_out_link"))

    lead.status = LeadStatus.OPT_OUT
    db.commit()

    return HTMLResponse(_SUCCESS_HTML.format(email=lead.email or "Il contatto"))
