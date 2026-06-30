from typing import Annotated
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.routers.dashboard.dashboard_schema import DashboardOut
from app.routers.dashboard.dashboard_service import get_dashboard_stats

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    range_: str = Query("week", alias="range", regex="^(week|month|year)$"),
    accept_language: Annotated[str | None, Header()] = None,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    lang = (accept_language or "en")[:2]
    return get_dashboard_stats(db, range_=range_, lang=lang)