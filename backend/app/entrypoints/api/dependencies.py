from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.pdf.renderer import OfficialPdfRenderer
from app.adapters.persistence.session import get_db
from app.adapters.persistence.uow import SqlAlchemyUnitOfWork
from app.application.ports import Clock, PdfPort, UnitOfWork
from app.domain.services.calculation_engine import CalculationEngine


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def get_unit_of_work(db: Annotated[Session, Depends(get_db)]) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(db)


def get_calculation_port() -> CalculationEngine:
    return CalculationEngine()


def get_clock() -> Clock:
    return SystemClock()


def get_pdf_port() -> PdfPort:
    return OfficialPdfRenderer()