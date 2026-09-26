from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.db.models import PacienteModel
from app.adapters.db.session import get_db
from app.entrypoints.api.schemas import PacienteCreate, PacienteResponse

router = APIRouter(prefix="/api/pacientes", tags=["Pacientes"])


@router.get("/buscar", response_model=PacienteResponse)
def buscar_paciente_por_ci_query(
    ci: str = Query(..., description="Número de C.I. del paciente"),
    db: Session = Depends(get_db),
):
    paciente = db.query(PacienteModel).filter(PacienteModel.ci == ci).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con C.I. '{ci}' no encontrado",
        )
    return paciente


@router.get("/buscar/{ci}", response_model=PacienteResponse)
def buscar_paciente_por_ci_path(
    ci: str,
    db: Session = Depends(get_db),
):
    paciente = db.query(PacienteModel).filter(PacienteModel.ci == ci).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con C.I. '{ci}' no encontrado",
        )
    return paciente


@router.post("/", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def crear_paciente(
    paciente_in: PacienteCreate,
    db: Session = Depends(get_db),
):
    existente = db.query(PacienteModel).filter(PacienteModel.ci == paciente_in.ci).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un paciente registrado con esta C.I.",
        )

    nuevo_paciente = PacienteModel(**paciente_in.model_dump())
    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)
    return nuevo_paciente
